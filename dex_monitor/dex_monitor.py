from uniswap import Uniswap
from web3 import Web3, exceptions  
import dotenv
import os 
from enum import Enum
import logging
from prometheus_client import start_http_server
from time import sleep 

from prometheus import update_pair
class TokensMainnet(Enum):
    ETH     ="0x0000000000000000000000000000000000000000"
    WETH    ="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    DAI     ="0x6B175474E89094C44Da98b954EedeAC495271d0F"
    BAT     ="0x0D8775F648430679A709E98d2b0Cb6250d2887EF"
    WBTC    ="0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    UNI     ="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    USDC    ="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

class TokensRinkeby(Enum):
    ETH     ="0x0000000000000000000000000000000000000000"
    DAI     ="0x2448eE2641d78CC42D7AD76498917359D961A783"
    BAT     ="0xDA5B056Cfb861282B4b59d29c9B395bcC238D29B"

class Networks(Enum):
    ETHEREUM_SEPOLIA='https://sepolia.infura.io'
    ETHEREUM_MAINNET='https://mainnet.infura.io'

class Trader():
    def __init__(self,
                 address: str=None,
                 private_key: str=None,
                 web3: Web3=None,
                 verbose: int=logging.INFO):
        
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

    # def get_raw_price(self):
    #     get_raw_price

class UniSwapTrader(Uniswap, Trader):
    def __init__(self,
                 address: str=None,
                 private_key: str=None,
                 web3: Web3=None,
                 version: int=1):
        Trader.__init__(self)
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
        
if __name__=='__main__':
    # load environment variables 
    dotenv.load_dotenv(verbose=True, override=True)
    
    # start 
    start_http_server(8000)

    # web3 
    infura_url=os.path.join(Networks.ETHEREUM_MAINNET.value, 'v3', os.getenv("INFURA_API_KEY"))
    web3 = Web3(Web3.HTTPProvider(infura_url))  

    # initilize uniswap trader
    uniswap=UniSwapTrader(web3=web3, version=2)

    while True: 
        print(uniswap.get_price(TokensMainnet.ETH.value, TokensMainnet.USDC.value))
        sleep(1)
    