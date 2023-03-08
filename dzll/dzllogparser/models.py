from django.db import models


class Player(models.Model):
    steam_id = models.IntegerField(verbose_name='SteamID', db_index=True,
                                   unique=True)
    dayzname = models.CharField(max_length=255, verbose_name='DayZ nickname')
    dayz_alt_names = models.TextField(verbose_name='Alternate names',
                                      blank=True)


class Car(models.Model):
    class CarStatus(models.TextChoices):
        LINKED = 'LINKED', 'Linked'
        FREE = 'FREE', 'Free'
        DELETED = 'DELETED', 'Deleted'

    car_id = models.IntegerField(verbose_name='Server CarID', db_index=True)
    name = models.CharField(max_length=255, verbose_name='Car name')
    car_type = models.CharField(max_length=255, verbose_name='Car type')
    position = models.CharField(max_length=255, verbose_name='Coordinates')
    car_status = models.CharField(
        max_length=10, choices=CarStatus.choices,
        default=CarStatus.LINKED, verbose_name='Car Status'
    )
    last_linit_time = models.DateTimeField(verbose_name='Last init time')
    deletion_time = models.DateTimeField(verbose_name='Deletion time',
                                         blank=True)


class Event(models.Model):
    action_time = models.DateTimeField(verbose_name='Action time')
    player = models.ForeignKey(Player, on_delete=models.CASCADE,
                              verbose_name='Player')
    car = models.ForeignKey(Car, on_delete=models.PROTECT, verbose_name='Car')
    action = models.CharField(max_length=255, verbose_name='Action')
