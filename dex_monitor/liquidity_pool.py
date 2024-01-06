from web3 import Web3
from typing import Union
from utils import getContractAbi
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker

from dex_monitor.mytoken import Token 
from dex_monitor.contract import MyContract
from dex_monitor.event import UniswapSwapEvent
from dex_monitor.tables import PoolEvent, PoolStatus

class LiquidityPool(MyContract):
    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address)
        self.dex=None
        token0_address=self.contract.functions.token0().call()
        token1_address=self.contract.functions.token1().call()
        self.token0=Token(web3=self.web3, address=token0_address)
        self.token1=Token(web3=self.web3, address=token1_address)

    def logSwapEvent(self, engine: Engine, event: UniswapSwapEvent): 
        # log in database 
        # create session
        Session = sessionmaker(bind=engine)
        session = Session()

        # postprocess event
        event.post(self.token0.decimals, self.token1.decimals)

        # add row to table 
        session.add(
            PoolEvent(dex=self.dex,
                      pool_address=self.address,
                      token0_address=self.token0.address,
                      token1_address=self.token1.address,
                      token0_symbol=self.token0.symbol,
                      token1_symbol=self.token1.symbol,
                      unix_timestamp=event.unix_timestamp, 
                      blocknumber=event.blocknumber,
                      sender=event.sender,
                      recipient=event.recipient,
                      amount0_float=event.amount0_float,
                      amount1_float=event.amount1_float,
                      price=event.price
            )
        )
        
        # commit
        session.commit()
    
        # close session
        session.close()

    def logStatus(self, engine: Engine, event: UniswapSwapEvent):
        # log in database 
        # create session
        Session = sessionmaker(bind=engine)
        session = Session()

        # postprocess event
        event.post(self.token0.decimals, self.token1.decimals)


        row_to_update = session.query(PoolStatus).filter_by(pool_address=self.address).first()

        if row_to_update:
            # update row
            row_to_update.price=event.price
        else:
            # add row to table 
            session.add(
                PoolStatus(dex=self.dex,
                           pool_address=self.address,
                           token0_address=self.token0.address,
                           token1_address=self.token1.address,
                           token0_symbol=self.token0.symbol,
                           token1_symbol=self.token1.symbol,
                           unix_timestamp=event.unix_timestamp,
                           blocknumber=event.blocknumber,
                           price=event.price
                )
            )
        
        # commit
        session.commit()
    
        # close session
        session.close()

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
        self.dex='UniswapV3'

    def getSwapEvent(self, from_block: Union[int, str]='latest', to_block: Union[int, str]='latest', callback=None):
        self.getEvent(event='Swap', from_block=from_block, to_block=to_block, callback=callback)

    def listenSwapEvent(self, event_handler=None, from_block: Union[int, str]='latest', update_period: int=60):
        self.listenEvent(event='Swap', 
                         event_handler=event_handler, 
                         from_block=from_block, 
                         update_period=update_period)
    
