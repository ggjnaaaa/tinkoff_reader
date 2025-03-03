# routes/directory/bot.py

from sqlalchemy.orm import Session
from typing import Optional
from models import Users, TgTmpUsers

def check_user_and_store_tg_tmp_user(db: Session, tg_nickname: str, chat_id: int):
    """
    Проверяет, существует ли пользователь с указанным tg-ником, и записывает его в tg_tmp_users.
    Если запись уже существует, обновляет её при необходимости.
    :param db: Сессия базы данных.
    :param tg_nickname: Telegram никнейм пользователя.
    :param chat_id: Telegram chat_id пользователя.
    :return: Кортеж (user, message): пользователь и сообщение.
    """
    # Проверяем, существует ли пользователь с таким tg-ником
    user = db.query(Users).filter(Users.tg == tg_nickname).first()
    if not user:
        return None, "У вас нет доступа к этому боту."

    # Проверяем наличие записи в tg_tmp_users
    tmp_user = db.query(TgTmpUsers).filter(TgTmpUsers.user_id == user.id).first()

    if tmp_user:
        # Если chat_id совпадает, ничего не делаем
        if tmp_user.chat_id == chat_id:
            return user, f"Доступ уже разрешён. Номер карты: {user.card_number}"
        else:
            # Если chat_id отличается, обновляем его
            tmp_user.chat_id = chat_id
            db.commit()
            return user, f"Доступ обновлён с новым chat_id: {chat_id}"
    else:
        # Если записи нет, создаём новую
        new_tmp_user = TgTmpUsers(user_id=user.id, chat_id=chat_id)
        db.add(new_tmp_user)
        db.commit()
        return user, f"Доступ разрешён. Номер карты: {user.card_number}"


def get_card_number_by_chat_id(db: Session, chat_id: int) -> Optional[str]:
    """
    Получение номера карты из базы данных по chat_id.
    """
    tg_user = db.query(TgTmpUsers).filter(TgTmpUsers.chat_id == chat_id).first()
    return tg_user.user.card_number if tg_user and tg_user.user else None
