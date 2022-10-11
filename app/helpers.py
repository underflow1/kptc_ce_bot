import os
import sqlite3
import logging
from dataclasses import astuple, dataclass

from models import PhotoModel, LocationModel


db_path ='app.db'

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(funcName)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


class SQLiteExtractor:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.curs = self.conn.cursor()
        logger.info('Connected to SQLite')


    def add_record(self, model_dict: dict, model: dataclass):
        data_model = model(**model_dict)
        logger.info(data_model)
        fields = ', '.join(data_model.__dict__)
        values = ', '.join(('?',) * len(data_model.__dict__))
        table_name = model.__tablename__
        query = f'''
            INSERT INTO {table_name}
                ({fields})
            VALUES
                ({values})
            ON CONFLICT (id) DO NOTHING
                '''
        args = astuple(data_model, tuple_factory=tuple)

        self.curs.execute(query, args)
        self.conn.commit()


    def check_user(self, user_id: str) -> bool:
        query = 'SELECT * FROM user WHERE user_id = ?'
        logger.info(query)
        logger.info(user_id)
        self.curs.execute(query, (user_id,))
        result = self.curs.fetchall()
        if len(result) > 0:
            return True
        return False


    def queryTableData(self, table_name: str) -> bool:
        query = f'SELECT * FROM {table_name}'
        try:
            self.curs.execute(query)
        except Exception as e:
            print(e)
            return False
        return True


    def extractTableDataLimit(self, table_name: str, limit: int = 100) -> list:
        query = f'SELECT * FROM {table_name}'
        try:
            self.curs.execute(query)
            rows = self.curs.fetchmany(limit)
        except Exception as e:
            logger.info(e)
            return False
        logger.info(rows)
        return rows
