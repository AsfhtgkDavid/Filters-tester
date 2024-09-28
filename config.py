from enum import Enum
from os import getenv
from dotenv import load_dotenv

load_dotenv()

class DatabaseSettings:
    _engine: str = 'postgresql'

    _user: str = getenv('user')
    _password: str = getenv('pass')
    _host: str = 'localhost'
    _port: str = '5432'
    _name: str = getenv('name')

    CONNECTION_STRING = f"{_engine}://{_user}:{_password}@{_host}:{_port}/{_name}"

    class Tables(str, Enum):
        KLINES = 'Klines'
