from django.contrib import admin
from django.urls import path, include

from dzllogparser.views import (
    IndexView, LoginUserView, PlayerView, CarView, SearchPlayerBySteamIDView,
    SearchCarByIDView, SearchByNickname, UpdateDbView, logout_user,
    VehicleTheftCasesView, VehicleLongUnusedView, CarDeleteView,
    TransportOwnersView)


urlpatterns = [
    path('login/', LoginUserView.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('', IndexView.as_view(), name='index'),
    path('player_by_steamid/<str:steam_id>/', PlayerView.as_view(),
        name='player_by_steam_id'),
    path('car_by_id/<int:car_id>/', CarView.as_view(), name='car_by_id'),
    path('search_by_steam_id/', SearchPlayerBySteamIDView.as_view(),
        name='search_by_steam_id'),
    path('search_by_car_id/', SearchCarByIDView.as_view(),
        name='search_by_car_id'),
    path('search_by_nickname/', SearchByNickname.as_view(),
        name='search_by_nickname'),
    path('vehicle_theft_view/', VehicleTheftCasesView.as_view(),
        name='vehicle_theft_view'),
    path('vehicle_long_unused/', VehicleLongUnusedView.as_view(),
        name='vehicle_long_unused'),
    path('delete_car/<int:pk>/', CarDeleteView.as_view(),
        name='delete_car'),
    path('update/', UpdateDbView.as_view(), name='update_db'),
    path('transport_owner_view/<str:steam_id>/', TransportOwnersView.as_view(),
         name='transport_owner_view'),
]
