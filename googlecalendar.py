import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

class GoogleCalendar():

    def __init__(self,calendarId,account_file):
        credentials = service_account.Credentials.from_service_account_file(account_file, scopes=['https://www.googleapis.com/auth/calendar'])
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        self.calendarId = calendarId

    def clear_events(self):
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(calendarId=self.calendarId, timeMin=now,
                                              singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        for event in events:
            self.service.events().delete(calendarId=self.calendarId, eventId=event['id']).execute()

    # создание словаря с информацией о событии
    def create_event_dict_from_chsuapi(self,urok):
        name = f'''{urok['abbrlessontype']} {urok['discipline']['title']} '''
        if urok['online'] == 0:
            name += f'''{urok['auditory']['title']} / {urok['build']['title']}'''
        else:
            name += 'Онлайн'
        day = urok['dateEvent'].split('.')
        day = f'''{day[-1]}-{day[-2]}-{day[-3]}'''
        event = {
            'summary': name,
            'description': '',
            'start': {
                'dateTime': f'''{day}T{urok['startTime']}:00+03:00''',
            },
            'end': {
                'dateTime': f'''{day}T{urok['endTime']}:00+03:00''',
            }
        }
        return event

    # создание события в календаре
    def create_event(self, urok):
        event = self.create_event_dict_from_chsuapi(urok)
        self.service.events().insert(calendarId=self.calendarId,body=event).execute()

    def add_attendant(self,attendant,date):
        event = {
            'summary': 'Дежурный - ' + attendant,
            'description': '',
            'start': {
                'date': date,
            },
            'end': {
                'date': date,
            }
        }
        self.service.events().insert(calendarId=self.calendarId,body=event).execute()
