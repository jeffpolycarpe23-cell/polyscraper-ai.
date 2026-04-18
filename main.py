from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
import requests
import os
import uvicorn

app = FastAPI()

# Configuration des templates
templates = Jinja2Templates(directory="templates")

def scrape_logic(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {"status": "Erreur", "data": f"Code {response.status_code}", "url": url}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tentative de trouver le titre
        title = "Produit inconnu"
        title_tag = soup.find("span", {"id": "productTitle"}) or soup.find("h1")
        if title_tag:
            title = title_tag.get_text().strip()

        # Tentative de trouver le prix (Amazon/eBay)
        price = "Prix non trouvé"
        # On cherche plusieurs classes communes
        price_selectors = [
            {"class": "a-offscreen"}, 
            {"class": "a-price-whole"}, 
            {"id": "prcIsum"}, 
            {"itemprop": "price"}
        ]
        for selector in price_selectors:
            found = soup.find(None, selector)
            if found:
                price = found.get_text().strip()
                break

        return {"status": "Succès", "data": f"{title} - {price}", "url": url}
    except Exception as e:
        return {"status": "Erreur", "data": str(e), "url": url}

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extract")
async def extract_data(request: Request):
    # Lecture JSON envoyée par ton JavaScript
    body = await request.json()
    links = body.get("links", [])
    
    results = []
    for url in links:
        if url.strip():
            res = scrape_logic(url.strip())
            results.append(res)
            
    return results

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
