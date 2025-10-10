import json
import random
import requests
import configparser
from .models import *
from datetime import datetime
from rest_framework import status
from django.shortcuts import render
from django.core.cache import cache
from django.core.paginator import Paginator
from rest_framework.response import Response
from django.http.response import JsonResponse
from rest_framework.decorators import api_view

today = datetime.today().strftime('%Y-%m-%d')

config = configparser.ConfigParser()
config.read("config.ini")

WIKI_URL = "https://en.wikipedia.org/w/api.php"
NEWSAPI_URL = f"https://newsapi.org/v2/top-headlines?apiKey={config.get('NEWSAPI', 'key')}"
ARTSY_URL = ""

HEADERS = {"User-Agent": "Atlas/1.0 (gerenahu1@gmail.com)"}
CATEGORIES = ["Philosophy", "History", "Technology", "Business", "Politics", "Sports", "Art"]
SOURCES = {
    "Philosophy": ["Wikipedia"],
    "History": ["Wikipedia"],
    "Technology": ["Wikipedia", "NewsAPI"],
    "Business": ["NewsAPI"],
    "Politics": ["NewsAPI"],
    "Sports": ["NewsAPI"],
    "Art": ["Artsy"]
}
ALL = {
    "date": today
}
FEED = []

def wiki_limits(query):
    if query == "Philosophy" or query == "History":
        return 30
    return 10

# Function to fetch from wikipedia
def fetch_wikipedia(query):
    print("FETCHING ⭐️: Wikipedia")
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srlimit": wiki_limits(query),
        "sroffset": random.randint(1,100)+50,
        "srsearch": query
    }
    response = requests.get(WIKI_URL, params=params, headers=HEADERS)
    data = json.loads(response.text)
    f = []
    
    for d in data["query"]["search"]:
        h = {
            "id": d["pageid"],
            "source": "Wikipedia",
            "img": "https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/500px-Wikipedia-logo-v2.svg.png",
            "readTime": d["wordcount"]/210,
            "title": d["title"],
            "url": f"https://en.wikipedia.org/?curid={d['pageid']}"
        }
        try:
            ALL[query].append(h)
        except KeyError:
            ALL[query] = [h]
        except Exception as e:
            raise e
    return

# Function to fetch from NewsAPI
def fetch_newsapi(query):
    print("FETCHING ⭐️: NewsAPI")
    params = {
        "category": query
    }
    response = requests.get(NEWSAPI_URL, params=params)
    data = response.json()
    f = []

    for d in data["articles"]:
        h = {
            "id": "",
            "source": d["source"]["name"],
            "img": d["urlToImage"],
            "author": d["author"],
            "title": d["title"],
            "url": d["url"]
        }
        try:
            ALL[query].append(h)
        except KeyError:
            ALL[query] = [h]
        except Exception as e:
            raise e
    return

# Function to fetch from Artsy
def fetch_artsy(query):
    return

# Function to build the homepage
def build_homepage():
    for category in CATEGORIES:
        if "Wikipedia" in SOURCES[category]:
            fetch_wikipedia(category)
        if "NewsAPI" in SOURCES[category]:
            fetch_newsapi(category)
    for i in ALL:
        FEED.extend(ALL[i])
    random.shuffle(FEED)
    save_articles()
    return

# Function to cache articles
def save_articles():
    cache.set("feed:home", FEED)
    cache.set("feed:categories", ALL)
    return

def home_feed(request):
    pnum = request.GET.get("pnum", 1)
    
    cache_key = "feed:home"
    cached_data = cache.get(cache_key)

    if cached_data:
        al = cache.get("feed:categories")
        if today == al["date"]:
            paginated = Paginator(cached_data, 30)
            # TODO: Implement logic to fetch more if it ends
            page = paginated.page(pnum)
            return JsonResponse({"status": 200, "has_more": page.has_next(), "data": page.object_list}, safe=False)
        f = Feed(feed=al, date=al["date"])
        f.save()

    build_homepage()
    paginated = Paginator(FEED, 30)
    page = paginated.page(pnum)
    return JsonResponse({"status": 201, "has_more": page.has_next(), "data": page.object_list}, safe=False)
    
def category_feed(request):
    category = request.GET.get("category", "")

    if category not in CATEGORIES:
        return JsonResponse({"status": 404, "message": "Category doesn't exist"}, status=404)
    
    cache_key = "feed:categories"
    cached_data = cache.get(cache_key)


    if cached_data:
        data = cached_data[category]
    
    else:
        build_homepage()
        data = ALL[category]

    return JsonResponse(data, safe=False)