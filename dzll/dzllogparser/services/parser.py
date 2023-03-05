import datetime
import re
import os

from typing import NamedTuple
from dataclasses import dataclass
from enum import Enum


FILE = 'ImmobilizerLog(2023_3_4_21_0).log'
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


class EventType(Enum):
    INIT = 1
    ACTION = 2
    DELETE = 3


@dataclass
class Event:
    event_type: EventType
    event_date: datetime.datetime
    action: str
    player: Player | None
    car: Car


def get_player_data(log_string: str) -> Player:
    player_data_string = re.search(
        r'Player\{.*\.\d{6}\}\s', log_string).group(0)
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
        r'^([0-1]?[0-9]|2[0-3]):[0-5]?[0-9]:[0-5]?[0-9]', action_str).group(0)
    action_time = datetime.datetime.strptime(
        current_time_string, '%H:%M:%S').time()
    
    return datetime.datetime.combine(current_date, action_time)


def get_action_str(log_string: str) -> str:
    action_str = re.search(r'(?<=\.\d{6}\}\s)(.*)(?=\scar:)',
                           log_string).group(0)
    return action_str


def defenition_input_data(dir_name: str, filename: str) -> list:
    players = dict()
    cars = dict()
    events = []
    file_path = os.path.join(os.getcwd(), filename)
    with open(file_path, 'r', encoding='utf-8') as file_instance:
        for number, file_string in enumerate(file_instance):
            log_string = file_string.strip()
            player = None
            try:
                car = get_car_data(log_string)
                action_date = get_action_time(dir_name, log_string)
            except AttributeError:
                print(f'Line {number} is skipped.')
                continue
            cars.update({car.car_id: car})
            
            if log_string.endswith(INIT_TYPE_STR_TRIGGER):
                event_type = EventType.INIT
                action=INIT_TYPE_STR_TRIGGER
            elif log_string.endswith(DELETE_TYPE_STR_TRIGGER):
                event_type = EventType.DELETE
                action=DELETE_TYPE_STR_TRIGGER
            else:
                player = get_player_data(log_string)
                players.update({player.steam_id: player})
                event_type = EventType.ACTION
                action = get_action_str(log_string)
            events.append(Event(
                event_type=event_type, event_date=action_date,
                action=action, player=player, car=car))
    return [players, cars, events]


if __name__ == '__main__':
    print(defenition_input_data(dir_name=TIMESTAMP_STR, filename=FILE))
