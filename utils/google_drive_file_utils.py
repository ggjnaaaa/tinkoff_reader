# utils/google_drive_file_utils.py

import os
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from utils.google_drive import get_drive_service


def upload_file(file_path, folder_id=None):
    """
    Выгружает файл в гугл диск.
    """
    service = get_drive_service()
    file_name = os.path.basename(file_path)

    # Проверяем, есть ли уже такой файл в Google Drive
    query = f"name='{file_name}' and trashed=false"
    if folder_id:
        query += f" and '{folder_id}' in parents"

    existing_files = service.files().list(q=query, fields="files(id)").execute().get("files", [])

    if existing_files:
        file_id = existing_files[0]["id"]
        print(f"Файл {file_name} найден. Обновляем его...")

        media = MediaFileUpload(file_path, resumable=True)
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        print(f"Файл {file_name} не найден. Загружаем новый...")

        file_metadata = {"name": file_name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    print(f"Файл {file_name} загружен в гугл диск.")


def download_file(file_name, destination_folder="./chrome_data/"):
    """
    Выгружает файл из гугл диска.
    """
    service = get_drive_service()
    
    query = f"name='{file_name}' and trashed=false"
    existing_files = service.files().list(q=query, fields="files(id)").execute().get("files", [])

    if not existing_files:
        print(f"Файл {file_name} не найден в Google Drive.")
        return False
    
    file_id = existing_files[0]["id"]
    request = service.files().get_media(fileId=file_id)
    
    os.makedirs(destination_folder, exist_ok=True)
    destination_path = os.path.join(destination_folder, file_name)

    with open(destination_path, "wb") as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    
    print(f"Файл {file_name} загружен в {destination_path}")
    return True
