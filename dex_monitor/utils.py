import os
import requests

def sqrtPriceX96_to_price(sqrtPriceX96: int, token0_decimals:int, token1_decimals: int):
    price = (sqrtPriceX96/2**96)**2*10**(token0_decimals-token1_decimals)
    return price

def tick_to_price(tick: float, token0_decimals:int, token1_decimals: int, base: float=1.0001):
    price = base ** tick **2*10**(token0_decimals-token1_decimals)
    return price

def getContractAbi(address: str):
    # Etherscan API URL
    api_url = f'https://api.etherscan.io/api'

    # Parameters for the API request
    params = {
        'module': 'contract',
        'action': 'getabi',
        'address': address,
        'apikey': os.getenv('ETHERSCAN_API_KEY'),
    }

    try:
        # Make the API request
        response = requests.get(api_url, params=params)
        response_json = response.json()

        # Check if the API request was successful
        if response_json['status'] == '1':
            return response_json['result']
        else:
            error_message = response_json.get('result', 'Unknown error')
            print(f"Failed to retrieve ABI. Error message: {error_message}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def getContractSourcecode(address: str):
    # Etherscan API URL
    api_url = f'https://api.etherscan.io/api'

    # Parameters for the API request
    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': address,
        'apikey': os.getenv('ETHERSCAN_API_KEY'),
    }

    try:
        # Make the API request
        response = requests.get(api_url, params=params)
        response_json = response.json()

        # Check if the API request was successful
        if response_json['status'] == '1':
            return response_json['result']
        else:
            error_message = response_json.get('result', 'Unknown error')
            print(f"Failed to retrieve ABI. Error message: {error_message}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    