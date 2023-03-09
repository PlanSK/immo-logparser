import datetime
import logging

from django.utils import timezone

from dzllogparser.models import Car, Player, Event
from dzllogparser.services.parser import LogfileData


db_logger = logging.getLogger(__name__)


def import_logfile_data_into_db(logfile_data: LogfileData):
    player_record_result = import_players_into_db(logfile_data.players)
    car_record_result = import_cars_into_db(logfile_data.cars)
    events_record_result = import_events_into_db(logfile_data.events)


def import_players_into_db(players: dict) -> tuple[int, int]:
    """Add new players into db and updating existing,
    and returns numbers of created and updated records.
    """
    queryset_objects_steam_id = Player.objects.values_list('steam_id')
    players_to_create = []
    players_to_update = []
    existing_steam_id_list = [
        steam_id for steam_id, in queryset_objects_steam_id]
    for steam_id, player in players.items():
        if steam_id in existing_steam_id_list:
            players_to_update.append(player)
        else:
            players_to_create.append(player)
    created_records = Player.objects.bulk_create(
        [
            Player(steam_id=player.steam_id, dayzname=player.name,
                   dayz_alt_names=', '.join(player.alter_names))
            for player in players_to_create
        ],
        batch_size=500
    )
    existing_records_in_db = Player.objects.filter(
        steam_id__in=[player.steam_id for player in players_to_update])
    records_for_update = []
    for player_record in existing_records_in_db:
        current_player = players.get(player_record.steam_id)
        if player_record.dayzname != current_player:
            player_record.dayzname = current_player.name
            player_record.dayz_alt_names = ', '.join(
                current_player.alter_names)
            records_for_update.append(player_record)
        else:
            continue
    updated_players = Player.objects.bulk_update(
        records_for_update, ['dayzname', 'dayz_alt_names'],
        batch_size=500
    )
    return (created_records, updated_players)


def import_cars_into_db(cars: dict) -> tuple[int, int, int]:
    """Add new cars into db, updating existing 
    and also deletes old deleted cars records.
    Returns numbers of created, updated and deleted records.
    """
    queryset_objects_steam_id = Car.objects.values_list('car_id')
    cars_to_create = []
    cars_to_update = []
    existing_car_id_list = [
        car_id for car_id, in queryset_objects_steam_id]
    for car_id, car in cars.items():
        if car_id in existing_car_id_list:
            cars_to_update.append(car)
        else:
            cars_to_create.append(car)
    created_records = Car.objects.bulk_create(
        [
            Car(car_id=car.car_id, name=car.name, car_type=car.car_type,
                position=car.position,car_status=car.status,
                last_init_time=car.last_init_time,
                deletion_time=car.deletion_time)
            for car in cars_to_create
        ],
        batch_size=500
    )
    existing_records_in_db = Car.objects.filter(
        car_id__in=[car_id for car_id in cars.keys()])
    for car_record in existing_records_in_db:
        current_car = cars.get(car_record.car_id)
        car_record.car_status=current_car.status
        car_record.deletion_time = current_car.deletion_time
        car_record.last_init_time = current_car.last_init_time
        car_record.position = current_car.position
    updated_records = Car.objects.bulk_update(
        existing_records_in_db,
        ['car_status', 'deletion_time', 'last_init_time', 'position'],
        batch_size=500
    )
    last_1_month_datetime = timezone.now() - datetime.timedelta(
        days=30)
    deleted_records, _ = Car.objects.filter(
        deletion_time__lt=last_1_month_datetime).delete()
    return (created_records, updated_records, deleted_records)


def import_events_into_db(events_list: list) -> int:
    """Add new events into db, and returns number of created records"""
    created_records = Event.objects.bulk_create([
        Event(action_time=event.event_date,
              player=Player.objects.get(steam_id=event.player.steam_id) \
                  if event.player else None,
              car=Car.objects.get(car_id=event.car_id),
              action=event.action)
        for event in events_list
    ], batch_size=1000)
    return created_records
