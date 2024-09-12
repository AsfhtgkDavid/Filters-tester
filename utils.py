from enum import Enum
import dataclasses
from datetime import datetime, timedelta
from typing import Literal


class TradeStatus(str, Enum):
    NEW = 'NEW'
    OPENED = 'OPENED'
    CLOSED = 'CLOSED'


class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(str, Enum):
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'


class ClosedBy(str, Enum):
    TP = "TP"
    SL = "SL"
    URGENTLY = "URGENTLY"


class TimeFrame:
    __graduation__ = {"m": 1, "h": 60, "d": 1440}

    _format = {
        'm': 'minute',
        'h': 'hour',
        'd': 'day'
    }

    def __init__(self, value: int, unit: Literal['m', 'h', 'd']):

        if value < 0:
            value = -value
        elif value == 0:
            value = 1

        self.value = value
        self.unit = unit

        self.minutes = self.__graduation__.get(unit) * value

    def __str__(self):
        return f'{self.value}{self.unit}'

    __repr__ = __str__

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.minutes > other.minutes:
            return True
        return False

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.minutes < other.minutes:
            return True
        return False

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.minutes >= other.minutes:
            return True
        return False

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.minutes <= other.minutes:
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.minutes == other.minutes:
            return True
        return False

    def get(self, exchange: str):
        match exchange:
            case 'PolygonAPI':
                return self.value, self._format[self.unit]
            case 'BinanceAPI':
                return self.value, self.unit


@dataclasses.dataclass
class Trade:
    side: Side
    symbol: str
    timeframe: TimeFrame
    volume: float

    entry_price: float
    tp_price: float
    sl_price: float

    entry_order_type: OrderType = OrderType.MARKET
    tp_order_type: OrderType = OrderType.MARKET
    sl_order_type: OrderType = OrderType.MARKET

    status: TradeStatus = TradeStatus.NEW

    fees_paid: float = 0
    profit_or_loss: float = 0

    opened_at: datetime = datetime.now()
    closed_at: datetime | None = None
    closed_by: ClosedBy | None = None

    id: int | None = None

    def close(self, by: ClosedBy, at: datetime = None):
        self.closed_at = at or (self.opened_at+timedelta(days=1)).replace(hour=0, minute=0, second=0)
        self.status = TradeStatus.CLOSED
        self.closed_by = by

    @property
    def is_closed(self):
        return isinstance(self.closed_at, datetime)

    @property
    def is_market(self):
        return self.entry_order_type == OrderType.MARKET

    @property
    def is_long(self):
        return self.side == Side.LONG

    @property
    def as_dict(self) -> dict:
        cols = [
            'side', 'symbol', 'timeframe', 'volume', 'entry_price',
            'tp_price', 'sl_price', 'entry_order_type', 'tp_order_type',
            'sl_order_type', 'status', 'fees_paid', 'profit_or_loss',
            'opened_at', 'closed_at', 'closed_by'
        ]

        return {k: self.__dict__.get(k) for k in cols}


def get_batch(iterable, batch_size: int, agg_func):
    result = []

    last_index = 0
    for index in range(batch_size, len(iterable) + batch_size, batch_size):
        result.append(iterable[last_index:index])
        last_index = index

    if agg_func is not None:
        result = list(map(agg_func, result))

    return result
