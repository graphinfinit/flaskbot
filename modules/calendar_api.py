from __future__ import print_function

"""
from __future__ import print_function
позволит вам использовать print в качестве функции:
print('# of entries', len(dictionary), file=sys.stderr)
"""
import datetime
from dateutil.relativedelta import relativedelta
import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build

from modules.settings import DELTA


import logging


SCOPES = ['https://www.googleapis.com/auth/calendar']
calendarId = 'ig1t25rtavmtl6cjq2g2inurq4@group.calendar.google.com'

#calendarId = 'speav93bqavpes0b4ao9p479e4@group.calendar.google.com'
SERVICE_ACCOUNT_FILE = 'modules/project01calendar-9a4134fa5364.json'

#SERVICE_ACCOUNT_FILE = 'modules/telegrambot-309019-007b231e22c3.json'



class GoogleCalendar(object):

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    # создание словаря с информацией о событии
    @staticmethod
    def create_event_dict(summary="",
                          description="",
                          start_datetime="2021-03-21T03:00:00+03:00",
                          end_datetime='2021-03-21T05:30:00+03:00'):
        event = {
            'summary': f'{summary}',
            'description': f'{description}',
            'start': {
                'dateTime': start_datetime,
            },
            'end': {
                'dateTime': end_datetime,
            }
        }
        return event

    # создание события в календаре
    def create_event(self, event):
        e = self.service.events().insert(calendarId=calendarId,
                                         body=event).execute()
        logging.info(f"Event created:{e.get('id')}  ({datetime.datetime.today()})")
        event_id = e.get('id')
        return event_id

    def delete_event(self, eventId):
        e = self.service.events().delete(calendarId=calendarId, eventId=eventId).execute()
        logging.info(f"Event deleted")

    def patch_event(self, eventId):
        e = self.service.events().patch(calendarId=calendarId,
                                        eventId=eventId,
                                        body={"summary": "free",
                                              "colorId": "2",
                                              "description": "Нло похитило запись. Теперь это свободное время"}).execute()




    # вывод  событий
    def get_events_list(self, delta=DELTA, timeMin=None, timeMax=None):
        if delta:
            # если задана дельта то находим все события с настоящего момента до (DELTA)дней спустя
            timeMin = datetime.datetime.utcnow().isoformat() + 'Z'
            month_plus = datetime.datetime.today() + relativedelta(days=delta)
            timeMax = month_plus.isoformat('T') + "Z"

        events_result = self.service.events().list(calendarId=calendarId,
                                                   timeMin=timeMin,
                                                   timeMax=timeMax,
                                                   q='free',
                                                   singleEvents=True,
                                                   orderBy='startTime').execute()
        return events_result



