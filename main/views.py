import random
import requests
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

WIKI_URL = "https://en.wikipedia.org/w/api.php"
NEWSAPI_URL = "https://newsapi.org/v2/top-headlines?apiKey="
ARTSY_URL = ""

HEADERS = {"User-Agent": "Atlas/1.0 (gerenahu1@gmail.com)"}
CATEGORIES = ["Philosophy", "History", "Technology", "Business", "Politics", "Sports", "Art"]
SOURCES = [
    {"Philosophy": ["Wikipedia"]},
    {"History": ["Wikipedia"]},
    {"Technology": ["Wikipedia", "NewsAPI"]},
    {"Business": ["NewsAPI"]},
    {"Politics": ["NewsAPI"]},
    {"Sports": ["NewsAPI"]},
    {"Art": ["Artsy"]}
]
FEED = []

# Function to fetch from wikipedia
def fetch_wikipedia(query):
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srlimit": 50,
        "srsearch": query
    }
    response = requests.get(WIKI_URL, params=params)
    data = response.json()
    f = []
    
    for d in data["query"]["search"]:
        f.append(
            {
                "id": d["pageid"],
                "source": "Wikipedia",
                "img": "",
                "readTime": d["wordcount"]/210,
                "title": d["title"],
                "url": f"https://en.wikipedia.org/?curid={d["pageid"]}"
            }
        )

    try:
        FEED[query].append(f)
    except KeyError:
        FEED[query] = f
    return

# Function to fetch from NewsAPI
def fetch_newsapi(query):
    params = {
        "category": query
    }
    response = requests.get(NEWSAPI_URL, params=params)
    data = response.json()
    f = []

    for d in data["articles"]:
        f.append(
            {
                "id": "",
                "source": d["source"]["name"],
                "img": d["urlToImage"],
                "author": d["author"],
                "title": d["title"],
                "url": d["url"]
            }
        )

    try:
        FEED[query].append(f)
    except KeyError:
        FEED[query] = f
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
        if "Artsy" in SOURCES[category]:
            fetch_artsy(category)
    for i in FEED:
        FEED[i] = random.shuffle(FEED[i])
    return

# Function to cache articles
def save_articles(articles):
    return

@api_view(["GET"])
def home_feed(request):
    # if Redis cache ? Return pagination
    p_num = request.GET.get("pnum", 1)
    