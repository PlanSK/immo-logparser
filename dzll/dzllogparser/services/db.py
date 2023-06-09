import logging
import time

from dataclasses import dataclass

from django.conf import settings
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from dzllogparser.models import Car, Player, Event
from dzllogparser.services.parser import LogfileData


db_logger = logging.getLogger(__name__)


@dataclass
class RecordsStatus:
    players_created: int = 0
    players_updated: int = 0
    car_created: int = 0
    car_updated: int = 0
    car_deleted: int = 0
    events_created: int = 0
    elapsed_time: float = 0.0


@dataclass
class OwnersCarStat:
    owner: Player
    car_count: int
    cars_list: list[Car]


def import_logfile_data_into_db(logfile_data: LogfileData,
                                days_limit: int = 0) -> RecordsStatus:
    """Calls functions to load data into db"""
    start_time = time.monotonic()
    player_created_records, player_updated_players = import_players_into_db(
        logfile_data.players)
    db_logger.info(
        f'Player records created: {player_created_records}. '
        f'Player records updated: {player_updated_players}. '
    )
    (car_created_records, car_updated_records,
            car_deleted_records) = import_cars_into_db(logfile_data.cars,
                                                       days_limit)
    db_logger.info(
        f'Car records created: {car_created_records}. '
        f'Car records updated: {car_updated_records}. '
        f'Old records has been deleted: {car_deleted_records}. '
    )
    events_record_result = import_events_into_db(logfile_data.events)
    db_logger.info(
        f'Event records created: {events_record_result}.'
    )
    elapsed_time = time.monotonic() - start_time
    db_logger.info(f'Eplased time: {elapsed_time}.')
    return RecordsStatus(
        players_created=player_created_records,
        players_updated=player_updated_players,
        car_created=car_created_records,
        car_updated=car_updated_records,
        car_deleted=car_deleted_records,
        events_created=events_record_result,
        elapsed_time=round(elapsed_time, 3)
    )


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
    return (len(created_records), updated_players)


def import_cars_into_db(cars: dict,
                        days_limit: int = 0) -> tuple[int, int, int]:
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
                position=car.position, car_status=car.status,
                last_init_time=car.last_init_time,
                deletion_time=car.deletion_time,
                last_using_time=car.last_use_time)
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
        if current_car.last_use_time:
            car_record.last_using_time = current_car.last_use_time
    updated_records = Car.objects.bulk_update(
        existing_records_in_db,
        ['car_status', 'deletion_time', 'last_init_time',
         'position', 'last_using_time'],
        batch_size=500
    )
    if days_limit:
        limit_datetime = timezone.now() - timezone.timedelta(
            days=days_limit)
        deleted_records, _ = Car.objects.filter(
            deletion_time__lt=limit_datetime).delete()
    else:
        deleted_records = 0
    return (len(created_records), updated_records, deleted_records)


def import_events_into_db(events_list: list) -> int:
    """Add new events into db, and returns number of created records"""
    created_records = Event.objects.bulk_create([
        Event(action_time=event.event_time,
              player=Player.objects.get(steam_id=event.player.steam_id) \
                  if event.player else None,
              car=Car.objects.get(car_id=event.car_id),
              action=event.action, position=event.position)
        for event in events_list
    ], batch_size=950)
    return len(created_records)


def change_status_for_phantoms() -> None:
    """Change car status to deleted if car not initialized for the last 6 
    hours
    """
    limit_phantom_time = timezone.now() - timezone.timedelta(hours=6)
    phantom_vehicle_list = Car.objects.filter(
        Q(last_init_time__lt=limit_phantom_time) |
        Q(last_init_time__isnull=True)).exclude(
            car_status=Car.CarStatus.DELETED)
    for phantom_vehicle in phantom_vehicle_list:
        phantom_vehicle.car_status='DELETED'
        try:
            phantom_vehicle.deletion_time=phantom_vehicle.last_init_time + \
                timezone.timedelta(hours=3)
        except TypeError:
            pass
    Car.objects.bulk_update(
        phantom_vehicle_list, ['car_status', 'deletion_time'], batch_size=500
    )


def get_player_cars(steam_id: str) -> OwnersCarStat:
    """Returns OwnersCarStat with count of player cars, and cars list"""
    player = get_object_or_404(Player, steam_id=steam_id)
    interval = timezone.now() - timezone.timedelta(
    days=settings.MINIMAL_USED_DAYS_CRITERIA)
    cars_stat = Event.objects.filter(
        player=player,
        action_time__gte=interval
    ).select_related('car', 'player').values('car').annotate(Count('car'))
    cars_id_list = [
        car['car']
        for car in cars_stat
        if car['car__count'] > settings.MINIMAL_ENEVT_COUNT_CRITERIA
    ]
    cars_list = list(Car.objects.filter(id__in=cars_id_list))
    return OwnersCarStat(owner=player, car_count=len(cars_list),
                         cars_list=cars_list)
