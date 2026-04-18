from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import uvicorn
import io

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Fonction de Scraping améliorée
def scrape_item(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept-Language": "fr-FR,fr;q=0.9"
    }
    try:
        res = requests.get(url.strip(), headers=headers, timeout=10)
        if res.status_code != 200:
            return {"url": url, "nom": "Erreur", "prix": f"Code {res.status_code}", "status": "🔴"}
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extraction du Titre
        title = "Produit inconnu"
        t_tag = soup.find("span", {"id": "productTitle"}) or soup.find("h1")
        if t_tag: title = t_tag.get_text().strip()[:50] + "..."

        # Extraction du Prix (Multi-sélecteurs pour Amazon/eBay)
        price = "Non détecté"
        p_tags = [
            soup.find("span", {"class": "a-offscreen"}),
            soup.find("span", {"id": "prcIsum"}),
            soup.find("div", {"class": "pre-price"}),
            soup.find("span", {"class": "a-price-whole"})
        ]
        for tag in p_tags:
            if tag:
                price = tag.get_text().strip()
                break
                
        return {"url": url, "nom": title, "prix": price, "status": "🟢"}
    except:
        return {"url": url, "nom": "Lien invalide", "prix": "-", "status": "❌"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": None})

@app.post("/extract")
async def extract(request: Request):
    form_data = await request.form()
    links_raw = form_data.get("links", "")
    links_list = [l for l in links_raw.split("\n") if l.strip()]
    
    final_results = []
    for link in links_list:
        data = scrape_item(link)
        final_results.append(data)
        
    return templates.TemplateResponse("index.html", {"request": request, "results": final_results})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
