import psycopg2
import pandas as pd
from sqlalchemy.engine import create_engine
from configparser import ConfigParser
from config import PROJECT_DIR
import os

# 配置文件
conf = ConfigParser()
conf.read(os.path.join(PROJECT_DIR, "config/base.conf"), encoding="utf-8")

db_config_dict = {
    'username': conf.get('DB', 'username'),
    'password': conf.get('DB', 'password'),
    'host': conf.get('DB', 'host'),
    'port': conf.get('DB', 'port'),
    'db': conf.get('DB', 'db')
}


class DBManager(object):
    def __init__(self):
        # 连接数据库
        self.engine = create_engine(
            'postgresql+psycopg2://{username}:{password}@{host}:{port}/{db}'.format(
                username=db_config_dict['username'],
                password=db_config_dict['password'],
                host=db_config_dict['host'],
                port=db_config_dict['port'],
                db=db_config_dict['db']
            ))

    def write(self, df, dbname, mode='a'):
        if_exist = 'append' if mode == 'a' else 'replace'
        df.to_sql(dbname, self.engine, if_exists=if_exist, index=False)

    def read(self, dbname , limit=None):
        return pd.read_sql("select * from {0}".format(dbname), self.engine)

