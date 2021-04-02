from flask import Flask
from flask import request
from flask import abort
from flask import jsonify

from apscheduler.schedulers.background import BackgroundScheduler

import json
from operator import itemgetter

from modules.telegram_api import *
from modules.calendar_api import *
from modules.settings import FIRST_MESSAGE, HELP_MESSAGE, TIMEZONE, SCHEDULER_TIME
from modules.sqlite_connector import *


logging.basicConfig(filename="bot.log", filemode='w', level=30)
logging.warning(f"flask_bot started... ({datetime.datetime.today()})")

app = Flask(__name__)

bindql = SqliteDb()
bindql.create_table()
bindql.create_events_table()


def sensor():
    """ Напоминания за 24 часа до сессии и об оплате сразу после сессии"""

    logging.info(f"Scheduler:{datetime.datetime.today()}")

    sql = SqliteDb()

    # проверим нужно ли отправить уведомление за 24 часа
    pre_events = sql.select_pre_events()
    if pre_events:
        for event in pre_events:
            event = dict(event)
            event_date = event["start_point"]
            datetime_event = datetime.datetime.strptime(event_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=TIMEZONE)

            # если событие произойдет раньше 24 часов то пометим как будто уведомление отправлено
            if datetime_event < datetime.datetime.today()+datetime.timedelta(hours=23):
                sql.update_notice(id=event["id"], prenotice=True, paynotice=False)


            a = datetime_event - datetime.timedelta(minutes=int(SCHEDULER_TIME/2)+1)
            b = datetime_event + datetime.timedelta(minutes=int(SCHEDULER_TIME/2)+1)
            if a <= datetime.datetime.today() + datetime.timedelta(hours=24) <= b:
                id = event["id"]
                user = sql.get_table(tgid=event["tgid"])
                chat_id = user[0]["chatid"]

                notice_message = f"""

Напоминаю, что ваша сессия состоится через 24 часа ({datetime_event}) TZ+3:00

https://zoom.us/j/6424000769?pwd=F7cJBUuNAzA
                
                """
                sql.update_notice(id=event["id"], prenotice=True, paynotice=False)
                send_message(message=notice_message, chat_id=chat_id)

    # проверим нужно ли отправить напоминание об оплате
    pay_events = sql.select_pay_events()
    if pay_events:
        for pay_event in pay_events:
            dau = dict(pay_event)
            dau_date = dau["start_point"]
            session = dau["session"]

            user_dau = sql.get_table(tgid=dau["tgid"])
            chat_id = user_dau[0]["chatid"]

            datetime_dau = datetime.datetime.strptime(dau_date, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(
                hours=TIMEZONE) + datetime.timedelta(minutes=session)
            if datetime_dau < datetime.datetime.today():
                pay_message = f"""

::::::::::::::::::::::::::::::::::::

Ваша сессия недавно закончилась. ({datetime_dau})
Не забудьте оплатить, если вы это еще не сделали.

::::::::::::::::::::::::::::::::::::

                                """

                sql.update_notice(id=dau["id"], prenotice=True, paynotice=True)
                send_message(message=pay_message, chat_id=chat_id)

sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor, 'interval', minutes=SCHEDULER_TIME)
sched.start()


@app.route("/", methods=['POST'])
def telegram_bot():
    data = request.json
    if data:
        # callback part
        if "callback_query" in data:
            chat_id = data['callback_query']['message']['chat']['id']
            call_data = data['callback_query']['data']
            message_id = data['callback_query']['message']['message_id']
            telegram_id = data['callback_query']['from']['id']
            callback_query_id = data['callback_query']['id']

            if call_data == "#tema":
                send_message(message='Выберите ваш вопрос',
                             chat_id=chat_id,
                             inline_keyboard=json.dumps(description_InlineKeyboardMarkup()))

            if call_data.startswith("#description_"):
                descriptions = ["Родительство", "Партнёрство", "Работа/карьера", "Родительская семья",
                                "Разобраться с собой", "Другое"]
                descript = descriptions[int(call_data[13:])]
                sql = SqliteDb()
                sql.update_description(description=descript, tgid=telegram_id)
                answerCallbackQuery(callback_query_id=callback_query_id,
                                    text=f'Выбрана тема - {descript}',
                                    show_alert=True)
                deleteMessage(chat_id=chat_id, message_id=message_id)

            if call_data.startswith("#del_"):
                event_id = call_data[5:]
                calendar = GoogleCalendar()
                calendar.patch_event(eventId=event_id)
                sql = SqliteDb()
                sql.delete_event(tgid=telegram_id, event_id=event_id)
                deleteMessage(chat_id=chat_id, message_id=message_id)


            if call_data.startswith("#menu"):
                editMessageText(message=FIRST_MESSAGE, chat_id=chat_id, message_id=message_id,
                                inline_keyboard=json.dumps(start_InlineKeyboardMarkup()))

            if call_data.startswith("#t_"):
                gl = GoogleCalendar()
                event_list = gl.get_events_list()

                # формируем список свободных дней и генерим клавиатуру
                free_days = []
                for time in event_list['items']:
                    if time['summary'] == "free":
                        dams = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
                        datetime_object = datetime.datetime.strptime(time['start']['dateTime'][:-15], "%Y-%m-%d")
                        free_days.append(
                            (datetime_object.day,
                             dams[datetime_object.weekday()],
                             f"{time['start']['dateTime'][:-15]}_{call_data}")
                        )

                CHOICEDAY_MESSAGE = f"""

Вы выбрали сессию длительностью {call_data[3:5]} минут. 

Выберите свободный день.

"""
                editMessageText(message=CHOICEDAY_MESSAGE,
                                chat_id=chat_id,
                                message_id=message_id,
                                inline_keyboard=json.dumps(free_InlineKeyboardMarkup(days=sorted(set(free_days),
                                                                                                 key=itemgetter(2)))))

            if call_data.startswith("#day_"):
                datetime_object = datetime.datetime.strptime(call_data[5:15], "%Y-%m-%d")
                session_delta = int(call_data[19:-3])

                # Получаем свободные интервалы для выбранного дня/ проверяем на текущий день.
                gl = GoogleCalendar()
                if datetime_object.day == datetime.datetime.today().day and datetime_object.month == datetime.datetime.today().month:
                    timemin = datetime.datetime.today()- datetime.timedelta(hours=TIMEZONE)
                    timemax = datetime.datetime(year=datetime.datetime.today().year,
                                                month=datetime.datetime.today().month,
                                                day=datetime.datetime.today().month,
                                                hour=23,
                                                minute=59) - datetime.timedelta(hours=TIMEZONE)
                else:
                    timemin = datetime_object - datetime.timedelta(hours=TIMEZONE)
                    timemax = datetime_object + datetime.timedelta(hours=23) - datetime.timedelta(hours=TIMEZONE)

                event_list = gl.get_events_list(delta=None,
                                                timeMin=timemin.isoformat() + 'Z',
                                                timeMax=timemax.isoformat() + 'Z')
                free_intervals = []
                for event in event_list["items"]:
                    if event['summary'] == "free":
                        free_intervals.append((event['start']['dateTime'][:-6], event['end']['dateTime'][:-6]))

                # создаем клавиатуру нарезая интервалы на сессии
                sessions = []
                for i in free_intervals:
                    start = datetime.datetime.strptime(i[0], "%Y-%m-%dT%H:%M:%S")
                    end = datetime.datetime.strptime(i[1], "%Y-%m-%dT%H:%M:%S")

                    while start.hour * 60 + start.minute + session_delta <= end.hour * 60 + end.minute:
                        sessions.append((start, session_delta, i[0], end))
                        start += datetime.timedelta(minutes=session_delta)

                CHOICEHOUR_MESSAGE = f"""
◯

Вы выбрали {session_delta} минут на {str(datetime_object)[:-9]}

Выберите подходящее время.

◯
"""

                editMessageText(message=CHOICEHOUR_MESSAGE, chat_id=chat_id, message_id=message_id,
                                inline_keyboard=json.dumps(freehour_InlineKeyboardMarkup(sessions)))

            if call_data.startswith("#ins_"):
                start_interval = datetime.datetime.strptime(call_data[14:33], "%Y-%m-%dT%H:%M:%S")
                end_interval = datetime.datetime.strptime(call_data[36:], "%y-%m-%d %H:%M:%S")
                start_point = datetime.datetime(start_interval.year,
                                                start_interval.month,
                                                start_interval.day,
                                                hour=int(call_data[5:7]),
                                                minute=int(call_data[8:10])) - datetime.timedelta(hours=TIMEZONE)

                end_point = start_point + datetime.timedelta(minutes=int(call_data[11:13]))

                # записываем в календарь main и создаем free записи если это нужно pre и post и удаляем event_g
                calendar = GoogleCalendar()

                ggh = start_point
                ind = ggh + datetime.timedelta(minutes=9)

                event_g = calendar.get_events_list(delta=None, timeMin=ggh.isoformat() + 'Z',
                                                   timeMax=ind.isoformat() + 'Z')

                eventId = event_g["items"][0]["id"]

                calendar.delete_event(eventId=eventId)

                # извлекаем из базы данных описание и имя человека
                sql = SqliteDb()
                ud = sql.get_table(tgid=telegram_id)
                user_data = ud[0]


                event_main = calendar.create_event_dict(summary=user_data["name"],
                                                        description=user_data["description"],
                                                        start_datetime=start_point.isoformat() + 'Z',
                                                        end_datetime=end_point.isoformat() + 'Z')

                start_interval -= datetime.timedelta(
                    hours=TIMEZONE)
                pre_delta = start_point - start_interval

                if pre_delta.seconds != 0:
                    event_pre = calendar.create_event_dict(summary="free",
                                                           description=None,
                                                           start_datetime=start_interval.isoformat() + 'Z',
                                                           end_datetime=start_point.isoformat() + 'Z')
                    x = calendar.create_event(event_pre)
                end_interval -= datetime.timedelta(
                    hours=TIMEZONE)
                post_delta = end_interval - end_point
                if post_delta.seconds != 0:
                    event_post = calendar.create_event_dict(summary="free",
                                                            description=None,
                                                            start_datetime=end_point.isoformat() + 'Z',
                                                            end_datetime=end_interval.isoformat() + 'Z')
                    x = calendar.create_event(event_post)

                event_id = calendar.create_event(event_main)
                sql.insert_event(start_point=start_point,
                                 tgid=telegram_id,
                                 event_id=event_id,
                                 add_date=datetime.datetime.now(),
                                 session=int(call_data[11:13]))


                end_point += datetime.timedelta(hours=TIMEZONE)
                start_point += datetime.timedelta(hours=TIMEZONE)

                allert_text = f"""
◯

Вы были записаны с {start_point} до {end_point}!
NAME: {user_data["name"]} 
DESCRIPTION: {user_data["description"]}

◯
"""

                answerCallbackQuery(callback_query_id=callback_query_id,
                                    text=allert_text, show_alert=True)

                send_message(message=allert_text, chat_id=chat_id)

                editMessageText(message=f"Хотите записаться еще на другое время?",
                                chat_id=chat_id,
                                message_id=message_id,
                                inline_keyboard=json.dumps(start_InlineKeyboardMarkup()))


        else:
            try:
                message_text = data['message']['text']
                chat_id = data['message']['chat']['id']
                telegram_id = data['message']['from']['id']

                if message_text == "/start":
                    sql = SqliteDb()

                    # проверка на наличие записи
                    ss = sql.get_table(tgid=telegram_id)
                    if not ss:
                        sql.insert_table(tgid=telegram_id, chatid=chat_id, name=str(telegram_id), description="без описания", level=1)
                        send_message(message="Вас приветствует бот-помощник Юмы. Напишите свое полное имя. ", chat_id=chat_id)
                    else:
                        send_message(message="Рад снова вас здесь видеть", chat_id=chat_id)
                        send_message(message=f're{message_text}Voo!',
                                     chat_id=chat_id,
                                     inline_keyboard=json.dumps(start_ReplyKeyboardMarkup()))

                if message_text and not message_text.startswith('/'):
                    sql = SqliteDb()
                    ss = sql.get_table(tgid=telegram_id)
                    if ss:
                        if ss[0]["level"] == 1:
                            answ = inadmissible_symbol(message_text)
                            if not answ:
                                sql.update_name(name=message_text, tgid=telegram_id)
                                sql.update_level(level=2, tgid=telegram_id)
                                send_message(message=f'{message_text}, я вас запомнил.',
                                             chat_id=chat_id,
                                             inline_keyboard=json.dumps(start_ReplyKeyboardMarkup()))
                            else:
                                send_message(message=f'Неправильный ввод данных. {answ}', chat_id=chat_id)

                if message_text == "Записаться":
                    send_message(message=FIRST_MESSAGE,
                                 chat_id=chat_id,
                                 inline_keyboard=json.dumps(start_InlineKeyboardMarkup()))

                if message_text == "Отменить запись":
                    sql = SqliteDb()
                    events = sql.get_events(tgid=telegram_id)
                    if events:
                        send_message(message="Нажмите на запись и она удалится",
                                     chat_id=chat_id,
                                     inline_keyboard=json.dumps(events_InlineKeyboardMarkup(events)))

                if message_text == "Написать Юме":
                    send_message(message='@YumaYuma4', chat_id=chat_id)

                if message_text == "Help":
                    send_message(message=HELP_MESSAGE, chat_id=chat_id)
                if message_text == "scheduler8":
                    # для тестирования
                    sensor()
                if message_text == "graphinfinit8":
                    #test
                    sql = SqliteDb()
                    all = sql.select_all()
                    mes = []
                    for i in all:
                        mes.append(dict(i)["tgid"])
                    messa = f"""
hello, graphinfinit
{mes}
"""
                    send_message(message=messa,
                                 chat_id=chat_id)

            except Exception as exc:
                logging.error(f"main {exc.args}")

    else:
        return abort(400)

    return jsonify({"200": "OK"})


if __name__ == "__main__":

    # не пишем лишние логи уровня INFO DEBUG от flask
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    app.run(debug=False)







"""
{'kind': 'calendar#events',
 'etag': '"p32cb3nddlv0eu0g"',
 'summary': 'ApiTest',
 'updated': '2021-03-21T02:46:45.199Z',
 'timeZone': 'Europe/Moscow',
 'accessRole': 'writer',
 'defaultReminders': [],
 'items': 
        [{'kind': 'calendar#event', 'etag': '"3232589552110000"', 'id': '31ch4mpt9cie79c34bcl79psjj', 'status': 'confirmed', 'htmlLink': 'https://www.google.com/calendar/event?eid=MzFjaDRtcHQ5Y2llNzljMzRiY2w3OXBzamogaWcxdDI1cnRhdm10bDZjanEyZzJpbnVycTRAZw', 'created': '2021-03-21T02:46:16.000Z', 'updated': '2021-03-21T02:46:16.055Z', 'summary': 'Событие', 'description': 'Описание', 'creator': {'email': 'graphinfinit@gmail.com'}, 'organizer': {'email': 'ig1t25rtavmtl6cjq2g2inurq4@group.calendar.google.com', 'displayName': 'ApiTest', 'self': True}, 'start': {'dateTime': '2021-03-21T10:30:00+03:00'}, 'end': {'dateTime': '2021-03-21T11:30:00+03:00'}, 'iCalUID': '31ch4mpt9cie79c34bcl79psjj@google.com', 'sequence': 0, 'reminders': {'useDefault': True}, 'eventType': 'default'},
         
         
         {'kind': 'calendar#event', 'etag': '"3232589610398000"', 'id': '0aa35kaclaoq2b8dvbj2jlmo1i', 'status': 'confirmed', 'htmlLink': 'https://www.google.com/calendar/event?eid=MGFhMzVrYWNsYW9xMmI4ZHZiajJqbG1vMWkgaWcxdDI1cnRhdm10bDZjanEyZzJpbnVycTRAZw', 'created': '2021-03-21T02:46:45.000Z', 'updated': '2021-03-21T02:46:45.199Z', 'summary': 'вввввваааууу', 'description': 'выдрааа удрала', 'creator': {'email': 'graphinfinit@gmail.com'}, 'organizer': {'email': 'ig1t25rtavmtl6cjq2g2inurq4@group.calendar.google.com', 'displayName': 'ApiTest', 'self': True}, 'start': {'dateTime': '2021-03-21T14:00:00+03:00'}, 'end': {'dateTime': '2021-03-21T15:00:00+03:00'}, 'iCalUID': '0aa35kaclaoq2b8dvbj2jlmo1i@google.com', 'sequence': 0, 'reminders': {'useDefault': True}, 'eventType': 'default'}]}"""


