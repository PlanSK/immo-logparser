import datetime
import logging
import re

from typing import NamedTuple
from dataclasses import dataclass
from enum import Enum


parser_logger = logging.getLogger(__name__)


INIT_TYPE_STR_TRIGGER = 'initialized.'
DELETE_TYPE_STR_TRIGGER = 'DELETED.'


@dataclass
class Car:
    car_id: str
    name: str
    car_type: str
    position: str
    status: str
    last_init_time: datetime.datetime | None
    deletion_time: datetime.datetime | None
    last_use_time: datetime.datetime | None

@dataclass
class Player:
    steam_id: str
    name: str
    alter_names: set


class EventType(Enum):
    ACTION = 1
    DELETE = 2


@dataclass
class Event:
    event_type: EventType
    event_time: datetime.datetime
    action: str
    player: Player | None
    car_id: int
    position: str | None


class LogfileData(NamedTuple):
    players: dict
    cars: dict
    events: list


def get_player_data(log_string: str) -> Player:
    """Returns Player dataclass with parsed data."""
    player_data_string = re.search(
        r'Player\{.*\.\d{6}\}\s', log_string).group(0)
    steam_id = re.search(r'(?<=steam:)[0-9]{17}', player_data_string).group(0)
    name = re.search(r'(?<=name:)(.*)(?=\ssteam:)',
                     player_data_string).group(0)
    return Player(
        steam_id=steam_id,
        name=name,
        alter_names=set()
    )


def get_car_data(log_string: str) -> Car:
    """Returns Car dataclass with parsed data."""
    car_data_string = re.search(r'car:<.*>', log_string).group(0)
    name = re.search(
        r'(?<=\<name=\()(.*)(?=\)\stype=)', car_data_string).group(0)
    car_type = re.search(r'(?<=type=)(.*)(?=\sid=)', car_data_string).group(0)
    car_id = re.search(r'(?<=id=)\d*', car_data_string).group(0)
    position_list = re.search(r'(?<=pos=)(\d*\.\d{6}\s){3}',
                              car_data_string).group(0).rstrip().split()
    rounded_position_list = [
        position[:-3] for position in position_list
    ]
    position = ', '.join(rounded_position_list)
    status = re.search(r'(?<=status=\[).*(?=\])', car_data_string).group(0)
    return Car(car_id=car_id, name=name, car_type=car_type, position=position,
               status=status, last_init_time=None, deletion_time=None,
               last_use_time=None)


def get_date_from_timestamp_str(timestamp: str) -> datetime.date:
    """Returns date from timestamp string"""
    current_timestamp = float(timestamp)
    current_date = datetime.datetime.utcfromtimestamp(current_timestamp).date()
    return current_date


def get_action_time(directory_name: str,
                           action_str: str) -> datetime.datetime:
    """Returns Action time from timestamp and parsed time."""
    current_date = get_date_from_timestamp_str(directory_name)
    current_time_string = re.match(
        r'^([0-1]?[0-9]|2[0-3]):[0-5]?[0-9]:[0-5]?[0-9]', action_str).group(0)
    action_time = datetime.datetime.strptime(
        current_time_string, '%H:%M:%S').time()
    return datetime.datetime.combine(
        current_date, action_time, tzinfo=datetime.timezone(
            offset=datetime.timedelta(hours=3))
    )


def get_action_str(log_string: str) -> str:
    """Returns parsed action text."""
    action_str = re.search(r'(?<=\.\d{6}\}\s)(.*)(?=\scar:)',
                           log_string).group(0)
    return action_str


def defenition_logfile_data(dir_name: str, file_strings: list) -> LogfileData:
    """Parsed data from file strings and returns LogfileData models
    with cars, players and events.
    """
    players = dict()
    cars = dict()
    events = []
    for number, file_string in enumerate(file_strings):
        log_string = file_string.strip()
        player = None
        try:
            car = get_car_data(log_string)
            action_time = get_action_time(dir_name, log_string)
        except AttributeError:
            parser_logger.info(f'Line {number} is skipped.')
            continue
        exists_record = cars.get(car.car_id)
        if exists_record:
            car.last_init_time = exists_record.last_init_time
        cars.update({car.car_id: car})
        if log_string.endswith(INIT_TYPE_STR_TRIGGER):
            car.last_init_time = action_time
            continue
        elif log_string.endswith(DELETE_TYPE_STR_TRIGGER):
            event_type = EventType.DELETE
            action=DELETE_TYPE_STR_TRIGGER
            car.deletion_time = action_time
            car.status = 'DELETED'
        else:
            player = get_player_data(log_string)
            db_player = players.get(player.steam_id)
            if (db_player and db_player.name != player.name):
                db_player.alter_names.add(db_player.name)
                db_player.name = player.name
                player = db_player
            players.update({player.steam_id: player})
            event_type = EventType.ACTION
            action = get_action_str(log_string)
            car.last_use_time = action_time
        events.append(Event(
            event_type=event_type, event_time=action_time, action=action,
            player=player, car_id=car.car_id, position=car.position))
    return LogfileData(players=players, cars=cars, events=events)
