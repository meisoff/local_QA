import base64
import hashlib
import json
import os
import shutil
from datetime import datetime
from os import getenv

from langchain_community.document_loaders import PyPDFLoader

from src.db import schema as db
from src.db.get_content import get_user_hash_file
from src.model.embeddings import embeddings_files, embed_and_write

PATH_TO_DATA = getenv('PATH_TO_DATA')


# Получение файла из временного хранилища
def get_hash_file(file_name):
    with open(PATH_TO_DATA + f"/{file_name}", "rb") as file:
        data = file.read()
        hash_file = hashlib.sha256(data).hexdigest()
        print(f'Хэш сумма файла: {hash_file}')
    return hash_file


# Сохраняем все файлы в папке
def save_files_from_base64(folder_path, files_base64):
    files_base64 = json.loads(files_base64)

    # Проверяем существование директории folder_path и создаем ее, если она отсутствует
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Перебираем все файлы в словаре files_base64
    for file_name, file_base64 in files_base64.items():
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as file:
            file_content = base64.b64decode(file_base64)
            file.write(file_content)


# Перебираем все файлы в папке, конвертируем в base64 и сериализуем
def files_to_base64(folder_path):
    files_base64 = {}

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:
                file_content = file.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                files_base64[file_name] = file_base64

    return json.dumps(files_base64)


# Сохранение данных о пользователе
def save_user_info(user_id, file_name, hash_file):
    try:
        account_id = db.Account.select().where(db.Account.tg_id == user_id)

        # embeddings = embeddings_files(file_name)
        #
        # # Сохраняем эмбеддинги во временное хранилище
        # embeddings.save(f"{PATH_TO_DATA}/{hash_file}")
        #
        # # Получаем сериализованные файлы
        # embeddings_serialized = files_to_base64(f"{PATH_TO_DATA}/{hash_file}")

        if account_id:
            # 1. Load the data
            loader = PyPDFLoader(f"{PATH_TO_DATA}/{file_name}")
            docs = loader.load()

            embed_and_write(docs, user_id)

            # (db.Account.update(embeddings_serialized=embeddings_serialized, hash_file=hash_file).where(db.Account.tg_id == user_id)).execute()
            (db.Account.update(hash_file=hash_file).where(db.Account.tg_id == user_id)).execute()
            print("Cохранили новую информацию в DB")

        else:
            # db.Account.create(tg_id=user_id, embeddings_serialized=embeddings_serialized, hash_file=hash_file, start_date=datetime.now())
            db.Account.create(tg_id=user_id, hash_file=hash_file, start_date=datetime.now())
    except Exception as e:
        raise e

    # finally:
        # shutil.rmtree(f"{PATH_TO_DATA}/{hash_file}")
        # print(f"Папка {PATH_TO_DATA}/{hash_file} успешно удалена вместе со всем содержимым.")


# Сохранение документов
async def save_file(file_name, user_id):
    # Проверка наличия файла в хранилище по hash
    hash_old_file = get_user_hash_file(user_id)
    hash_new_file = get_hash_file(file_name)
    if hash_new_file != hash_old_file:
            try:
                save_user_info(user_id, file_name, hash_new_file)

            except Exception as e:
                print(f"Ошибка при сохранении: {e}")
                raise e

            finally:
                os.remove(PATH_TO_DATA + f"/{file_name}")
                print(f"Файл {file_name} успешно удален из временного хранилища")

    else:
        os.remove(PATH_TO_DATA + f"/{file_name}")
        print(f"Файл {file_name} уже был загружен ранее и удален из временного хранилища")

