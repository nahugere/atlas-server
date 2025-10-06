from django.urls import path, include
from . import views as MViews

urlpatterns = [
    path("home/", MViews.home_feed)
]
