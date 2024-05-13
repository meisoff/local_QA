from src.db import schema as db


# def get_user_hash_file_fake(user_id):
#
#     hash_file_fake = "184430b6cc6f73627bdcd17a7d2d66473ba374c81e2ec2be966d8e4466af3cca"
#     print(user_id)
#     # Возвращается hash файла
#     return hash_file_fake


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