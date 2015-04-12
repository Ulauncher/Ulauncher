import os
from ulauncher_lib.helpers import get_config_dir
from .Db import Db

__all__ = ['db']

db = Db(os.path.join(get_config_dir(), 'user_queries.db'))
db.open()
