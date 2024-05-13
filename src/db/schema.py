from peewee import *


# pg_db = PostgresqlDatabase('postgres', user='postgres', password='111',
#                            host='localhost', port=5433)
pg_db = SqliteDatabase('/home/kalyrginas/tg_rag_QA/src/db/my_database.db')


class BaseModel(Model):
    class Meta:
        database = pg_db


class Account(BaseModel):
    id = PrimaryKeyField(column_name='id')
    tg_id = TextField(column_name='tg_id', unique=True, null=False)
    embeddings_serialized = TextField(column_name='embeddings_serialized', default=None, null=True)
    hash_file = TextField(column_name='hash_file', default=None, null=True)
    start_date = DateTimeField(column_name='start_date', default=None, null=False)

    class Meta:
        table_name = 'account'


# Скрипт для создания таблиц
if __name__ == "__main__":
    pg_db.connect()
    pg_db.create_tables([Account])
