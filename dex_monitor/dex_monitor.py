#%%
from uniswap import Uniswap
from web3 import Web3, exceptions
from web3.eth import Contract
import dotenv
import os 
from enum import Enum
import logging
from prometheus_client import start_http_server
from time import sleep 
import json
import pandas as pd
from typing import Union, List
from utils import sqrtPriceX96_to_price, getContractAbi, getContractSourcecode
import pprint
import threading 

from prometheus import update_pair

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

class Trader():
    def __init__(self,
                 address: str=None,
                 private_key: str=None,
                 web3: Web3=None,
                 verbose: int=logging.INFO):
        
        self.web3=web3

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

    def listenEvent(self, contract: Contract, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest', update_period: int=60):
        self.logger.info(f'Listening for event {event} @ {contract.address}')

        # subscribe to events
        while True:
            self.getEvent(contract, event, event_handler, from_block)
            sleep(update_period)
    
    @staticmethod
    def getEvent(contract: Contract, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest'):
        events = contract.events[event].get_logs(fromBlock=from_block)
        for event in events:
            if event_handler:
                event_handler(event)
    
class UniSwapTrader(Uniswap, Trader):
    def __init__(self,
                 address: str=None,
                 private_key: str=None,
                 web3: Web3=None,
                 version: int=1,
                 verbose=logging.INFO):
        
        Trader.__init__(self, web3=web3, verbose=verbose)

        if web3.is_connected():
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
    
    # def get_event

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
    
    def monitorPool(self, addresses: List[str]):
        def event_handler(pool: LiquidityPool, event):
            post_event=pool.postSwapEvent(event)
            self.logger.info(f'Swap @ {pool.address}\n{pprint.pformat(dict(post_event), sort_dicts=False)}')

        pools=[]
        for address in addresses:
            pools.append(UniswapLiquidityPool(web3=self.web3, address=address))
            self.logger.info(pools[-1])

        for pool in pools:
            threading.Thread(target=pool.listenSwapEvent(event_handler=event_handler,
                                                         from_block=self.web3.eth.block_number-5, 
                                                         update_period=60)).start()

class MyContract:
    def __init__(self, contract: Contract, verbose=logging.INFO):
        self.contract=contract

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

    def listenEvent(self, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest', update_period: int=60):
        self.logger.info(f'Listening for event {event} @ {self.contract.address}')

        # subscribe to events
        while True:
            self.getEvent(event, event_handler, from_block)
            sleep(update_period)
    
    def getEvent(self, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest'):
        events = self.contract.events[event].get_logs(fromBlock=from_block)
        for event in events:
            if event_handler:
                event_handler(self, event)

class Token(MyContract):
    def __init__(self, web3: Web3, address: str):
        self.web3=web3
        self.address=Web3.to_checksum_address(address)
        contract=self.web3.eth.contract(address=self.address, abi=getContractAbi(address))
        super().__init__(contract)
        self.decimals=self.contract.functions.decimals().call()
        self.symbol=self.contract.functions.symbol().call()

    def __str__(self):
        string=f"{self.symbol} @ {self.address}"
        return string

    def __repr__(self) -> str:
        return str(self)
        
class LiquidityPool(MyContract):
    def __init__(self, web3: Web3, address: str):
        self.address=Web3.to_checksum_address(address)
        self.web3=web3
        contract=self.web3.eth.contract(address=self.address, abi=str(getContractAbi(address)))
        super().__init__(contract)
        token0_address=self.contract.functions.token0().call()
        token1_address=self.contract.functions.token1().call()
        self.token0=Token(web3=self.web3, address=token0_address)
        self.token1=Token(web3=self.web3, address=token1_address)

    def __str__(self)->str:
        string=f"Liquidity Pool @ {self.address}\n \
                token0: {self.token0}\n \
                token1: {self.token1}\n"
        return string

    def __repr__(self) -> str:
        return str(self)

class UniswapLiquidityPool(LiquidityPool):
    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address)

    def listenSwapEvent(self, event_handler=None, from_block: Union[int, str]='latest', update_period: int=60):
        self.listenEvent(event='Swap', 
                         event_handler=event_handler, 
                         from_block=from_block, 
                         update_period=update_period)

    def postSwapEvent(self, event):
        '''
        Swap Event Format
        https://docs.uniswap.org/contracts/v3/reference/core/interfaces/pool/IUniswapV3PoolEvents
        Uniswap V3 Math
        https://blog.uniswap.org/uniswap-v3-math-primer
        '''
        post_event={
            'blockNumber': event['blockNumber'],
            'event': event['event'],
            'sender': event['args']['sender'],
            'recipient': event['args']['recipient'],
            'amount0': event['args']['amount0']/10**self.token0.decimals,
            'amount1': event['args']['amount1']/10**self.token1.decimals,
            'sqrtPriceX96': event['args']['sqrtPriceX96'],
            'price': sqrtPriceX96_to_price(event['args']['sqrtPriceX96'], self.token0.decimals, self.token1.decimals),
            'tick': event['args']['tick'],
            'deltaLiquidity': event['args']['liquidity']
        }
        return post_event
#%%
# load environment variables 
dotenv.load_dotenv(verbose=True, override=True)

# start 
# start_http_server(8000)

# web3 
infura_url=os.path.join(InfuraNetworks.ETHEREUM_MAINNET.value, 'v3', os.getenv("INFURA_API_KEY"))
web3 = Web3(Web3.HTTPProvider(infura_url))  

#%%
# initialize uniswap trader
uniswap_trader=UniSwapTrader(web3=web3, version=2, verbose=logging.INFO)

# pools=uniswap_trader.getPoolAddresses(n_pairs=1000)

# while True: 
#     print(uniswap_trader.get_price(EthereumMainnetAddresses.ETH.value, EthereumMainnetAddresses.USDC.value))
#     sleep(1)

uniswap_trader.monitorPool(addresses=[WETH_USDT_pool])

#%% 
# test liquidity pool
pool=LiquidityPool(web3=web3, address=WETH_USDT_pool)


# %%
code=getContractSourcecode(WETH_USDT_pool)
# %%
