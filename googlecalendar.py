import googleapiclient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import date
from datetime import timedelta
from datetime import datetime

class GoogleCalendar():

    def __init__(self,data):
        credentials = service_account.Credentials.from_service_account_file(data['account_file'], scopes=['https://www.googleapis.com/auth/calendar'])
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
        self.ids = data['calendar']
        self.dejur = data['dejur']
        self.multi_cal = data['multi_cal']

    def clear(self):
        for cal in self.ids:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(calendarId=self.ids[cal], timeMin=now,
                                                       singleEvents=True,
                                                       orderBy='startTime').execute()
            events = events_result.get('items', [])
            for event in events:
                self.service.events().delete(calendarId=self.ids[cal], eventId=event['id']).execute()

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

    def create_attendant_dict(self,attendant,date):
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
        return event

    # создание события в календаре
    def add_schedule(self, schedule):
        for urok in schedule:
            event = self.create_event_dict_from_chsuapi(urok)
            if self.multi_cal:
                self.service.events().insert(calendarId=self.ids[urok['abbrlessontype']],body=event).execute()
            else:
                self.service.events().insert(calendarId=self.ids['д'],body=event).execute()

    def add_attendants(self):
        start_date = date.today()
        delt_date = date(2021,11,8)
        for i in range (30):
            i_day = start_date + timedelta(days = i)
            if i_day.weekday() == 6:
                continue
            delta = i_day - delt_date
            attendant = self.dejur[(delta.days % len(self.dejur))-delta.days//7 % len(self.dejur)]
            event = self.create_attendant_dict(attendant,i_day.isoformat())
            self.service.events().insert(calendarId=self.ids['д'],body=event).execute()
