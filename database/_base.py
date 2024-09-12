from sqlalchemy import create_engine, inspect, Engine
from sqlalchemy.orm import sessionmaker, Session
from pandas import DataFrame, read_sql, concat
from typing import List, Callable

from .models import Base, TradeDB
from utils import Trade
from config import DatabaseSettings


class Database:
    engine: Engine = create_engine(DatabaseSettings.CONNECTION_STRING)
    sm: Callable[[], Session] = sessionmaker(bind=engine, expire_on_commit=False)

    @staticmethod
    def klines_tablename(symbol: str, interval: int, unit: str):
        """
        Generates the table name for storing klines data in the database based on the symbol, interval, and unit

        :param symbol: trading symbol (e.g., 'BTCUSD') for which the klines data is stored
        :param interval: time interval representing the frequency of the klines data
        :param unit: time unit (e.g., 'm' for minutes, 'h' for hours)
        :return: string representing the table name
        """
        return DatabaseSettings.Tables.KLINES + f'-{symbol.upper()}-{interval}{unit}'

    @classmethod
    def add_klines(
            cls,
            table: DataFrame,
            symbol: str,
            interval: int,
            unit: str,
    ):

        tablename = cls.klines_tablename(symbol, interval, unit)

        if cls.is_table_exists(tablename):
            df = read_sql(tablename, cls.engine)
            table = concat([table, df], ignore_index=True)
            table.drop_duplicates(inplace=True)
            table.sort_values('time', inplace=True)
            table.reset_index(drop=True, inplace=True)

        try:
            table.to_sql(
                name=tablename,
                con=cls.engine,
                if_exists='replace',
                index=False
            )

        except Exception as ex_:
            raise print(
                "Unable to serialize klines.\n\n"
                "This exception provided by:\n\n"
                f"{ex_.__traceback__.__str__()}"
            )

    @classmethod
    def get_klines(cls, symbol: str, interval: int, unit: str) -> None | DataFrame:

        tablename = cls.klines_tablename(symbol, interval, unit)

        if not cls.is_table_exists(tablename):
            return None

        try:
            return read_sql(
                sql=tablename,
                con=cls.engine,
            )

        except Exception as ex_:
            raise print(
                "Unable to deserialize klines.\n\n"
                "This exception provided by:\n\n"
                f"{ex_.__traceback__.__str__()}"
            )

    @classmethod
    def is_table_exists(cls, name: str):
        """
        Checks if a table with the specified name exists in the database.

        :param name: name of the table to check for existence
        :return: `True` if the table exists in the database; otherwise, `False`.
        """
        return inspect(cls.engine).has_table(name)


Base.metadata.create_all(Database.engine)
