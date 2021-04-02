import requests
from modules.settings import TELEGRAM_URL, TOKEN
"""
Функции помогающие обращаться к телеграмму.

"""


def events_InlineKeyboardMarkup(events):

    board = []
    for event in events:
        board.append([{"text": f"{event['start_point']} (дата добавления {event['add_date']})", "callback_data":f"#del_{event['event_id']}"}])

    return {'inline_keyboard': board}


def start_ReplyKeyboardMarkup():
    """
    обычная стартовая клавиатура
    """
    board = [
        [{"text": "Записаться"}, {"text": "Отменить запись"}],
        [{"text": "Написать Юме"}, {"text": "Help"}]
    ]
    return {'keyboard': board}


def start_InlineKeyboardMarkup():
    """
    :return: dict keyboard json-ифицируемый объект стартовой инлайн клавиатуры
    """
    board = [
        [{"text": "Тема консультации", "callback_data": "#tema"}],
        [{"text": "⌛ 30 минут", "callback_data": "#t_30min"}],
        [{"text": "⌛ 90 минут", "callback_data": "#t_90min"}]
    ]
    return {'inline_keyboard': board}


def description_InlineKeyboardMarkup():
    """
    :return: dict keyboard json-ифицируемый объект стартовой инлайн клавиатуры
    """
    board = [
        [{"text": "Родительство", "callback_data": "#description_0"}],
        [{"text": "Партнёрство", "callback_data": "#description_1"}],
        [{"text": "Работа/карьера", "callback_data": "#description_2"}],
        [{"text": "Родительская семья", "callback_data": "#description_3"}],
        [{"text": "Разобраться с собой", "callback_data": "#description_4"}],
        [{"text": "Другое", "callback_data": "#description_5"}]
    ]
    return {'inline_keyboard': board}





def free_InlineKeyboardMarkup(days, width=3):
    """
    :return: dict keyboard json-ифицируемый объект стартовой инлайн клавиатуры
    """
    board = []
    line = []
    flag = 0
    for day in days:
        line.append({"text": f"▷ {day[1]} ({day[2][:-9]})", "callback_data": f"#day_{day[2]}"})
        flag += 1

        if flag == width:
            board.append(line)
            line = []
            flag = 0
        if len(days) - len(board)*width - flag == 0:
            board.append(line)
    board.append([{"text": "главное меню", "callback_data": "#menu"}])
    return {'inline_keyboard': board}


def freehour_InlineKeyboardMarkup(sessions, width=3):
    """
    :return: dict keyboard json-ифицируемый объект стартовой инлайн клавиатуры
    """
    board = []
    line = []
    flag = 0
    for session in sessions:
        line.append({"text": f"▷ {session[0].hour}:{'00' if session[0].minute == 0 else session[0].minute}",
                     "callback_data": f"#ins_{str(session[0])[11:13]}-{'00' if session[0].minute == 0 else session[0].minute}_{session[1]}_{session[2]}_{session[3]}"})
        flag += 1
        if flag == width:
            board.append(line)
            line = []
            flag = 0
        if len(sessions) - len(board)*width - flag == 0:
            board.append(line)
    board.append([{"text": "главное меню", "callback_data": "#menu"}])
    return {'inline_keyboard': board}


def send_message(message, chat_id, inline_keyboard=None):
    '''
    Отправка сообщения на сервер телеграмм
    '''
    if inline_keyboard is None:
        data = {
            "chat_id": chat_id,
            "text": message
                }
    else:
        data = {
            "chat_id": chat_id,
            "text": message,
            "reply_markup": inline_keyboard
                }
    return requests.post(f"{TELEGRAM_URL}{TOKEN}/sendMessage", data=data)


def editMessageText(message, chat_id, message_id, inline_keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": message,
        "message_id": message_id,
        "reply_markup": inline_keyboard
    }

    return requests.post(f"{TELEGRAM_URL}{TOKEN}/editMessageText", data=data)


def editMessageCaption(message, chat_id, message_id):
    data = {
        "chat_id": chat_id,
        "text": message,
        "message_id": message_id,
    }

    return requests.post(f"{TELEGRAM_URL}{TOKEN}/editMessageCaption", data=data)


def sendPhoto(chat_id, photo, caption=None, reply_markup=None):
    data = {"chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "reply_markup": reply_markup
            }
    return requests.post(f"{TELEGRAM_URL}{TOKEN}/sendPhoto", data=data)


def deleteMessage(chat_id, message_id):
    data = {"chat_id": chat_id,
            "message_id": message_id,
            }
    return requests.post(f"{TELEGRAM_URL}{TOKEN}/deleteMessage", data=data)


def answerCallbackQuery(callback_query_id, text, show_alert=True, url=None, cache_time=None):
    data = {"callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert
            }

    return requests.post(f"{TELEGRAM_URL}{TOKEN}/answerCallbackQuery", data=data)


