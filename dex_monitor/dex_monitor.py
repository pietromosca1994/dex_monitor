import sys
import os 
PROJECT_PATH=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_PATH)

from web3 import Web3
from uniswap import Uniswap
import dotenv
from enum import Enum
import logging
from prometheus_client import start_http_server
from time import sleep 
import json
import pandas as pd
from typing import Union, List, Dict
import threading 
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from copy import copy

from dex_monitor.prometheus import update_pair
from dex_monitor.tables import Base
from dex_monitor.liquidity_pool import UniswapLiquidityPool, LiquidityPool
from dex_monitor.event import Event

WBTC_ETH_pool='0xCBCdF9626bC03E24f779434178A73a0B4bad62eD'
WETH_USDC_pool='0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640'
WETH_USDT_pool='0x11b815efb8f581194ae79006d24e0d814b7697f6'

class EthereumMainnetAddresses(Enum):
    ETH                     ="0x0000000000000000000000000000000000000000"
    WETH                    ="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    DAI                     ="0x6B175474E89094C44Da98b954EedeAC495271d0F"
    BAT                     ="0x0D8775F648430679A709E98d2b0Cb6250d2887EF"
    WBTC                    ="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    UNI                     ="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    USDC                    ="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    UNISWAP_FACTORY_V2      ="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    UNISWAP_FACTORY_V3      =""

class EthereumRinkebyAddresses(Enum):
    ETH     ="0x0000000000000000000000000000000000000000"
    DAI     ="0x2448eE2641d78CC42D7AD76498917359D961A783"
    BAT     ="0xDA5B056Cfb861282B4b59d29c9B395bcC238D29B"

class InfuraNetworks(Enum):
    ETHEREUM_SEPOLIA='https://sepolia.infura.io'
    ETHEREUM_MAINNET='https://mainnet.infura.io'
    POLYGON_MAINNET='https://polygon-mainnet.infura.io'
    POLYGON_MUMBAI='https://polygon-mumbai.infura.io'

new_block_event=threading.Event()


class Trader():
    def __init__(self,
                 address: str=None,
                 private_key: str=None,
                 web3: Web3=None,
                 engine: Engine=None,
                 verbose: int=logging.INFO):
        self.web3=web3
        self.engine=engine

        self.latest_block=self.web3.eth.block_number
        self.pools: List[LiquidityPool]=[]

        if self.engine:
            Base.metadata.create_all(bind=self.engine)
        # configure logger
        logging.basicConfig(
            level=verbose,
            format="%(asctime)s [%(levelname)s] %(message)s",  # Define the log format
            handlers=[
                logging.StreamHandler(),  # Output logs to the console
                # logging.FileHandler("app.log"),  # Output logs to a file (optional)
            ]
        )
        self.logger=logging.getLogger(self.__class__.__name__)
        pass 

    def onNewBLock(self):
        raise NotImplementedError
    
    def updateLatestBlock(self, update_period: int):
        while True:
            # get latest block
            latest_block=self.web3.eth.block_number
            
            # check if there is a new block
            if latest_block!=self.latest_block:
                self.latest_block=latest_block
                self.onNewBLock()
            
            sleep(update_period)

    def monitor(self, update_period: int =1):
        threading.Thread(self.updateLatestBlock(update_period))        


    # def listenEvent(self, contract: Contract, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest', update_period: int=60):
    #     self.logger.info(f'Listening for event {event} @ {contract.address}')

    #     # subscribe to events
    #     while True:
    #         self.getEvent(contract, event, event_handler, from_block)
    #         sleep(update_period)
    
    # @staticmethod
    # def getEvent(contract: Contract, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest'):
    #     events = contract.events[event].get_logs(fromBlock=from_block)
    #     for event in events:
    #         if event_handler:
    #             event_handler(event)
    
class UniSwapTrader(Uniswap, Trader):
    def __init__(self,
                 address: str=None,
                 private_key: str=None,
                 web3: Web3=None,
                 engine: Engine=None,
                 version: int=1,
                 verbose=logging.INFO):
        
        Trader.__init__(self, web3=web3, engine=engine, verbose=verbose)

        if self.web3.is_connected():
            Uniswap.__init__(self, 
                             address=address,
                             private_key=private_key,
                             web3=web3,
                             version=version)
            self.logger.info(f"Connected to {web3.provider.endpoint_uri}")
        else:
            self.logger.error(f"Web3 is currently not connected")

    
    @update_pair
    def get_price(self, token_in, token_out):
        return self.get_raw_price(token_in, token_out)
    
    def setPools(self, addresses: List[str]):
        self.logger.info("Setting pools to monitor")
        for address in addresses:
            pool=UniswapLiquidityPool(web3=self.web3, address=address)
            self.pools.append(copy(pool))
            self.logger.info(pool)
            
    def getPoolAddresses(self, n_pairs: int = None):
        with open('./dex_monitor/abi/uniswap_factory_v2.json', 'r') as f:
            abi=json.load(f)
        
        # create uniswap 
        uniswap_factory_contract = self.web3.eth.contract(address=EthereumMainnetAddresses.UNISWAP_FACTORY_V2.value, 
                                                          abi=abi)
        
        if n_pairs:
            pair_count=n_pairs
        else:
            # Call the getPairCount function on the Uniswap Factory contract to get the number of pairs
            pair_count = uniswap_factory_contract.functions.allPairsLength().call()
            self.logger.info(f'Found {pair_count} pairs')
            
        self.logger.info(f'Getting info for {pair_count} pairs')

        # create pools data
        pools=[]
        for pair in range(pair_count):
            pool_address = uniswap_factory_contract.functions.allPairs(pair).call()
            self.logger.info(f'Getting info for pair @ {pool_address}')

            with open('./dex_monitor/abi/IUniswapV2Pair.json', 'r') as f:
                abi=json.load(f)
            pool_address_contract=self.web3.eth.contract(address=pool_address, abi=abi)
            token0_address=pool_address_contract.functions.token0().call()
            token1_address=pool_address_contract.functions.token1().call()

            info={
                'token0': token0_address,
                'token1': token1_address,
                'pool': pool_address
            }

            pools.append(info)
        
        pools=pd.DataFrame(pools)
        pools.to_csv('./dex_monitor/pools/uniswap_pools.csv')
        
        return pools
    
    def onNewBLock(self):
        for pool in self.pools:
            threading.Thread(pool.getEvent(event='Swap',
                                           from_block=self.latest_block,
                                           to_block=self.latest_block,
                                           callback=self.SwapEventCallback)) #TODO substitute with getSwapEvent

    def SwapEventCallback(self, event: Event, pool: LiquidityPool):
        # post_event=pool.postSwapEvent(event)
        self.logger.info(f'Swap event @ {pool.address}\n{event}')
        pool.logSwapEvent(self.engine, event)
        pool.logStatus(self.engine, event)

#%%
# load environment variables 
dotenv.load_dotenv('./.env', verbose=True, override=True)
dotenv.load_dotenv('./docker/.env', verbose=True, override=True)
# start 
# start_http_server(8000)

# web3 
infura_url=os.path.join(InfuraNetworks.ETHEREUM_MAINNET.value, 'v3', os.getenv("INFURA_API_KEY"))
web3 = Web3(Web3.HTTPProvider(infura_url))  

# initialize engine
database_url=f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/dex_db"
engine=create_engine(database_url, echo=False)  

#%%
# initialize uniswap trader
uniswap_trader=UniSwapTrader(web3=web3, engine=engine, version=2, verbose=logging.INFO)
uniswap_trader.setPools(addresses=[WETH_USDT_pool])
uniswap_trader.monitor(update_period=1)
