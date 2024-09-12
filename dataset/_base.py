from datetime import datetime
from inspect import signature

from pandas import DataFrame, Series, concat

from numpy import ndarray, array

from .indicators import base as indicators
from .apis import BinanceAPI, Exchanges
from utils import TimeFrame
from database import Database

indicators = [(name, func) for name, func in indicators.__dict__.items() if '__' not in name and callable(func)]


class Dataset:
    exchange: Exchanges = BinanceAPI

    def __init__(self, name: str, content: DataFrame | None = None):
        self.normalization_coefficients = {}
        self.name = name

        self.x_train: ndarray = array([])
        self.y_train: ndarray = array([])

        self.x_test: ndarray = array([])
        self.y_test: ndarray = array([])

        self.is_ready: bool = False

        self.content: DataFrame = content
        self.base_content = self.content[['time', 'open', 'high', 'low', 'close']].copy()

    def __getitem__(self, item):
        """
         Retrieves an item or a slice of items from the content attribute of the class instance.

        :param item: The item or slice to retrieve.
        :return:
        If `item` is a slice object, returns a new instance of the class with a subset of the content based on the slice
        If `item` is a single index or a list of indices, returns the corresponding values from the content.
        """
        if isinstance(item, slice):
            dataset = self.__class__(self.name, self.content.iloc[item])
            dataset.is_ready = self.is_ready
            dataset.normalization_coefficients = self.normalization_coefficients
            dataset.base_content = self.base_content[item]
            return dataset

        return self.content[item]

    @classmethod
    def make(
            cls,
            symbol: str,
            timeframe: TimeFrame,
            start: datetime,
            end: datetime,
            exchange: Exchanges = None,
            **kwargs
    ):
        """
         Creates or updates an instance of the class with market data (klines) for the specified symbol and time range

        :param symbol: market symbol
        :param timeframe: timeframe
        :param start: start datetime for the data retrieval
        :param end: end datetime for the data retrieval
        :param exchange: optional exchange parameter to specify the data source or exchange for fetching klines
        :param kwargs: additional keyword arguments to pass to the data fetching method
        :return: instance of the class with the data for the specified symbol and time range.
        """
        if exchange is not None:
            cls.exchange = exchange

        changes = False
        interval, unit = timeframe.get(cls.exchange.__name__)

        klines = Database.get_klines(symbol, interval, unit)
        if klines is not None:
            _start, *_, _end = klines['time']
            timeline = ()

            if start.date() < _start.date():
                changes = True
                timeline += (cls.__parse_new_klines(symbol, interval, unit, start, _start), )

            timeline += (klines, )

            if end.date() > _end.date():
                changes = True
                timeline += (cls.__parse_new_klines(symbol, interval, unit, _end, end), )

            if len(timeline) > 1:
                klines = concat(timeline).drop_duplicates().reset_index(drop=True)

        else:
            changes = True

            klines = cls.__parse_new_klines(
                symbol=symbol,
                interval=interval,
                unit=unit,
                start=start,
                end=end,
                **kwargs
            )

        if changes and not klines.empty:
            Database.add_klines(klines, symbol, interval, unit)

        return cls(
            name=Database.klines_tablename(symbol, interval, unit),
            content=klines[start <= klines['time']][end > klines['time']]
        )

    @classmethod
    def __parse_new_klines(
            cls,
            symbol: str,
            interval: int,
            unit: str,
            start: datetime,
            end: datetime,
            **kwargs
    ):
        """
        Fetch and process kline (candlestick) data for a given trading symbol, time interval, and time range.
            Additionally, compute and append selected technical indicators to the kline data.

        :param symbol: symbol for which to fetch the kline data
        :param interval: time interval for the klines
        :param unit: unit of the interval (e.g., 'm' for minutes, 'h' for hours)
        :param start: start datetime for fetching klines
        :param end: end datetime for fetching klines
        :param kwargs: additional parameters that may be passed to the exchange's `get_klines` method
        :return:
        """
        klines = cls.exchange.get_klines(
            symbol=symbol,
            interval=interval,
            unit=unit,
            start=start,
            end=end,
            **kwargs
        )
        return cls.calculate_indicators_values(klines)

    @staticmethod
    def calculate_indicators_values(klines):
        indicators_df = DataFrame()

        for name, indicator in indicators:
            args = [param.name.removesuffix('_') for param in signature(
                indicator).parameters.values() if param.default and param.name != 'kwargs']

            try:
                resp = indicator(*[klines[col] for col in args])
            except Exception:
                continue

            if isinstance(resp, DataFrame):
                if all(resp.count() < len(indicators_df) * .9):
                    continue

                resp.drop(columns=[col for col in resp.columns if len(resp[col]) * .9 > resp[
                    col].count() or col in indicators_df.columns], inplace=True)
                indicators_df = concat([indicators_df, resp], axis=1)

            elif isinstance(resp, Series):
                if resp.count() < len(indicators_df) * .9:
                    continue
                indicators_df = concat([indicators_df, resp], names=[*indicators_df.columns, name], axis=1)

        return concat((klines, indicators_df), axis=1).dropna()

