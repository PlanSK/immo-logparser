from django.contrib import admin
from django.urls import path, include

from dzllogparser.views import IndexView


urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('update/', IndexView.as_view(), name='update_db')
]
