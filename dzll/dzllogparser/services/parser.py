import datetime
import re
from typing import NamedTuple


FILE = '../ImmobilizerLog(2023_3_4_21_0).log'
TIMESTAMP_STR = '1677952821'

INIT_TYPE_STR_TRIGGER = 'initialized.'
DELETE_TYPE_STR_TRIGGER = 'DELETED.'


class Car(NamedTuple):
    car_id: int
    name: str
    car_type: str
    position: str
    status: str


class Player(NamedTuple):
    steam_id: int
    name: str


def defenition_input_data(input_str_data: str) -> None:
    if input_str_data.endswith(INIT_TYPE_STR_TRIGGER):
        pass
    elif input_str_data.endswith(DELETE_TYPE_STR_TRIGGER):
        pass
    else:
        pass


def get_player_data(player_data_string: str) -> Player:
    steam_id = re.search(r'(?<=steam:)[0-9]{17}', player_data_string).group(0)
    name = re.search(r'(?<=name:)(.*)(?=\ssteam:)',
                     player_data_string).group(0)
    return Player(
        steam_id=steam_id,
        name=name
    )


def get_car_data(log_string: str) -> Car:
    car_data_string = re.search(r'car:<.*>', log_string).group(0)
    name = re.search(
        r'(?<=\<name=\()(.*)(?=\)\stype=)', car_data_string).group(0)
    car_type = re.search(r'(?<=type=)(.*)(?=\sid=)', car_data_string).group(0)
    car_id = re.search(r'(?<=id=)\d*', car_data_string).group(0)
    position = re.search(
        r'(?<=pos=)(\d*\.\d{6}\s){3}', car_data_string).group(0).rstrip()
    status = re.search(r'(?<=status=\[).*(?=\])', car_data_string).group(0)
    return Car(car_id=car_id, name=name, car_type=car_type,
               position=position, status=status)


def get_action_time(directory_name: str,
                           action_str: str) -> datetime.datetime:
    current_timestamp = float(directory_name)
    current_date = datetime.date.fromtimestamp(current_timestamp)
    current_time_string = re.match(
        r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5]?[0-9]', action_str).group(0)
    action_time = datetime.datetime.strptime(
        current_time_string, '%H:%M:%S').time()
    
    return datetime.datetime.combine(current_date, action_time)


def parse_action_str(directory_name: str, action_str: str) -> list:
    action_time = get_action_time(directory_name, action_str)
    player_data_string = re.search(
        r'Player\{.*\.\d{6}\}\s', action_str).group(0)
    current_player = get_player_data(player_data_string)
    current_car = get_car_data(action_str)
    action = re.search(r'(?<=\.\d{6}\}\s)(.*)(?=\scar:)', action_str).group(0)
    return [action_time, current_player, current_car, action]


if __name__ == '__main__':
    def_str = '22:38:0 Player{name:Plan steam:76561199163269309 pos:2528.438721 257.033264 9583.657227} сел в машину car:<name=(GAZ-59037) type=BTR id=746019054 pos=2528.236328 256.355103 9582.357422 status=[FREE]>'
    print(parse_action_str(directory_name=TIMESTAMP_STR, action_str=def_str))
