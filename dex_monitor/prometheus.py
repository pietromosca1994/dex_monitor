from prometheus_client import start_http_server, Counter, Gauge, Summary, Histogram
from typing import Tuple

pair=Gauge('pair', 'pair')


def update_pair(func):
    def wrapper(*args, **kwargs):
        value=func(*args, **kwargs)
        pair.set(value)
        return value
    return wrapper

        


    
