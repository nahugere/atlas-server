from django.urls import path, include
from . import views as v

urlpatterns = [
    path("home/", v.home_feed, name="home"),
    path("category/", v.category_feed, name="category")
]
