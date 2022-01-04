import requests
from trello import TrelloClient
from trello.label import Label
from datetime import date
from datetime import timedelta
import json
import pickle


def get_schedule(start_date, end_date = None):
    headers = {
                "Content-Type": "application/json",
                "charset": "utf-8"
              }
    login = {"password": "ds3m#2nn", "username": "mobil"}
    headers["Authorization"] = f'''Bearer {requests.post("http://api.chsu.ru/api/auth/signin",json=login,headers=headers).json()["data"]}'''
    query = f"/timetable/v1/from/{start_date}/to/{end_date or start_date}/groupId/1705969217226798687/"
    return requests.get('http://api.chsu.ru/api/' + query, headers=headers).json()


def clientinit():
    client = TrelloClient(
        api_key='d42b44c207e03f201f203ec3291e9264',
        api_secret='87c9f356c2317e1647884c915b94b63fea294e599e704d20987bd35513490541',
        token='a28214b9e494796f5e2669dc19403ae9ded9eedb882f728d17564c67c4fb6ced'
        )
    all_boards = client.list_boards()
    board = client.get_board('61330bb18f46e673ee876b15')
    print(board.get_labels())
    return board.all_lists()[2:9] , client


data = date(2021,11,8)
data = data.today()
start_date = data + timedelta(days = 1)
iso_start = start_date.isoformat()
iso_start = iso_start.split('-')
end_date = data + timedelta(days = 6)
iso_end = end_date.isoformat()
iso_end = iso_end.split('-')
schedule = get_schedule(f'{iso_start[2]}.{iso_start[1]}.{iso_start[0]}', f'{iso_end[2]}.{iso_end[1]}.{iso_end[0]}')
trlist, client = clientinit()
weekname = {0: 'Понедельник', 1 : 'Вторник', 2 : 'Среда', 3 : 'Четверг', 4 : 'Пятница', 5 : 'Суббота'}
#dejur = ['Романов Тимур','Сапарбаев Нуратдин','Сатторов Оллоназар','Смирнов Александр','Тимаев Никита','Титов Андрей',
#'Ярашбаев Алишер','Абдукодиров Жавохир','Варварский Ярослав','Варганов Никита','Гринько Дмитрий','Кенжабаев Адхам','Мирзалиев Рахмали']
#ddej = {}
with open('dejdata.pickle', 'rb') as f:
    dejur,ddej = pickle.load(f)
for i in range(6):
    i_day = start_date + timedelta(days = i)
    i_weekday = i_day.weekday()
    if i_weekday == 6:
        continue
    i_list = trlist[i_weekday]
    i_list.archive_all_cards()
    i_list.set_name(f'''{weekname[i_weekday]} / {i_day.day}.{i_day.month}.{i_day.year}''')
    if i_day in ddej:
        i_list.add_card(f'Дежурство {ddej[i_day]}')
    else:
        dejurnii = dejur.pop(0)
        dejur.append(dejurnii)
        i_list.add_card(f'Дежурство {dejurnii}')
        ddej[i_day] = dejurnii
dejdata = [dejur,ddej]

with open('dejdata.pickle','wb') as f:
    pickle.dump(dejdata, f)
labels = [
Label(client,'61330bb20b749303b1cd9f82', 'Информатика'),
Label(client,'61330bb4c2449a1d16546b0b', 'Математика'),
Label(client,'6133415644c7b83500e78a07', 'Другое'),
Label(client,'61330bb4935ee18c23bb213d', 'Гуманитарные науки'),
Label(client,'61330bb36b923b6d688756b0', '123')]
labels = {
'Системное и прикладное программное обеспечение' :labels[0],
'Математический анализ' : labels[1],
'Алгоритмы и алгоритмические языки': labels[0],
'Физическая культура и спорт (элективная дисциплина)': labels[4],
'Алгебра и геометрия' : labels[1],
'История': labels[3],
'Математическая логика' : labels[1],
'Иностранный язык (англ)': labels[3],
'Иностранный язык (англ с "0")': labels[3],
'Другое': labels[2]
}
for urok in schedule:
    u_day = urok['dateEvent'].split('.')
    u_day = date(int(u_day[2]),int(u_day[1]),int(u_day[0]))
    u_list = trlist[u_day.weekday()]
    card = f'''{urok['startTime']} - {urok['endTime']} {urok['abbrlessontype']} {urok['discipline']['title']} '''
    if urok['online'] == 0:
        card += f'''{urok['auditory']['title']} / {urok['build']['title']}'''
    else:
        card += 'Онлайн'
    if urok['discipline']['title'] in labels:
        label = labels[urok['discipline']['title']]
    else:
        label = labels['Другое']
    u_list.add_card(card, labels = [label])
