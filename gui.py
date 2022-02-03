import PySimpleGUI as sg
from parserrasp import *
import pickle
from trello import TrelloClient
import os
import sys
from webbrowser import open_new_tab as open_url
import googleapiclient
from google.oauth2 import service_account
from googlecalendar import GoogleCalendar
from datetime import datetime
from psgtray import SystemTray
from time import sleep

def save_data():
    with open('data.pickle', 'wb') as f:
        pickle.dump(data, f)

def check_date_loop():
    while True:
        if date.today() >= data['last_update'] + timedelta(data['update_range']):
            data['last_update'] = date.today()
            save_data()
            return
        else:
            sleep(60*30)

def tr_key_set():
    layout = [  [sg.Text('Установка ключей')],
                [sg.Text('Для того что бы в автоматическом режиме обновлять доску, тебе необходимо ввести свои ключи разработчика'+
                         '\nИх можно получить вот здесь: https://trello.com/app-key'+
                         '\nКлюч - вверху страницы, Секрет - внизу, Чтобы получить токен необходимо перейти по ссылке в верхней части страницы')],
                [sg.Text('Key'), sg.Input(key = '-KEY-')],
                [sg.Text('Secret'), sg.Input(key = '-SECRET-')],
                [sg.Text('Token'), sg.Input(key = '-TOKEN-')],
                [sg.Button('Далее'), sg.Button('Открыть ссылку')]  ]
    window = sg.Window('Устаовка ключей', layout,enable_close_attempted_event = True, finalize = True)
    if 'trello_key' in data:
        window['-KEY-'].update(value = data['trello_key'])
    if 'trello_secret' in data:
        window['-SECRET-'].update(value = data['trello_secret'])
    if 'trello_token' in data:
        window['-TOKEN-'].update(value = data['trello_token'])
    while True:
        event, values = window.read()
        if event == 'Далее':
            try:
                client = TrelloClient(
                    api_key = values['-KEY-'],
                    api_secret = values['-SECRET-'],
                    token = values['-TOKEN-'])
                list_boards = client.list_boards()
                data['trello_key'] = values['-KEY-']
                data['trello_secret'] = values['-SECRET-']
                data['trello_token'] = values['-TOKEN-']
                window.close()
                return 'tr_board_chouse'
            except:
                sg.popup('Неверные данные')
        elif event == 'Открыть ссылку':
            open_url(r'https://trello.com/app-key')
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def tr_board_chouse():
    client = TrelloClient(
        api_key = data['trello_key'],
        api_secret = data['trello_secret'],
        token = data['trello_token'])
    list_boards = client.list_boards()
    name_boards = [i.name for i in list_boards]
    layout =[ [sg.Text('Выбери доску на которую будет заполняться расписание')],
              [sg.Combo(name_boards, key = '-BOARD-', size = (30,None))],
              [sg.Button('Далее'),sg.Button('Обновить список досок')] ]
    window = sg.Window( 'Выбор доски',layout = layout,enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Обновить список досок':
            list_boards = client.list_boards()
            name_boards = [i.name for i in list_boards]
            window['-BOARD-'].update(values = name_boards)
        elif event == 'Далее':
            if values['-BOARD-'] not in name_boards:
                sg.popup('Неверное значение')
                continue
            for board in list_boards:
                if values['-BOARD-'] == board.name:
                    break
            data['trello_board'] = board.id
            window.close()
            return 'tr_column_chouse'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def tr_column_chouse():
    layout = [  [sg.Text('Выбери список с которого будет начинаться расписание'+
                         '\nПервую колонку можно оставить например под дз'+
                         '\nНомера колонок считаются слева от 1')],
                [sg.Input(key = '-COLUMN-')],
                [sg.Button('Далее')]  ]
    window = sg.Window('Выбор номера колонки',layout = layout,enable_close_attempted_event = True, finalize = True)
    if 'trello_startlist' in data:
        window['-COLUMN-'].update(value = data['trello_startlist'])
    while True:
        event, values = window.read()
        if event == 'Далее':
            try:
                if int(values['-COLUMN-'])<1:
                    sg.Popup('Отрицательных колонок не существует.')
                    continue
            except:
                sg.Popup('Неверное значение')
                continue
            data['trello_startlist'] = int(values['-COLUMN-'])- 1
            client = TrelloClient(
                api_key = data['trello_key'],
                api_secret = data['trello_secret'],
                token = data['trello_token'])
            board = client.get_board(data['trello_board'])
            lists = board.open_lists()
            if len(lists) < data['trello_startlist']+6:
                for i in range(data['trello_startlist']+6 - len(lists)):
                    board.add_list(str(i),pos = 'bottom')
                    window.refresh()
            window.close()
            if 'labels_on' not in data:
                if sg.popup_yes_no('К каждой карточке на трелло можно добавлять цветную метку в зависимости от типа занятия, лекции, практики и тд.'+
                                   '\nВы хотите настроить метки?') == 'Yes':
                    return 'tr_labels_chouse'
                else:
                    data['labels_on'] = False
                    data['trello'] = True
                    save_data()
                    return 'set_groupId'
            else:
                return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def tr_labels_chouse():
    client = TrelloClient(
        api_key = data['trello_key'],
        api_secret = data['trello_secret'],
        token = data['trello_token'])
    board = client.get_board(data['trello_board'])
    labels = board.get_labels()
    labels_name = [label.name for label in labels]
    layout = [  [sg.Text('Выберите метки, их необходимо создать в Трелло\nВ правом верхнем углу меню > Ещё > метки')],
                [sg.Text('Лекции'), sg.Combo(labels_name, key = 'л', size = (30,None))],
                [sg.Text('Практики'), sg.Combo(labels_name, key ='п', size = (30,None))],
                [sg.Text('Лабораторные'), sg.Combo(labels_name, key ='лб', size = (30,None))],
                [sg.Text('Зачеты'), sg.Combo(labels_name, key ='з', size = (30,None))],
                [sg.Text('Экзамены'), sg.Combo(labels_name, key ='э', size = (30,None))],
                [sg.Button('Далее'), sg.Button('Обновить список')]  ]
    window = sg.Window('Выбор меток',layout = layout,enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Обновить список':
            labels = board.get_labels()
            labels_name = [label.name for label in labels]
            for i in ['л', 'п', 'лб', 'з', 'э']:
                window[i].update(values = labels_name)
                window.refresh()
        elif event == 'Далее':
            labels_dict = {}
            for i in ['л', 'п', 'лб', 'з', 'э']:
                for label in labels:
                    if label.name == i:
                        break
                labels_dict[i] = label.id
            data['labels'] = labels_dict
            data['labels_on'] = True
            data['trello'] = True
            save_data()
            window.close()
            if 'groupId' not in data:
                return 'set_groupId'
            else:
                return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def cal_set_file():
    layout = [  [sg.Text('Создание файла')],
                [sg.Text('Для того что бы в автоматическом режиме обновлять календарь необходимо создать сервисный аккаунт google'+
                         '\nЭто делается здесь: https://console.cloud.google.com/apis/credentials'+
                         '\nСначала необходимо согласится с политикой Google и создать проект'+
                         '\nДалее с помощью + вверху создать сервисный аккаунт'+
                         '\nДалее значок карандаша рядом с появившемся аккаунтом > keys > add key > create new key > JSON > create')],
                [sg.Text('Прикрепите скачанный файл, советую держать его в папке с программой.')],
                [sg.Input(), sg.FileBrowse()],
                [sg.Text('ВАЖНО!\nПерейдите по 2 ссылке и включите апи календаря для проекта')],
                [sg.Button('Далее'),sg.Button('Перейти по 1 ссылке'),sg.Button('Перейти по 2 ссылке')]  ]
    window = sg.Window('Создание файла',layout = layout,enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Перейти по 1 ссылке':
            open_url(r'https://console.cloud.google.com/apis/credentials')
        elif event == 'Перейти по 2 ссылке':
            open_url(r'https://console.cloud.google.com/apis/library/calendar-json.googleapis.com')
        elif event == 'Далее':
            try:
                credentials = service_account.Credentials.from_service_account_file(values[0], scopes=['https://www.googleapis.com/auth/calendar'])
                service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
                data['account_file'] = values[0]
                window.close()
                return 'update_len'
            except:
                sg.popup('Неверные данные')
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def update_len():
    layout = [  [sg.Text('Выбор временного отрезка')],
                [sg.Text('На календарь можно добавить неограниченно много расписания,'+
                        '\nно чем больше дней нужно обновить тем дольше будет выполняться программа')],
                [sg.Text('На сколько дней вы хотите заглядывать в будущее?')],
                [sg.Input(default_text  = data['cal_update_len'] if 'cal_update_len' in data else 30)],
                [sg.Button('Далее')] ]
    window = sg.Window('Выбор отрезка',layout = layout,enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Далее':
            try:
                val = int(values[0])
                assert val > 1
            except:
                sg.popup('Неверные данные')
                continue
            data['cal_update_len'] = val
            window.close()
            return 'razvilka'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def razvilka():
    layout = [  [sg.Text('Приветствую тебя, путник. Ты пришел к развилке судеб, сейчас от твоего выбора зависит будущее всего мира....'+
                         '\nКхм.... Кажется это не тот текст, А нашел!')],
                [sg.Text('Так как на календаре цвет событий видит только тот кто создает событие, для расписания есть два варианта:')],
                [sg.Text('1 Вариант - Создать 1 календарь что бы править всеми, черт опять не тот текст.'+
                         '\nНа нем выкладывать все расписание, но без доступа к разделению занятий по цветам')],
                [sg.Text('2 Вариант - Создать несколько календарей под каждый тип занятия'+
                         '\nТогда каждый сможет настроить цвета под себя и будет возможность быстрой сортировки')],
                [sg.Button('1 Вариант'),sg.Button('2 Вариант')]  ]
    window = sg.Window('Развилка судеб',layout = layout,enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == ('1 Вариант'):
            window.close()
            return 'first_var'
        elif event == ('2 Вариант'):
            window.close()
            return 'second_var'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def first_var():
    layout = [  [sg.Text('Настройка календаря')],
                [sg.Text('Введите адрес календаря на котором будет выкладываться расписание,'+
                         '\nДля начала его надо создать в левом меню, '+
                         '\nДалее необходимо предоставить доступ сервисному аккаунту для изменения календаря.'+
                         '\nПараметры календаря > Доступ для отдельных пользователей > Добавить пользователей > Вставте email аккаунта > предоставте доступ к редактированию'+
                         '\nИдентификатор календаря находится внизу окна настроек'+
                         '\nУчтите что про каждом обновлении все данные из календаря будут стерты')],
                [sg.Text('Введите идентификатор календаря')],
                [sg.Input(key = '-CALENDAR-')],
                [sg.Button('Далее')]  ]
    window = sg.Window('Настройка календаря',layout = layout,enable_close_attempted_event = True, finalize = True)
    if 'calendars' in data:
        window['-CALENDAR-'].update(value = data['calendars']['д'])
    while True:
        event, values = window.read()
        if event == 'Далее':
            try:
                credentials = service_account.Credentials.from_service_account_file(data['account_file'],
                              scopes=['https://www.googleapis.com/auth/calendar'])
                service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
                now = datetime.utcnow().isoformat() + 'Z'
                events_result = service.events().list(calendarId=values['-CALENDAR-'], timeMin=now,
                                                           singleEvents=True,
                                                           orderBy='startTime').execute()
                events = events_result.get('items', [])
                data['calendars'] = {'д': values['-CALENDAR-']}
                data['multi_cal'] = False
                data['calendar'] = True
                save_data()
                window.close()
                if 'groupId' not in data:
                    return 'set_groupId'
                else:
                    return 'menu'
            except:
                sg.popup('Неверные данные')
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == "Yes":
            window.close()
            return 'exit'

def second_var():
    layout = [  [sg.Text('Настройка клендарей')],
                [sg.Text('Введите адрес календарей на которых будет выкладываться расписание,'+
                         '\nДля начала их надо создать в левом меню, '+
                         '\nДалее необходимо предоставить доступ сервисному аккаунту для изменения календаря.'+
                         '\nПараметры календаря > Доступ для отдельных пользователей > Добавить пользователей > Вставте email аккаунта > предоставте доступ к редактированию'+
                         '\nИдентификатор календаря находится внизу окна настроек'+
                         '\nУчтите что про каждом обновлении все данные из календаря будут стерты'+
                         '\nПоле календаря дежурств можете оставить пустым, если не собираетесь в будущем настривать дежурства')],
                [sg.Text('Лекции'),sg.Input(key = 'л')],
                [sg.Text('Практики'),sg.Input(key = 'п')],
                [sg.Text('Лабораторные'),sg.Input(key = 'лб')],
                [sg.Text('Зачеты'),sg.Input(key = 'з')],
                [sg.Text('Экзамены'),sg.Input(key = 'э')],
                [sg.Text('Дежурства'),sg.Input(key = 'д')],
                [sg.Button('Далее')]  ]
    window = sg.Window('Настройка календарей', layout = layout, enable_close_attempted_event = True, finalize = True)
    if 'calendars' in data:
        calendars = data['calendars']
        for i in calendars:
            window[i].update(value = calendars['д'])
    while True:
        event, values = window.read()
        if event == 'Далее':
            try:
                credentials = service_account.Credentials.from_service_account_file(data['account_file'],
                              scopes=['https://www.googleapis.com/auth/calendar'])
                service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
                now = datetime.utcnow().isoformat() + 'Z'
                if values['д'] == '':
                    del values['д']
                for i in values:
                    window.refresh()
                    cal = values[i]
                    events_result = service.events().list(calendarId=cal, timeMin=now,
                                                            singleEvents=True,
                                                            orderBy='startTime').execute()
                    events = events_result.get('items', [])
                data['multi_cal'] = True
                data['calendars'] = values
                data['calendar'] = True
                save_data()
                window.close()
                if 'groupId' not in data:
                    return 'set_groupId'
                else:
                    return 'menu'
            except:
                sg.popup(f'Неверные данные в календаре {i}')
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def set_groupId():
    groups = get_list_groups(data)
    groups_name = []
    groups_id = {}
    for group in groups:
        groups_name.append(group['title'])
        groups_id[group['title']] = group['id']
    layout = [  [sg.Text('Настройка группы')],
                [sg.Text('Выберите свою группу')],
                [sg.Combo(groups_name)],
                [sg.Button('Далее')]  ]
    window = sg.Window('Выбор группы', layout, enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Далее':
            if values[0] in groups_id:
                data['groupId'] = groups_id[values[0]]
                window.close()
                if 'att_on' not in data and sg.popup_yes_no('Вы хотите настроить список дежурных? Они будут назначаться на каждый рабочий день') == 'Yes':
                    return 'set_attendant_list'
                else:
                    data['att_on'] = False
                    save_data()
                    return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def set_attendant_list():
    layout = [  [sg.Text('Настройка списка группы')],
                [sg.Text('Введите список дежурных, каждый человек с новой строки')],
                [sg.Multiline(size = (40,30),key = '-ATTENDANTS-')],
                [sg.Button('Далее'),sg.Button('Выключить дежурных')]  ]
    window = sg.Window('Расписание', layout, enable_close_attempted_event = True, finalize = True)
    if 'attendants' in data:
        window['-ATTENDANTS-'].update(value = '\n'.join(data['attendants']))
    while True:
        event, values = window.read()
        if event == 'Далее':
            attendants = values['-ATTENDANTS-'].split('\n')
            if len(attendants) == 0:
                sg.popup('Введите хотябы 1 человека')
                continue
            data['attendants'] = attendants
            data['att_on'] = True
            save_data()
            window.close()
            return 'menu'
        elif event == 'Выключить дежурных':
            data['att_on'] = False
            save_data()
            window.close()
            return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def auto_update_menu():
    layout = [  [sg.Text('Настройка автообновления')],
                [sg.Text('Вы хотите добавить автобновление расписания?'+
                         '\nПриложение будет добавленно в авто загрузку,и будет автоматически обновлять расписание если прошло указанное количество дней.'+
                         '\nОбновление происходит только если прошло указанное количество дней и приложение открыто на главном меню или скрыто в трей')],
                [sg.Text('Если вы хотите настроить автообновление введите через сколько дней программа будет обновлять расписание, иначе нажмите назад.')],
                [sg.Input()]  ]
    if 'auto_update' in data:
        layout.append([sg.Button('Далее'), sg.Button('Выключить автообновление' if data['auto_update'] else 'Включить автообновление', key = '-SWITCH-'),sg.Button('Назад')])
    else:
        layout.append([sg.Button('Далее'), sg.Button('Назад')])
    window = sg.Window('Настройка автообновления', layout, enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Далее':
            try:
                assert int(values[0]) > 0
            except:
                sg.popup('Неверные данные')
                continue
            data['auto_update'] = True
            data['last_update'] = date.today()
            data['update_range'] = int(values[0])
            save_data()
            file = sys.argv[0]
            user_path = os.path.expanduser('~')
            file_path = f"{user_path}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\CHSU-timetable.bat"
            if not os.path.exists(file_path):
                with open(file_path, "w+") as bat_file:
                    bat_file.write(f'@echo off\n@chcp 1251\nstart {file} -h')
            window.close()
            return 'menu'
        elif event == 'Назад':
            window.close()
            return 'menu'
        elif event == '-SWITCH-':
            data['auto_update'] = False if data['auto_update'] else True
            window['-SWITCH-'].update(text = 'Выключить автообновление' if data['auto_update'] else 'Включить автообновление')
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def trello_menu():
    layout = [  [sg.Text('Настройка trello')],
                [sg.Button('Ключи'),sg.Button('Доска'),sg.Button('Номер колонки'),sg.Button('Метки'),
                 sg.Button('Выключить трелло' if data['trello'] else 'Включить трелло', key = '-SWITCH-'),sg.Button('Назад')]  ]
    window = sg.Window('Настройка Trello', layout, enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Ключи':
            window.hide()
            win = tr_key_set()
            save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Доска':
            window.hide()
            win = tr_board_chouse()
            save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Номер колонки':
            window.hide()
            win = tr_column_chouse()
            save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Метки':
            window.hide()
            win = tr_labels_chouse()
            save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == '-SWITCH-':
            data['trello'] = False if data['trello'] else True
            window['-SWITCH-'].update(text = 'Выключить трелло' if data['trello'] else 'Включить трелло')
            save_data()
        elif event == 'Назад':
            window.close()
            return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def calendar_menu():
    layout = [  [sg.Text('Настройка Google Calendar')],
                [sg.Button('Ключ-файл'),sg.Button('Временной промежуток'),sg.Button('Настройка календарей'),
                sg.Button('Выключить календарь' if data['calendar'] else 'Включить календарь', key = '-SWITCH-'),sg.Button('Назад')]  ]
    window = sg.Window('Настройка Trello', layout, enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Ключ-файл':
            window.hide()
            win = cal_set_file()
            save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Настройка календарей':
            window.hide()
            win = razvilka()
            if win == 'first_var':
                win = first_var()
                save_data()
            elif win == 'second_var':
                win = second_var()
                save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Временной промежуток':
            window.hide()
            win = update_len()
            save_data()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == '-SWITCH-':
            data['calendar'] = False if data['calendar'] else True
            window['-SWITCH-'].update(text = 'Выключить календарь' if data['calendar'] else 'Включить календарь')
            save_data()
        elif event == 'Назад':
            window.close()
            return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def group_menu():
    layout = [  [sg.Text('Настройка группы')],
                [sg.Button('Номер группы'),sg.Button('Список дежурных'),sg.Button('Назад')]  ]
    window = sg.Window('Настройка Trello', layout, enable_close_attempted_event = True, finalize = True)
    while True:
        event, values = window.read()
        if event == 'Номер группы':
            window.hide()
            win = set_groupId()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Список дежурных':
            window.hide()
            win = set_attendant_list()
            if win == 'exit':
                window.close()
                return 'exit'
            window.un_hide()
        elif event == 'Назад':
            window.close()
            return 'menu'
        elif event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT and sg.popup_yes_no('Вы уверены что хотите закрыть приложение?') == 'Yes':
            window.close()
            return 'exit'

def menu(hide = False):
    menu = ['', ['Обновить расписание','Открыть окно', '---', 'Выход']]
    layout = [  [sg.Text('Приветствую тебя кто бы ты ни был')],
                [sg.Text('Это приложение позволяет в автоматическом режиме добавлять расписание чгу на доску в Trello и GoogleCalendar')],
                [sg.Text('Выберите что вы хотите создать/настроить:')],
                [sg.Button('Trello'), sg.Button('GoogleCalendar'), sg.Button('Группа'), sg.Button('Автообновление'), sg.Button('Обновить расписание', key = '-UPDATE-'), sg.Button('Скрыть')] ]
    window = sg.Window('Расписание', layout, finalize = True)
    tray = SystemTray(menu, single_click_events=False, window=window, tooltip='Расписание ЧГУ', icon=sg.DEFAULT_BASE64_ICON)
    if hide:
        window.hide()
    else:
        tray.hide_icon()
    if 'auto_update' in data and data['auto_update']:
        window.perform_long_operation(check_date_loop,'Обновить расписание')
    while True:
        event, values = window.read()
        if event == tray.key:
            event = values[event]
        if event in (sg.WIN_CLOSED, 'Выход'):
            tray.close()
            window.close()
            return 'exit'
        elif event in (sg.EVENT_SYSTEM_TRAY_ICON_DOUBLE_CLICKED,'Открыть окно'):
            hide = False
            tray.hide_icon()
            window.un_hide()
            window.bring_to_front()
        elif event == 'Trello':
            if 'trello' not in data:
                window.close()
                return 'tr_key_set'
            else:
                window.close()
                return 'trello_menu'
        elif event == 'GoogleCalendar':
            if 'calendars' not in data:
                window.close()
                return 'cal_set_file'
            else:
                window.close()
                return 'calendar_menu'
        elif  event == 'Группа':
            if 'groupId'not in data:
                window.close()
                return 'set_groupId'
            else:
                window.close()
                return 'group_menu'
        elif event == 'Скрыть':
            hide = True
            window.hide()
            tray.show_icon()
        elif event == '-UPDATE-':
            window.perform_long_operation(lambda: update_all(data), '-OPERATION DONE-')
            window['-UPDATE-'].update(text = 'Обновляю расписание')
        elif event == 'Автообновление':
            window.close()
            return 'auto_update_menu'
        elif event == '-OPERATION DONE-':
            if hide:
                tray.show_message('Расписание', 'Расписание обновленно')
            else:
                sg.popup('Расписание обновленно')
            window['-UPDATE-'].update(text = 'Обновить расписание')
            if 'auto_update' in data and data['auto_update']:
                data['last_update'] = date.today()
                window.perform_long_operation(check_date_loop,'Обновить расписание')

def main(win):
    sg.theme('DarkAmber')
    while True:
        if win == 'menu':
            win = menu()
        elif win == 'hide_menu':
            win = menu(hide=True)
        elif win == 'exit':
            break
        elif win == 'tr_key_set':
            win = tr_key_set()
        elif win == 'tr_board_chouse':
            win = tr_board_chouse()
        elif win == 'tr_column_chouse':
            win = tr_column_chouse()
        elif win == 'tr_labels_chouse':
            win = tr_labels_chouse()
        elif win == 'cal_set_file':
            win = cal_set_file()
        elif win == 'update_len':
            win = update_len()
        elif win == 'razvilka':
            win = razvilka()
        elif win == 'first_var':
            win = first_var()
        elif win == 'second_var':
            win = second_var()
        elif win == 'set_groupId':
            win = set_groupId()
        elif win == 'set_attendant_list':
            win = set_attendant_list()
        elif win == 'group_menu':
            win = group_menu()
        elif win == 'calendar_menu':
            win = calendar_menu()
        elif win == 'trello_menu':
            win = trello_menu()
        elif win == 'auto_update_menu':
            win = auto_update_menu()
        else:
            sg.popup('Ошибка при переходе между окнами')
            break

if __name__ == '__main__':
    if 'data.pickle' in os.listdir():
        f =  open('data.pickle', 'rb')
        data = pickle.load(f)
    else:
        data = {'chsu_password': "ds3m#2nn",
                'chsu_login': "mobil"}
    if '-h' in sys.argv:
        main('hide_menu')
    else:
        main('menu')
