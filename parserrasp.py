import requests
from datetime import date
from datetime import timedelta
import googlecalendar
import trello_schedule
import pickle


def get_schedule(data,start_date, end_date = None):
    headers = {
                "Content-Type": "application/json",
                "charset": "utf-8"
              }
    login = {"password": data['chsu_password'], "username": data['chsu_login']}
    headers["Authorization"] = f'''Bearer {requests.post("http://api.chsu.ru/api/auth/signin",json=login,headers=headers).json()["data"]}'''
    query = f"/timetable/v1/from/{start_date}/to/{end_date or start_date}/groupId/{data['groupId']}/"
    return requests.get('http://api.chsu.ru/api/' + query, headers=headers).json()

def get_list_groups(data):
    headers = {
                "Content-Type": "application/json",
                "charset": "utf-8"
              }
    login = {"password": data['chsu_password'], "username": data['chsu_login']}
    headers["Authorization"] = f'''Bearer {requests.post("http://api.chsu.ru/api/auth/signin",json=login,headers=headers).json()["data"]}'''
    return requests.get('http://api.chsu.ru/api/group/v1', headers=headers).json()

def trello_update(data):
    start_date = date.today()
    end_date = start_date + timedelta(days = 5)
    schedule = get_schedule(data,start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
    trello = trello_schedule.Trelloschedule(data)
    trello.clear()
    if data['att_on']:
        trello.add_attendants()
    trello.add_schedule(schedule)

def calendar_update(data):
    start_date = date.today()
    end_date = start_date + timedelta(days = data['cal_update_len'])
    schedule = get_schedule(data,start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))
    calendar = googlecalendar.GoogleCalendar(data)
    calendar.clear()
    if data['att_on']:
        calendar.add_attendants()
    calendar.add_schedule(schedule)

def update_all(data):
    if 'trello' in data and data['trello'] :
        trello_update(data)
    if 'calendar' in data and data['calendar']:
        calendar_update(data)

if __name__ == '__main__':

    with open('data.pickle', 'rb') as f:
        data = pickle.load(f)

    update_all(data)
