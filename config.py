from enum import Enum


class DatabaseSettings:
    _engine: str = 'postgresql'

    _user: str = 'POSTGRES_USER'
    _password: str = 'POSTGRES_PASSWORD'
    _host: str = 'POSTGRES_HOST'
    _port: str = 'POSTGRES_PORT'
    _name: str = 'POSTGRES_NAME'

    CONNECTION_STRING = f"{_engine}://{_user}:{_password}@{_host}:{_port}/{_name}"

    class Tables(str, Enum):
        KLINES = 'Klines'
