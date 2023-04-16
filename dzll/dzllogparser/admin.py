from django.contrib import admin

from dzllogparser.models import Car, Player, Event


class EventAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'player', 'action', 'car')
    search_fields = ('player', 'action', 'car')
    list_filter = ('action',)


class CarAdmin(admin.ModelAdmin):
    list_display = ('car_id', 'name', 'car_status')
    list_filter = ('car_status',)


admin.site.register(Car, CarAdmin)
admin.site.register(Player)
admin.site.register(Event, EventAdmin)
