import os
from xdg.BaseDirectory import xdg_config_home
from .Db import Db

__all__ = ['db']

db = Db(os.path.join(xdg_config_home, 'ulauncher', 'user_queries.db'))
db.open()
