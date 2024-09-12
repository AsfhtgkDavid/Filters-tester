from typing import Type

from .binance import BinanceAPI
from .polygon import PolygonAPI


Exchanges = Type[BinanceAPI | PolygonAPI]
