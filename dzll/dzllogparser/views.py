from typing import Any

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, RedirectView, DetailView
from django.urls import reverse_lazy

from dzllogparser.services.ftp import get_ftp_data
from dzllogparser.models import Player, Car


class LoginUserView(LoginView):
    template_name = 'dzllogparser/login.html'
    form_class = AuthenticationForm
    redirect_authenticated_user = True


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'dzllogparser/index.html'


class PlayerView(LoginRequiredMixin, DetailView):
    template_name = 'dzllogparser/player_view.html'
    model = Player

    def get_object(self):
        steam_id = self.kwargs.get('steam_id')
        return get_object_or_404(Player, steam_id=steam_id)


class CarView(LoginRequiredMixin, DetailView):
    template_name = 'dzllogparser/car_view.html'
    model = Car

    def get_object(self):
        car_id = self.kwargs.get('car_id')
        return get_object_or_404(Car, car_id=car_id)


class UpdateDbView(LoginRequiredMixin, RedirectView):
    pattern_name = 'index'

    def get_redirect_url(self, *args, **kwargs):
        get_ftp_data()
        return super().get_redirect_url(*args, **kwargs)


class SearchPlayerBySteamIDView(LoginRequiredMixin, RedirectView):
    def post(self, request):
        steam_id = request.POST.get('steam_id')
        player_object = get_object_or_404(Player, steam_id=steam_id)
        return redirect(player_object)


class SearchCarByIDView(LoginRequiredMixin, RedirectView):
    def post(self, request):
        car_id = request.POST.get('car_id')
        car_object = get_object_or_404(Car, car_id=car_id)
        return redirect(car_object)


class SearchByNickname(LoginRequiredMixin, TemplateView):
    template_name = 'dzllogparser/index.html'
