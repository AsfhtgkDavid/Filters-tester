from enum import Enum


class DatabaseSettings:
    _engine: str = 'postgresql'

    _user: str = getenv('POSTGRES_USER')
    _password: str = getenv('POSTGRES_PASSWORD')
    _host: str = getenv('POSTGRES_HOST')
    _port: str = getenv('POSTGRES_PORT')
    _name: str = getenv('POSTGRES_NAME')

    CONNECTION_STRING = f"{_engine}://{_user}:{_password}@{_host}:{_port}/{_name}"

    class Tables(str, Enum):
        KLINES = 'Klines'
