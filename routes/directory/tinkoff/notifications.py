# routes/directory/tinkoff/notifications.py

# Сторонние модули
from sqlalchemy.orm import Session
from sqlalchemy.future import select

# Собственные модули
from models import (
    TgTmpUsers,
    UserNotifications,
    Users
) 

def get_chat_ids_for_error_notifications(db: Session):
    """
    Получает список chat_id из tg_tmp_users для пользователей,
    которым нужно отправлять сообщения об ошибках.
    """
    query = (
        select(TgTmpUsers.chat_id)
        .join(UserNotifications, TgTmpUsers.user_id == UserNotifications.user_id)
        .where(UserNotifications.receive_error_notifications == True)
    )
    result = db.execute(query)
    return [str(row[0]) for row in result.fetchall()]


def get_chat_ids_for_transfer_notifications(db: Session):
    """
    Получает список chat_id из tg_tmp_users для пользователей,
    которым нужно отправлять все расходы.
    """
    query = (
        select(TgTmpUsers.chat_id)
        .join(UserNotifications, TgTmpUsers.user_id == UserNotifications.user_id)
        .where(UserNotifications.receive_transfer_notifications == True)
    )
    result = db.execute(query)
    return [str(row[0]) for row in result.fetchall()]


def get_card_nums_for_transfer_notifications(db: Session):
    """
    Получает список карт из users для пользователей,
    которым нужно отправлять все расходы.
    """
    query = (
        select(Users.card_number)
        .join(UserNotifications, Users.id == UserNotifications.user_id)
        .where(UserNotifications.receive_transfer_notifications == True)
    )
    result = db.execute(query)
    return [str(row[0]) for row in result.fetchall()]