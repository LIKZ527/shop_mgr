import pymysql
from src.config import DB_CONFIG

def get_conn(**kw):
    cfg = {**DB_CONFIG, **kw}
    return pymysql.connect(**cfg, cursorclass=pymysql.cursors.DictCursor)