from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()
# Assure-toi que le nom du dossier sur GitHub est bien "templates"
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "results": None})

@app.post("/extract")
async def extract(request: Request, links: str = Form(...)):
    # On sépare les liens et on nettoie
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}

    for url in list_links:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # Extraction simple du titre pour tester
            title = soup.title.string if soup.title else "Produit sans titre"
            results.append({"nom": title[:50], "url": url, "status": "🟢"})
        except:
            results.append({"nom": "Lien erroné", "url": url, "status": "❌"})
            
    return templates.TemplateResponse("index.html", {"request": request, "results": results})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
