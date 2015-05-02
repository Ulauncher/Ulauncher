import os
from ulauncher_lib.ulauncherconfig import CACHE_DIR
from .Db import Db

__all__ = ['db']

db = Db(os.path.join(CACHE_DIR, 'user_queries.db'))
db.open()
