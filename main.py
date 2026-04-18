from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}
    try:
        r = requests.get(url.strip(), headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Trouver le nom
        nom = "Produit inconnu"
        n_tag = soup.find("span", {"id": "productTitle"}) or soup.find("h1")
        if n_tag: nom = n_tag.get_text().strip()[:40] + "..."

        # Trouver le prix
        prix = "Non trouvé"
        p_tag = soup.find("span", {"class": "a-offscreen"}) or soup.find("span", {"class": "a-price-whole"})
        if p_tag: prix = p_tag.get_text().strip()

        return {"nom": nom, "prix": prix, "url": url, "status": "🟢"}
    except:
        return {"nom": "Lien invalide", "prix": "-", "url": url, "status": "❌"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": None})

@app.post("/extract")
async def extract(request: Request, links: str = Form(...)):
    links_list = [l for l in links.split("\n") if l.strip()]
    results = [get_data(l) for l in links_list]
    return templates.TemplateResponse("index.html", {"request": request, "results": results})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
