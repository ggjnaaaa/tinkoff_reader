# routes/directory/tinkoff/users_info.py

# Стандартные модули Python
from collections import defaultdict

# Собственные модули
from models import TgTmpUsers, Users


def get_all_cards_by_chat_ids(db, chat_ids):
    """
    Возвращает словарь, где ключ — это chat_id, а значение — список карт, связанных с этим chat_id.
    """
    results = db.query(TgTmpUsers.chat_id, Users.card_number).join(Users).filter(
        TgTmpUsers.chat_id.in_(chat_ids)
    ).all()

    cards_by_chat_id = defaultdict(list)
    for chat_id, card_number in results:
        cards_by_chat_id[str(chat_id)].append(card_number)

    return cards_by_chat_id