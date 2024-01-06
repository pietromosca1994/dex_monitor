#%%
from web3 import Web3
import pprint
from typing import Dict

from dex_monitor.utils import sqrtPriceX96_to_price

class Event():
    def __init__(self, web3: Web3, event):
        self.web3=web3
        self.blocknumber=event['blockNumber']
        self.unix_timestamp=self.web3.eth.get_block(self.blocknumber).timestamp

        for key, value in event['args'].items():
            setattr(self, key, value)
    
    def post(self):
        raise NotImplementedError

    def __str__(self)->str:
        string=f"Event \n{pprint.pformat(self.__dict__, sort_dicts=False)}"
        return string

    def __repr__(self) -> str:
        return str(self)
    
class UniswapSwapEvent(Event):
    def __init__(self,
                 web3: Web3, 
                 event: Dict):
        self.sender=None
        self.recipient=None
        self.amount0=None
        self.amount1=None
        self.sqrtPriceX96=None
        self.liquidity=None
        self.tick=None

        super().__init__(web3, event)

    def post(self, token0_decimals: int, token1_decimals):
        '''
        Swap Event Format
        https://docs.uniswap.org/contracts/v3/reference/core/interfaces/pool/IUniswapV3PoolEvents
        Uniswap V3 Math
        https://blog.uniswap.org/uniswap-v3-math-primer
        '''

        self.amount0_float=self.amount0/10**token0_decimals
        self.amount1_float=self.amount1/10**token1_decimals
        self.price=sqrtPriceX96_to_price(self.sqrtPriceX96, token0_decimals, token1_decimals)