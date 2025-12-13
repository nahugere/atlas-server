import json
import random
import hashlib
import requests
import configparser
from .models import *
from main.sources import *
from upstash_redis import Redis
from rest_framework import status
from datetime import date, datetime
from django.shortcuts import render
# from django.core.cache import cache
from django.core.paginator import Paginator
from rest_framework.response import Response
from django.http.response import JsonResponse
from rest_framework.decorators import api_view

today = datetime.today().strftime('%Y-%m-%d')

config = configparser.ConfigParser()
config.read("config.ini")

WIKI_URL = "https://en.wikipedia.org/w/api.php"
NEWSAPI_URL = f"https://newsapi.org/v2/top-headlines?apiKey={config.get('NEWSAPI', 'key')}"
HEADERS = {"User-Agent": "Atlas/1.0 (gerenahu1@gmail.com)"}
ARTSY_URL = ""

S = {
    "Wikipedia": WikiPedia(HEADERS),
    "NewsAPI": NewsAPI(HEADERS)
}

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

redis_url = config.get('UPSTASH', 'url').strip()
redis_token = config.get('UPSTASH', 'token').strip()

cache = Redis(url=redis_url, token=redis_token)

def wiki_limits(query):
    if query == "Philosophy" or query == "History":
        return 30
    return 10

# Function to build the homepage
def build_homepage():
    for category in CATEGORIES:
        if "Wikipedia" in SOURCES[category]:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srlimit": wiki_limits(category),
                "sroffset": random.randint(1,100)+50,
                "srsearch": category
            }
            _source = S["Wikipedia"].fetch_data(params, WIKI_URL)
            data = S["Wikipedia"].poppulate_data(_source, category)
        if "NewsAPI" in SOURCES[category]:
            params = {
                "category": category
            }
            _source = S["NewsAPI"].fetch_data(params, NEWSAPI_URL)
            data = S["NewsAPI"].poppulate_data(_source, category)

        FEED.extend(data)
        try:
            ALL[category].extend(data)
        except KeyError:
            ALL[category] = data
        except Exception as e:
            raise e
        
    random.shuffle(FEED)
    save_articles()

# Function to cache articles
def save_articles():
    cache.set("feed:home", json.dumps(FEED))
    cache.set("feed:categories", json.dumps(ALL))

def home_feed(request):
    pnum = request.GET.get("pnum", 1)

    print(config.get('UPSTASH', 'url'))
    print(config.get('UPSTASH', 'token'))
    # return
    
    cache_key = "feed:home"
    cached_data = cache.get(cache_key)

    if cached_data:
        # al = cache.get("feed:categories")
        # if today == al["date"]:
        paginated = Paginator(json.loads(cached_data), 30)
        # TODO: Implement logic to fetch more if it ends
        page = paginated.page(pnum)
        # f = Feed(feed=al, date=al["date"])
        # f.save()
        g = clean_data(page.object_list)
        return JsonResponse({"status": 200, "has_more": page.has_next(), "data": clean_data(page.object_list)}, safe=False)

    build_homepage()
    paginated = Paginator(FEED, 30)
    page = paginated.page(pnum)
    return JsonResponse({"status": 201, "has_more": page.has_next(), "data": clean_data(page.object_list)}, safe=False)
    
def category_feed(request):
    category = request.GET.get("category", "")

    if category not in CATEGORIES:
        return JsonResponse({"status": 404, "message": "Category doesn't exist"}, status=404)
    
    cache_key = "feed:categories"
    cached_data = json.loads(cache.get(cache_key))

    if cached_data:
        data = cached_data[category]
    
    else:
        build_homepage()
        data = ALL[category]

    return JsonResponse(data, safe=False)

def clean_data(data):
    rd = []
    for d in data:
        if type(d) == dict:
            rd.append(d)
    return rd

def detail_page(request):
    source = request.GET.get("s", "")
    category = request.GET.get("category", "")
    wiki_detail = request.GET.get("wd", "")
    
    detail = {}
    articles = []

    if source == "Wikipedia":
        # Get description and other data for wikipedia page
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageprops",
            "exintro": True,
            "explaintext": True,
            "ppprop": "description",
            "pageids": wiki_detail
        }
        _source = S["Wikipedia"].fetch_data(params, WIKI_URL)
        detail = S["Wikipedia"].poppulate_detail(_source, wiki_detail)
    
    else:
        # Get other data for other sources
        params = {
            "sources": source,
            "pageSize": 10
        }
        _source = S["NewsAPI"].fetch_data(params, NEWSAPI_URL)
        data = S["NewsAPI"].poppulate_data(_source, category)

        if len(data)>0:
            a = {
                "name": f"Articles From {source}",
                "articles": data
            }
            articles.append(a)


    cache_key = "feed:categories"
    cached_data = cache.get(cache_key)
    a = {
        "name": "Similar Articles",
        "articles": random.sample(json.loads(cached_data)[category], 12)
    }
    articles.append(a)

    return JsonResponse({"detail": detail, "articles": articles}, status=200)

# def detail_page(request):
#     # TODO: Remove repetitive articles looping logic
#     source = request.GET.get("s", "")
#     category = request.GET.get("category", "")
#     wiki_detail = request.GET.get("wd", "")
#     articles = []

#     if category not in CATEGORIES:
#         return JsonResponse({"status": 404, "message": "Category doesn't exist"}, status=404)

#     # Fetch articles from source
#     if source != "" and source != "Wikipedia":
#         p1 = {
#             "sources": source
#         }
#         r1 = requests.get(NEWSAPI_URL, params=p1)
#         same_source_articles = r1.json()
#         a = {
#             "name": "Articles From Source",
#             "articles": []
#         }

#         for d in same_source_articles["articles"]:
#             date = datetime.fromisoformat(d["publishedAt"].replace("Z", "+00:00"))
#             h = {
#                 "id": int(hashlib.sha256(d["title"].encode()).hexdigest(), 16) % 100000,
#                 "source": d["source"]["name"],
#                 "img": d["urlToImage"],
#                 "author": d["author"],
#                 "title": d["title"],
#                 "author": d["author"],
#                 "url": d["url"],
#                 "date": date.strftime("%b %d, %Y"),
#                 "category": category
#             }
#             if d["description"] == None:
#                 h["description"] = d["content"]
#             else:
#                 h["description"] = d["description"]
#             a["articles"].append(h)
#         articles.append(a)
    
#         # Fetch similar articles
#         p2 = {
#             "category": category
#         }
#         r2 = requests.get(NEWSAPI_URL, params=p2)
#         similar_articles = r2.json()

#         a = {
#             "name": "Simmilar Articles",
#             "articles": []
#         }
        
#         for d in similar_articles["articles"]:
#             date = datetime.fromisoformat(d["publishedAt"].replace("Z", "+00:00"))
#             h = {
#                 "id": int(hashlib.sha256(d["title"].encode()).hexdigest(), 16) % 100000,
#                 "source": d["source"]["name"],
#                 "img": d["urlToImage"],
#                 "author": d["author"],
#                 "title": d["title"],
#                 "author": d["author"],
#                 "url": d["url"],
#                 "date": date.strftime("%b %d, %Y"),
#                 "category": category
#             }
#             if d["description"] == None:
#                 h["description"] = d["content"]
#             else:
#                 h["description"] = d["description"]
#             a["articles"].append(h)
        
#         articles.append(a)

#         return JsonResponse({"articles": articles}, safe=False)
    
#     cache_key = "feed:categories"
#     cached_data = cache.get(cache_key)

#     d = {}

#     if wiki_detail != "":
#         params = {
#             "action": "query",
#             "format": "json",
#             "prop": "extracts|pageprops",
#             "exintro": True,
#             "explaintext": True,
#             "ppprop": "description",
#             "pageids": wiki_detail
#         }
#         response = requests.get(WIKI_URL, params=params, headers=HEADERS)
#         data = response.json()
#         page = data["query"]["pages"][str(wiki_detail)]
#         if page.get("pageprops", {}).get("description"):
#             d["summary"] = page.get("pageprops", {}).get("description")[0:900]
#         elif page.get("extract"):
#             d["summary"] = page.get("extract")[0:500]

#     if cached_data:
#         data = json.loads(cached_data)[category]
#         return JsonResponse({
#             "detail": d,
#             "name": "Similar Articles",
#             "articles": random.sample(data, 12)
#         }, safe=False)
#     return JsonResponse({"message": "We couldn't find the content you requested"}, status=404)



def search(request):
    search = request.GET.get("search")
    return JsonResponse({"message": f"you searched for {search}"}, status=200)