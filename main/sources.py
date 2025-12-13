from datetime import datetime
import hashlib
import requests

class Source:

    def __init__(self, headers):
        self.headers = headers
    
    def poppulate_data(self, data, q):
        raise NotImplementedError

    def fetch_data(self, params, url):
        try:
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            return data
        except Exception as e:
            raise ConnectionError

class WikiPedia(Source):

    def __init__(self, headers):
        super().__init__(headers)

    def fetch_data(self, params, url):
        print("FETCHING WIKIPEDIA ⭐️")
        return super().fetch_data(params, url)
    
    def poppulate_data(self, data, q):
        a = []
    
        for d in data["query"]["search"]:
            h = {
                "id": d["pageid"],
                "source": "Wikipedia",
                "img": "https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/500px-Wikipedia-logo-v2.svg.png",
                "readTime": d["wordcount"]/210,
                "title": d["title"],
                "url": f"https://en.wikipedia.org/?curid={d['pageid']}",
                "category": q
            }
            a.append(h)
        
        return a

    def poppulate_detail(self, data, q):
        d = {}
        page = data["query"]["pages"][str(q)]
        if page.get("pageprops", {}).get("description"):
            d["description"] = page.get("pageprops", {}).get("description")[0:900]
        elif page.get("extract"):
            d["description"] = page.get("extract")[0:500]
        
        return d

class NewsAPI(Source):

    def __init__(self, headers):
        super().__init__(headers)

    def fetch_data(self, params, url):
        print("FETCHING NEWSAPI ⭐️")
        return super().fetch_data(params, url)
    
    def poppulate_data(self, data, q):
        a = []

        for d in data["articles"]:
            date = datetime.fromisoformat(d["publishedAt"].replace("Z", "+00:00"))
            h = {
                "id": int(hashlib.sha256(d["title"].encode()).hexdigest(), 16) % 100000,
                "source": d["source"]["name"],
                "img": d["urlToImage"],
                "author": d["author"],
                "title": d["title"],
                "author": d["author"],
                "url": d["url"],
                "date": date.strftime("%b %d, %Y"),
                "category": q
            }
            if d["description"] == None:
                h["description"] = d["content"]
            else:
                h["description"] = f'{d["description"][0:200]}...'
            a.append(h)
        
        return a

    def poppulate_detail(self, data, q):
        return