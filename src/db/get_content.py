from src.db import schema as db

def get_user_hash_file(user_id):
    try:
        account_id = db.Account.select().where(db.Account.tg_id == user_id)

        if account_id:
            hash_file = (db.Account.select(db.Account.hash_file).where(db.Account.tg_id == user_id))
            print(f'Получили hash из db {hash_file}')
            return hash_file
        else:
            print('Пользователь не найден')
            return None

    except Exception as e:
        raise e