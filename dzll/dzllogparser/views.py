from typing import Any

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, RedirectView, DetailView
from django.urls import reverse_lazy

from dzllogparser.services.ftp import get_ftp_data
from dzllogparser.models import Player, Car, Event
from dzllogparser.mixins import TitleMixin

class LoginUserView(LoginView):
    template_name = 'dzllogparser/login.html'
    form_class = AuthenticationForm
    redirect_authenticated_user = True


class IndexView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'dzllogparser/index.html'
    title = 'Index'


class PlayerView(LoginRequiredMixin, TitleMixin, DetailView):
    template_name = 'dzllogparser/player_view.html'
    model = Player
    title = 'Player view'

    def get_object(self):
        steam_id = self.kwargs.get('steam_id')
        return get_object_or_404(Player, steam_id=steam_id)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        last_actions = Event.objects.filter(player=self.object).select_related(
            'car', 'player').order_by('-action_time')
        paginated_actions = Paginator(last_actions, 15)
        page_number = self.request.GET.get('page', 1)
        actions_list = paginated_actions.page(page_number)

        context.update({
            'last_actions': actions_list,
            'current_page': int(page_number),
            'paginated_range': paginated_actions.page_range,
            'num_pages': paginated_actions.num_pages
        })
        return context


class CarView(LoginRequiredMixin, TitleMixin, DetailView):
    template_name = 'dzllogparser/car_view.html'
    model = Car
    title = 'Car view'

    def get_object(self):
        car_id = self.kwargs.get('car_id')
        return get_object_or_404(Car, car_id=car_id)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        last_actions = Event.objects.filter(car=self.object).select_related(
            'car', 'player').order_by('-action_time')

        paginated_actions = Paginator(last_actions, 15)
        page_number = self.request.GET.get('page', 1)
        actions_list = paginated_actions.page(page_number)

        context.update({
            'last_actions': actions_list,
            'current_page': int(page_number),
            'paginated_range': paginated_actions.page_range,
            'num_pages': paginated_actions.num_pages
        })
        return context


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


class SearchByNickname(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'dzllogparser/players_found.html'
    title = 'Search by nickname'

    def post(self, request):
        nickname = request.POST.get('nickname')
        players_with_nickname = Player.objects.filter(
            dayzname__icontains=nickname)
        context = {
            'players_with_nickname': players_with_nickname,
            'title': self.title,
        }
        return super(TemplateView, self).render_to_response(context)
