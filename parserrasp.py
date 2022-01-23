import requests
from datetime import date
from datetime import timedelta
import googlecalendar
import trello_schedule
import pickle

with open('data.pickle', 'rb') as f:
    data = pickle.load(f)

def get_schedule(data,start_date, end_date = None):
    headers = {
                "Content-Type": "application/json",
                "charset": "utf-8"
              }
    login = {"password": data['chsu_password'], "username": data['chsu_login']}
    headers["Authorization"] = f'''Bearer {requests.post("http://api.chsu.ru/api/auth/signin",json=login,headers=headers).json()["data"]}'''
    query = f"/timetable/v1/from/{start_date}/to/{end_date or start_date}/groupId/{data['groupId']}/"
    return requests.get('http://api.chsu.ru/api/' + query, headers=headers).json()

def trello_update(data):
    start_date = date.today()
    end_date = start_date + timedelta(days = 7)
    schedule = get_schedule(data,start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
    trello = trello_schedule.Trelloschedule(data)
    trello.clear()
    if data['att_on']:
        trello.add_attendants()
    trello.add_schedule(schedule)

def calendar_update(data):
    start_date = date.today()
    end_date = start_date + timedelta(days = 30)
    schedule = get_schedule(data,start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
    calendar = googlecalendar.GoogleCalendar(data)
    calendar.clear()
    if data['att_on']:
        calendar.add_attendants()
    calendar.add_schedule(schedule)
if __name__ == '__main__':
    if data['trello'] :
        print('Обновляю трелло')
        trello_update(data)
    if data['calendar']:
        print('Обновляю календарь')
        calendar_update(data)
