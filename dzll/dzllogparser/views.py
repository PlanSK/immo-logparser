from typing import Any

from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, RedirectView, DetailView, View
from django.urls import reverse_lazy

from dzllogparser.services.ftp import get_updates_from_ftp
from dzllogparser.models import Player, Car, Event
from dzllogparser.mixins import TitleMixin


class LoginUserView(LoginView):
    template_name = 'dzllogparser/login.html'
    form_class = AuthenticationForm
    redirect_authenticated_user = True


class IndexView(LoginRequiredMixin, TitleMixin, TemplateView):
    template_name = 'dzllogparser/index.html'
    title = 'Index'
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'players_number': Player.objects.all().count(),
            'cars_number': Car.objects.all().count(),
            'events_number': Event.objects.all().count(),
        })
        return context


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
        page_number = int(self.request.GET.get('page', 1))
        actions_list = paginated_actions.page(page_number)
        if paginated_actions.num_pages > 40:
            if page_number < 20:
                page_range = range(1, 41)
            else:
                if page_number - 18 <= 0:
                    start_range = 1
                else:
                    start_range = page_number - 18
                if page_number + 20 > paginated_actions.num_pages:
                    page_range = range(start_range,
                                       paginated_actions.num_pages + 1)
                else:
                    page_range = range(start_range, page_number + 21)
        else:
            page_range = paginated_actions.page_range

        context.update({
            'last_actions': actions_list,
            'current_page': int(page_number),
            'paginated_range': page_range,
            'num_pages': paginated_actions.num_pages
        })
        return context


class UpdateDbView(LoginRequiredMixin, View):
    """Manual update db view"""
    def get(self, request, *args, **kwargs):
        records_status = get_updates_from_ftp()
        return HttpResponse(
            f'Player: created {records_status.players_created}, '
            f'updated {records_status.players_updated}. '
            f'Car created {records_status.car_created}, '
            f'updated {records_status.car_updated}, '
            f'deleted {records_status.car_deleted}. '
            f'Events created: {records_status.events_created}. '
            f'Eplased time: {records_status.elapsed_time}s.'
        )


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
        founded_players = Player.objects.filter(
            Q(dayzname__icontains=nickname) | \
                Q(dayz_alt_names__icontains=nickname))
        context = {
            'players_with_nickname': founded_players,
            'title': self.title,
        }
        return super(TemplateView, self).render_to_response(context)


def logout_user(request):
    logout(request)
    return redirect('login')


def page_not_found(request, exception):
    response = render(request, 'dzllogparser/404.html',
                      {'title': 'Page not found'})
    response.status_code = 404
    return response


def page_forbidden(request, exception):
    response = render(
        request, 'dzllogparser/403.html', {'title': 'Access forbidden'}
    )
    response.status_code = 403
    return response


def page_server_error(request):
    response = render(
        request, 'dzllogparser/500.html', {'title': 'Internal Server Error'}
    )
    response.status_code = 500
    return response
