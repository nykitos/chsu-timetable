from trello import TrelloClient
from trello.label import Label
from datetime import timedelta
from datetime import date


class Trelloschedule:

    def __init__(self,data):
        self.client = TrelloClient(
            api_key = data['trello_key'],
            api_secret = data['trello_secret'],
            token = data['trello_token']
            )
        self.board = self.client.get_board(data['trello_board'])
        self.lists = self.board.open_lists()[data['trello_startlist'] : data['trello_startlist']+7]
        self.att_on =  data['att_on']
        if self.att_on:
            self.attendants = data['attendants']
        self.labels_on = data['labels_on']
        if self.labels_on:
            self.labels = data['labels']

    def clear(self):
        delt_date = date(2021,11,8)
        start_date = delt_date.today()
        weekname = {0: 'Понедельник', 1 : 'Вторник', 2 : 'Среда',
        3 : 'Четверг',4 : 'Пятница', 5 : 'Суббота'}
        for i in range(7):
            i_day = start_date + timedelta(days = i)
            i_weekday = i_day.weekday()
            if i_weekday == 6:
                continue
            i_list = self.lists[i_weekday]
            i_list.archive_all_cards()
            i_list.set_name(f'{weekname[i_weekday]} / {i_day.day}.{i_day.month}.{i_day.year}')

    def add_attendants(self):
        start_date = date.today()
        delt_date = date(2021,11,8)
        for i in range(7):
            i_day = start_date + timedelta(days = i)
            i_weekday = i_day.weekday()
            if i_weekday == 6:
                continue
            i_list = self.lists[i_weekday]
            delta = i_day - delt_date
            i_list.add_card(f'Дежурство {self.attendants[(delta.days % len(self.attendants))-delta.days//7 % len(self.attendants)]}')

    def add_schedule(self,schedule):
        for urok in schedule:
            u_day = urok['dateEvent'].split('.')
            u_day = date(int(u_day[2]),int(u_day[1]),int(u_day[0]))
            u_list = self.lists[u_day.weekday()]
            card = f'''{urok['startTime']} - {urok['endTime']} {urok['abbrlessontype']} {urok['discipline']['title']} '''
            if urok['online'] == 0:
                card += f'''{urok['auditory']['title']} / {urok['build']['title']}'''
            else:
                card += 'Онлайн'
            if self.labels_on:
                u_list.add_card(card,
                labels = [Label(self.client,self.labels[urok['abbrlessontype']], '123')])
            else:
                u_list.add_card(card)
