from sqlalchemy import Column, Integer, String, MetaData, Float, BigInteger, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr

# numeric types 
# https://www.postgresql.org/docs/current/datatype-numeric.html

Base=declarative_base()
metadata=MetaData()

class PoolEvent(Base):
    __tablename__='pool_event'
    
    id = Column(BigInteger, primary_key=True)
    dex=Column(String, nullable=False)
    pool_address=Column(String, nullable=False)
    token0_address=Column(String, nullable=False)
    token1_address=Column(String, nullable=False)
    token0_symbol=Column(String, nullable=False)
    token1_symbol=Column(String, nullable=False)
    unix_timestamp=Column(BigInteger, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=func.now())
    blocknumber=Column(BigInteger, nullable=False)
    sender=Column(String)
    recipient=Column(String)
    # amount0=Column(BigInteger)
    # amount1=Column(BigInteger)
    # sqrtPriceX96=Column(BigInteger)
    # liquidity=Column(BigInteger)
    # tick=Column(BigInteger)
    amount0_float=Column(Float)
    amount1_float=Column(Float)
    price=Column(Float)

    



class PoolStatus(Base):
    __tablename__='pool_status'

    id = Column(BigInteger, primary_key=True)
    dex=Column(String, nullable=False)
    pool_address=Column(String, nullable=False)
    token0_address=Column(String, nullable=False)
    token1_address=Column(String, nullable=False)
    token0_symbol=Column(String, nullable=False)
    token1_symbol=Column(String, nullable=False)
    unix_timestamp=Column(BigInteger, nullable=False)
    timestamp=Column(DateTime(timezone=True), default=func.now())
    blocknumber=Column(BigInteger, nullable=False)
    price=Column(Float)

    # @declared_attr
    # def timestamp(cls):
    #     return Column(DateTime, server_default=func.to_timestamp(func.cast(cls.unix_timestamp, 'double precision')))