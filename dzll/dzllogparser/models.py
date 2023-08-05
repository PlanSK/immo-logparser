from django.db import models
from django.urls import reverse_lazy


class Player(models.Model):
    steam_id = models.CharField(max_length=255, verbose_name='SteamID', 
                                db_index=True, unique=True)
    bohemia_id = models.CharField(max_length=255, verbose_name='Bohemia ID',
                                  blank=True, unique=True)
    dayzname = models.CharField(max_length=255, verbose_name='DayZ nickname')
    dayz_alt_names = models.TextField(verbose_name='Alternate names',
                                      blank=True)

    def get_absolute_url(self):
        return reverse_lazy('player_by_steam_id',
                            kwargs={'steam_id': self.steam_id})

    def __str__(self):
        return f'{self.dayzname} ({self.steam_id})'


class Location(models.Model):
    location_datetime = models.DateTimeField(
        verbose_name='Location Date and Time')
    coord_x = models.FloatField(verbose_name='X coordinate')
    coord_y = models.FloatField(verbose_name='Y coordinate')
    note = models.CharField(max_length=255, verbose_name='Note')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True,
                               null=True, verbose_name='Player')


class Car(models.Model):
    class CarStatus(models.TextChoices):
        LINKED = 'LINKED', 'Linked'
        FREE = 'FREE', 'Free'
        DELETED = 'DELETED', 'Deleted'

    car_id = models.CharField(max_length=255, verbose_name='Server CarID',
                              db_index=True)
    name = models.CharField(max_length=255, verbose_name='Car name')
    car_type = models.CharField(max_length=255, verbose_name='Car type')
    position = models.ForeignKey(Location, on_delete=models.PROTECT)
    car_status = models.CharField(
        max_length=10, choices=CarStatus.choices,
        default=CarStatus.LINKED, verbose_name='Car Status'
    )
    last_init_time = models.DateTimeField(verbose_name='Last init time',
                                          blank=True, null=True)
    deletion_time = models.DateTimeField(verbose_name='Deletion time',
                                         blank=True, null=True)
    last_using_time = models.DateTimeField(verbose_name='Last using time',
                                         blank=True, null=True)

    def get_absolute_url(self):
        return reverse_lazy('car_by_id',
                            kwargs={'car_id': self.car_id})

    def __str__(self):
        return f'{self.name} ({self.car_id})'


class Event(models.Model):
    action_time = models.DateTimeField(verbose_name='Action time')
    player = models.ForeignKey(Player, on_delete=models.CASCADE,
                              verbose_name='Player', blank=True, null=True)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name='Car')
    action = models.CharField(max_length=255, verbose_name='Action')
    position = models.ForeignKey(Location, on_delete=models.PROTECT,
                                 verbose_name='Location')

    def __str__(self) -> str:
        return f'{self.action_time} {self.player} {self.action}'
