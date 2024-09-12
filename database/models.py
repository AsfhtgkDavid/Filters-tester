from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    Integer,
    LargeBinary,
    Float,
    DateTime,
    Enum as SAEnum,
    Numeric,
    PickleType
)

from utils import (
    Side,
    OrderType,
    TradeStatus,
    ClosedBy
)

Base = declarative_base()


class ModelDB(Base):
    """
    A class to represent a neural network model record in the database.

    Attributes:
        Same as model
    """

    __tablename__ = 'models'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    model_type = Column(String, nullable=False)
    architecture = Column(String, nullable=False)
    weights = Column(LargeBinary, nullable=False)
    depth = Column(Integer, nullable=False)
    window = Column(Integer, nullable=False)
    diff_on = Column(PickleType)


class TradeDB(Base):
    """
    A class to represent a trade record in the database.

    Attributes:
        Same as trade
    """
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True, autoincrement=True)

    side = Column(SAEnum(Side), nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    volume = Column(Float, nullable=True)

    entry_price = Column(Numeric, nullable=True)
    tp_price = Column(Numeric, nullable=False)
    sl_price = Column(Numeric, nullable=False)

    entry_order_type = Column(SAEnum(OrderType), default=OrderType.MARKET)
    tp_order_type = Column(SAEnum(OrderType), default=OrderType.MARKET)
    sl_order_type = Column(SAEnum(OrderType), default=OrderType.MARKET)

    status = Column(SAEnum(TradeStatus), default=TradeStatus.NEW)

    fees_paid = Column(Float, nullable=False)
    profit_or_loss = Column(Float, nullable=True)

    opened_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(SAEnum(ClosedBy), nullable=True)
