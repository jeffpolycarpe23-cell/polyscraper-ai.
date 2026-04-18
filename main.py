from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()

# Ton design Pro (Version Multi-Liens)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PolyScraper AI v2.1 Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0b1120] text-white min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-[#171f2f] rounded-3xl shadow-2xl p-6 border border-slate-800">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-extrabold tracking-tight">🕵️‍♂️ PolyScraper <span class="text-blue-500">AI</span></h1>
            <p class="text-slate-400 text-xs mt-2 font-medium">L'extraction de données nouvelle génération.</p>
        </div>

        <form action="/extract" method="post" class="space-y-4">
            <textarea name="links" rows="4" required 
                class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 placeholder-slate-500 focus:border-blue-500 outline-none transition-all"
                placeholder="Collez vos liens Amazon ici..."></textarea>
            
            <button type="submit" 
                class="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-black py-4 rounded-2xl transition-all shadow-lg active:scale-95 uppercase">
                EXTRAIRE LES DONNÉES ⚡
            </button>
        </form>

        {% if results %}
        <div class="mt-8 animate-fade-in">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-4">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Rapport d'extraction</span>
                <span class="h-2 w-2 rounded-full bg-green-500"></span>
            </div>
            
            <div class="space-y-3 max-h-64 overflow-y-auto pr-2">
                {% for item in results %}
                <div class="bg-[#1e293b] p-4 rounded-2xl border border-slate-700/50">
                    <h3 class="text-blue-400 font-bold text-sm truncate">{{ item.nom }}</h3>
                    <div class="flex justify-between mt-2">
                        <span class="text-xs text-slate-400">🏷️ Prix : <span class="text-white font-bold">{{ item.prix }}</span></span>
                        <span class="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-500">Amazon</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    from jinja2 import Template
    return Template(HTML_TEMPLATE).render(request=request, results=None)

@app.post("/extract", response_class=HTMLResponse)
async def extract(request: Request, links: str = Form(...)):
    from jinja2 import Template
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Referer": "https://www.google.com/"
    }

    for url in list_links:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title_tag = soup.find("span", {"id": "productTitle"}) or soup.find("h1")
            title = title_tag.get_text().strip()[:40] if title_tag else "Produit trouvé"

            price = "Non trouvé"
            possible_prices = [
                soup.find("span", {"class": "a-offscreen"}),
                soup.find("span", {"class": "a-price-whole"}),
                soup.select_one(".a-price .a-offscreen")
            ]
            
            for p in possible_prices:
                if p:
                    price = p.get_text().strip()
                    break
            
            results.append({"nom": title, "prix": price})
        except:
            results.append({"nom": "Lien bloqué", "prix": "-"})
            
    return Template(HTML_TEMPLATE).render(request=request, results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
