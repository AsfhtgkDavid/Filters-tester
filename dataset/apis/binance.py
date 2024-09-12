from datetime import datetime, timedelta
import time

from binance import Client
from pandas import DataFrame, Series


class BinanceAPI:
    client = Client()

    __name__ = 'BinanceAPI'

    @classmethod
    def __get_klines_batch(
            cls,
            symbol: str,
            interval_str: str,
            start: int,
            end: int,
            retries: int = 20,
            retry_sleep_time: float = 20,
    ):
        """
        Fetches a batch of kline (candlestick) data for a given symbol and time interval

        :param symbol: trading symbol (e.g., 'BTCUSDT') for which to fetch kline data
        :param interval_str: interval as a string (e.g., '1m', '5m', '1h') for the klines
        :param start: start timestamp (in milliseconds) for fetching klines.
        :param end: end timestamp (in milliseconds) for fetching klines.
        :param retries:  number of times to retry fetching data in case of failure
        :param retry_sleep_time: number of seconds to wait between retries
        :return: list of kline data if successful, or None if all retries fail
        """
        for retry in range(retries):
            try:
                return cls.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval_str,
                    start_str=f'{start:%Y-%m-%d}',
                    end_str=f'{end:%Y-%m-%d}',
                )
            except Exception as e:
                print(f"{retry}. {e}")
                time.sleep(retry_sleep_time)
                continue

    @classmethod
    def __make_df(cls, klines: list):
        """
        Converts a list of kline data into a pandas DataFrame with specific columns

        :param klines: kline data where each element is a list or tuple representing the kline attributes
        :return:
        """
        df = DataFrame(
            klines,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "CloseTime",
                "QuoteVolume",
                "NumberOfTrades",
                "TakerBuyBaseVolume",
                "TakerBuyQuoteVolume",
                "Ignore",
            ],
        )
        df.drop(
            labels=[
                "CloseTime",
                "QuoteVolume",
                "NumberOfTrades",
                "TakerBuyBaseVolume",
                "TakerBuyQuoteVolume",
                "Ignore",
            ],
            axis=1,
            inplace=True,
        )
        df = df.astype("float", copy=True)
        df['time'] = Series(map(lambda el: datetime.fromtimestamp(el // 1000), df['time']))
        return df

    @classmethod
    def get_klines(
            cls,
            symbol: str,
            interval: int,
            unit: str,
            start: datetime,
            end: datetime,
            retries: int = 20,
            retry_sleep_time: float = 20,
            sleep_time: float = 0.2,
    ):
        """
        Retrieves historical kline (candlestick) data for a specified symbol and interval from the exchange

        :param symbol: trading symbol (e.g., 'BTCUSDT') for which to fetch kline data
        :param interval: interval for each kline in minutes (e.g., 1, 5, 15, 60)
        :param unit: unit of the interval (e.g., 'm' for minutes, 'h' for hours).
        :param start: starting datetime for fetching klines.
        :param end: ending datetime for fetching klines.
        :param retries: number of times to retry fetching data in case of failure
        :param retry_sleep_time: number of seconds to wait between retries.
        :param sleep_time: number of seconds to wait between each batch request to avoid rate limiting
        :return: pandas DataFrame containing the kline data with columns:
            "time", "open", "high", "low", "close", "volume"
        """
        _klines = []

        if end - start < timedelta(days=15):
            kline_time_ms = timedelta(seconds=(end - start).total_seconds())
        else:
            kline_time_ms = timedelta(days=15)

        while True:
            if start >= end:
                break
            _end = start + kline_time_ms

            _klines.extend(cls.__get_klines_batch(
                symbol=symbol,
                interval_str=f"{interval}{unit}",
                start=start,
                end=_end,
                retries=retries,
                retry_sleep_time=retry_sleep_time,
            ))

            time.sleep(sleep_time)
            start = _end
        return cls.__make_df(_klines)
