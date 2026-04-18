from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()

# Ton design avec barre de chargement et boutons exports
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PolyScraper AI v3.0 Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .loader { border-top-color: #3b82f6; animation: spinner 1.5s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none; }
    </style>
</head>
<body class="bg-[#0b1120] text-white min-h-screen flex items-center justify-center p-4 font-sans">
    <div class="w-full max-w-md bg-[#171f2f] rounded-3xl shadow-2xl p-6 border border-slate-800">
        
        <div class="text-center mb-8">
            <h1 class="text-3xl font-extrabold tracking-tight italic">🕵️‍♂️ PolyScraper <span class="text-blue-500 underline">AI</span></h1>
            <p class="text-slate-400 text-[10px] mt-2 font-bold uppercase tracking-widest">L'extraction de données nouvelle génération</p>
        </div>

        <form id="scrapeForm" action="/extract" method="post" class="space-y-4">
            <textarea name="links" rows="4" required 
                class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 placeholder-slate-500 focus:border-blue-500 outline-none transition-all"
                placeholder="Collez vos liens Amazon ici (un par ligne)..."></textarea>
            
            <button type="submit" id="btnSubmit"
                class="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-black py-4 rounded-2xl transition-all shadow-lg active:scale-95 uppercase text-sm tracking-widest">
                GÉNÉRER LES DONNÉES ⚡
            </button>
        </form>

        <div id="loading" class="hidden mt-8 text-center animate-pulse">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-slate-700 h-12 w-12 mb-4 mx-auto"></div>
            <p class="text-blue-400 text-xs font-bold uppercase tracking-widest">Recherche en cours sur Amazon...</p>
            <p class="text-slate-500 text-[10px] mt-1">Analyse des prix via PolyScraper Bot</p>
        </div>

        {% if results %}
        <div class="mt-8 animate-fade-in">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-4">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest italic">Rapport d'extraction</span>
                <div class="flex gap-2">
                    <button class="text-[9px] bg-green-900/30 text-green-400 border border-green-800 px-2 py-1 rounded-md font-bold hover:bg-green-800 hover:text-white transition">EXCEL</button>
                    <button class="text-[9px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-1 rounded-md font-bold hover:bg-slate-700 transition">CSV</button>
                </div>
            </div>
            
            <div class="space-y-3 max-h-64 overflow-y-auto pr-2 custom-scrollbar">
                {% for item in results %}
                <div class="bg-[#1e293b] p-4 rounded-2xl border border-slate-700/50 hover:border-blue-500/50 transition-colors">
                    <h3 class="text-blue-400 font-bold text-xs truncate">{{ item.nom }}</h3>
                    <div class="flex justify-between mt-2 items-center">
                        <span class="text-xs text-white font-black px-2 py-1 bg-blue-900/50 rounded-lg">🏷️ {{ item.prix }}</span>
                        <span class="text-[9px] text-slate-500 font-bold">SOURCE: AMAZON</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <p class="text-center text-[9px] text-slate-600 mt-8 font-medium italic">PolyScraper AI - Dashboard de Contrôle v3.0</p>
    </div>

    <script>
        const form = document.getElementById('scrapeForm');
        const loading = document.getElementById('loading');
        const btn = document.getElementById('btnSubmit');

        form.onsubmit = function() {
            form.classList.add('hidden');
            loading.classList.remove('hidden');
        };
    </script>
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
    
    # --- TA CLÉ SCRAPINGANT ICI ---
    # Je mets celle de ta capture d'écran pour t'aider
    api_token = "93663a8a07f04313b4e9f7831d3d63d8" 
    
    for url in list_links:
        try:
            # Utilisation de ScrapingAnt pour éviter les blocages
            ant_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={api_token}&browser=false"
            res = requests.get(ant_url, timeout=25)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Extraction du titre
            title_tag = soup.find("span", {"id": "productTitle"}) or soup.find("h1")
            title = title_tag.get_text().strip()[:35] + "..." if title_tag else "Produit Amazon"

            # Extraction du prix
            price = "Vérifier prix"
            possible_prices = [
                soup.find("span", {"class": "a-offscreen"}),
                soup.find("span", {"class": "a-price-whole"}),
                soup.select_one(".a-price .a-offscreen")
            ]
            
            for p in possible_prices:
                if p:
                    price = p.get_text().strip()
                    if "," in price or "." in price: # Vérifie que c'est bien un prix
                        break
            
            results.append({"nom": title, "prix": price})
        except:
            results.append({"nom": "Lien restreint", "prix": "-"})
            
    return Template(HTML_TEMPLATE).render(request=request, results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
