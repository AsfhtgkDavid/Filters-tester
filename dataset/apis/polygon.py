import time
from datetime import datetime

from requests import Session
from pandas import DataFrame, to_datetime, concat


class PolygonAPI:
    DOMAIN: str = 'https://api.polygon.io/'
    API_KEY: str = 'apiKey=_o8tglR39WDMJaHW3GGZfZAIoSh5CcIs'

    __name__ = 'PolygonAPI'

    @staticmethod
    def __datetime_to_str(start: datetime, end: datetime) -> (str, str):
        """
        Converts the start and end datetime objects to formatted strings.

        :param start: starting datetime object.
        :param end: ending datetime object.
        :return: tuple containing the formatted start and end date strings
        """

        return f'{start:%Y-%m-%d}/{end:%Y-%m-%d}'

    @staticmethod
    def __timeframe_to_str(interval: int, unit: str) -> (str, str):
        """
        Converts the interval and unit into a formatted string.

        :param interval: number of units (e.g., 1, 5, 15, 60).
        :param unit: unit of the interval (e.g., 'm' for minutes, 'h' for hours, 'd' for days)
        :return: tuple containing the formatted interval and unit string
        """

        return f'{interval}/{unit}'

    @staticmethod
    def __params_to_str(params) -> str:
        """
        Converts a dictionary of parameters into a query string.

        :param params: dictionary of parameters
        :return: string representing the parameters in query string format
        """

        link = '?'
        for key, value in params.items():
            link += f'{key}={value}&'
        return link

    @staticmethod
    def __resp_to_df(resp) -> DataFrame:
        """
        Converts a response dictionary into a pandas DataFrame.

        :param resp: dictionary containing the response data
        :return: pandas DataFrame with columns 'time', 'open', 'high', 'low', 'close', and 'volume'.
                 Returns an empty DataFrame if the input `resp` is None.
        """

        if resp is None:
            return DataFrame()

        df = DataFrame.from_dict(resp)
        df = df[['t', 'o', 'h', 'l', 'c', 'v']]
        df['t'] = to_datetime(df['t'], unit='ms')
        return df.rename(columns={
            't': 'time', 'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'})

    @classmethod
    def get_candles_link(
            cls,
            symbol: str,
            tf: str,
            timeline: str,
            **kwargs: str
    ) -> str:
        """
        Constructs a URL for fetching candlestick data from an API.

        :param symbol: trading symbol (e.g., 'BTCUSDT') for which to retrieve k_lines data
        :param tf: time frame for the k_lines data (e.g., '1min', '5min', '1h')
        :param timeline: start date/time for the data request in ISO format (e.g., '2024-01-01T00:00:00Z')
        :param kwargs: additional query parameters to include in the request URL, provided as key-value pairs
        :return: string representing the complete URL for the API request.
        """

        return cls.DOMAIN + f'v2/aggs/ticker/{symbol}/range/{tf}/{timeline}' + \
            cls.__params_to_str(kwargs) + cls.API_KEY

    @classmethod
    def get_symbols_link(cls, **kwargs: str) -> str:
        """
        Construct and return a URL to retrieve ticker symbols data from an API, including any additional
            query parameters provided as keyword arguments.
        :return:
        """

        return cls.DOMAIN + f'v3/reference/tickers' + cls.__params_to_str(kwargs) + cls.API_KEY

    @classmethod
    def get_symbols(cls, **kwargs):
        """
        Retrieve and return a dictionary of trading symbols with their associated metadata by making
            multiple API requests. This method handles pagination and rate limiting.

        Args:
            **kwargs: Additional query parameters to be included in the API request URL as key-value pairs.
                  These parameters are passed to the `get_symbols_link` method to construct the request URL.

        Returns:
            dict: A dictionary where the keys are trading symbols (tickers) and the values are dictionaries
                  containing metadata for each symbol.

        """
        symbols = {}

        with Session() as s:
            url = cls.get_symbols_link(
                limit='1000',
                active='true',
                **kwargs
            )
            while True:
                resp = s.get(url).json()

                if error := resp.get('error'):
                    if 'maximum requests per minute' in error:
                        time.sleep(65)
                        continue
                    break

                for item in resp['results']:
                    symbols[item.pop('ticker')] = item

                url = resp.get('next_url')
                if url is None:
                    break
                url += '&' + cls.API_KEY

        return symbols

    @classmethod
    def get_klines(
            cls,
            symbol: str,
            interval: int,
            unit: str,
            start: datetime,
            end: datetime,
            **kwargs: str
    ) -> None | DataFrame | dict:
        """
        Fetches historical candlestick data for a given symbol and time range.

        :param symbol: trading symbol (e.g., 'BTCUSDT') for which to retrieve k_lines data.
        :param interval: interval for k_lines data
        :param unit: unit of the interval
        :param start: start date and time for the data request
        :param end: end date and time for the data request
        :return: pandas DataFrame containing the k_lines data, or `None` if no data is retrieved
        """

        result = DataFrame()

        with Session() as s:
            while True:
                resp = s.get(cls.get_candles_link(
                    symbol=symbol,
                    tf=cls.__timeframe_to_str(interval, unit),
                    timeline=cls.__datetime_to_str(start, end),
                    limit='50000',
                    **kwargs
                )).json()
                resp = cls.__resp_to_df(resp.get('results'))

                try:
                    if resp['time'][resp.last_valid_index()] == start:
                        break

                    result = concat([result, resp], ignore_index=True)
                    last = result['time'][result.last_valid_index()]

                    if last >= end:
                        break
                    start = last

                except Exception:
                    break

        return result
