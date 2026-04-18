from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()

# Ton design est stocké ici
def get_html(results_html=""):
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PolyScraper AI v2.1</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#0b1120] text-white font-sans min-h-screen flex items-center justify-center p-4">
        <div class="w-full max-w-md bg-[#171f2f] rounded-3xl shadow-2xl p-6 border border-slate-800">
            <div class="text-center mb-8">
                <h1 class="text-3xl font-extrabold tracking-tight">🕵️‍♂️ PolyScraper <span class="text-blue-500">AI</span></h1>
                <p class="text-slate-400 text-xs mt-2">Mode Multi-Liens Activé</p>
            </div>

            <form action="/extract" method="post" class="space-y-4">
                <textarea name="links" rows="4" required class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 outline-none focus:border-blue-500" placeholder="Collez vos liens ici..."></textarea>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-2xl transition-all uppercase">EXTRAIRE LES DONNÉES ⚡</button>
            </form>

            <div id="results" class="mt-8 space-y-3">
                {results_html}
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def home():
    return get_html()

@app.post("/extract", response_class=HTMLResponse)
async def extract(links: str = Form(...)):
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results_cards = ""
    
    headers = {{"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}}

    for url in list_links:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            title = (soup.title.string[:35] + '...') if soup.title else "Produit"
            
            # Recherche du prix Amazon
            price = "Vérification..."
            price_tag = soup.find("span", {{"class": "a-offscreen"}}) or soup.find("span", {{"class": "a-price-whole"}})
            if price_tag:
                price = price_tag.get_text().strip()
            
            # Création du petit bloc de résultat
            results_cards += f'''
            <div class="bg-[#1e293b] p-3 rounded-xl border border-slate-700">
                <p class="text-blue-400 text-sm font-bold truncate">{title}</p>
                <p class="text-xs text-white">Prix détecté : <span class="font-bold text-green-400">{price}</span></p>
            </div>
            '''
        except:
            results_cards += f'<div class="text-red-400 text-xs">Erreur sur : {url[:30]}...</div>'
            
    return get_html(results_cards)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
