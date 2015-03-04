import os
from xdg.BaseDirectory import xdg_config_home
from .QueryDb import QueryDb

__all__ = ['db']

db = QueryDb(os.path.join(xdg_config_home, 'ulauncher', 'user_queries.db'))
db.open()