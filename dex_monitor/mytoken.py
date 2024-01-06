
from web3 import Web3

from dex_monitor.contract import MyContract

class Token(MyContract):
    def __init__(self, web3: Web3, address: str):
        super().__init__(web3, address)
        self.decimals=self.contract.functions.decimals().call()
        self.symbol=self.contract.functions.symbol().call()

    def __str__(self):
        string=f"{self.symbol} @ {self.address}"
        return string

    def __repr__(self) -> str:
        return str(self)