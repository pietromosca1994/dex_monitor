from web3 import Web3
from web3.eth import Contract
import logging
from time import sleep 
from typing import Union, List

from dex_monitor.event import UniswapSwapEvent
from dex_monitor.utils import getContractAbi

class MyContract:
    def __init__(self, web3: Web3, address: str, verbose=logging.INFO):
        self.web3=web3
        self.address=Web3.to_checksum_address(address)
        self.contract=self.web3.eth.contract(address=self.address, abi=getContractAbi(self.address))

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

    def getEvent(self, event: Union[List[str], str], from_block: Union[int, str]='latest', to_block: Union[int, str]='latest', callback=None):
        events = self.contract.events[event].get_logs(fromBlock=from_block, toBlock=to_block)
        for event in events:
            if event['event']=='Swap':
                event=UniswapSwapEvent(self.web3, event)
                if callback:
                    callback(event, self)

    def listenEvent(self, event: Union[List[str], str], event_handler=None, from_block: Union[int, str]='latest', update_period: int=60):
        self.logger.info(f'Listening for event {event} @ {self.contract.address}')

        # subscribe to events
        while True:
            self.getEvent(event, event_handler, from_block)
            sleep(update_period)
    

