from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import requests
from bs4 import BeautifulSoup
import os
import uvicorn
import re
import pandas as pd
import io

app = FastAPI()

# Mémoire pour les exports
latest_results = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PolyScraper AI v6.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .loader { border-top-color: #3b82f6; animation: spinner 1s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none; }
    </style>
</head>
<body class="bg-[#0b1120] text-white min-h-screen flex items-center justify-center p-4 font-sans">
    <div class="w-full max-w-md bg-[#171f2f] rounded-3xl shadow-2xl p-6 border border-slate-800">
        
        <div class="text-center mb-8">
            <h1 class="text-3xl font-extrabold tracking-tight italic">🕵️‍♂️ PolyScraper <span class="text-blue-500 underline">AI</span></h1>
            <p class="text-slate-400 text-[10px] mt-2 font-bold uppercase tracking-widest text-blue-300">Mode Force Brute : Walmart & Sony</p>
        </div>

        <form id="scrapeForm" action="/extract" method="post" class="space-y-4">
            <textarea name="links" rows="4" required 
                class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 outline-none focus:border-blue-500 transition-all"
                placeholder="Collez vos liens Walmart, Amazon, Sony ici..."></textarea>
            
            <button type="submit" id="btnSubmit"
                class="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-black py-4 rounded-2xl shadow-lg uppercase text-sm tracking-widest">
                FORCER L'EXTRACTION ⚡
            </button>
        </form>

        <div id="loading" class="hidden mt-8 text-center animate-pulse">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-slate-700 h-12 w-12 mb-4 mx-auto"></div>
            <p class="text-blue-400 text-[10px] font-bold uppercase tracking-widest">Contournement des pare-feu...</p>
        </div>

        {% if results %}
        <div class="mt-8 animate-fade-in">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-4">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest italic">Données Extraites</span>
                <div class="flex gap-3">
                    <a href="/download/excel" class="text-green-400 text-[10px] font-black hover:underline">EXCEL</a>
                    <a href="/download/csv" class="text-slate-400 text-[10px] font-black hover:underline">CSV</a>
                </div>
            </div>
            
            <div class="space-y-3 max-h-64 overflow-y-auto pr-2">
                {% for item in results %}
                <div class="bg-[#1e293b] p-4 rounded-2xl border border-slate-700/50">
                    <h3 class="text-blue-400 font-bold text-[11px] truncate">{{ item.nom }}</h3>
                    <div class="flex justify-between mt-2 items-center">
                        <span class="text-xs text-white font-black px-2 py-1 bg-blue-900/40 rounded-lg">🏷️ {{ item.prix }}</span>
                        <span class="text-[9px] text-slate-500 font-bold uppercase tracking-widest">{{ item.site }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        const form = document.getElementById('scrapeForm');
        form.onsubmit = () => {
            form.classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');
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
    global latest_results
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    api_token = "93663a8a07f04313b4e9f7831d3d63d8" 
    
    for url in list_links:
        try:
            domain = re.search(r'https?://(?:www\.)?([^./]+)', url)
            site_name = domain.group(1).upper() if domain else "WEB"

            # PARAMÈTRES DE FORCE : Browser + IP Résidentielle (indétectable)
            ant_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={api_token}&browser=true&proxy_type=residential"
            
            res = requests.get(ant_url, timeout=55)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. Extraction du Titre
            title = soup.title.string.strip()[:40] if soup.title else "Produit trouvé"

            # 2. ALGORITHME DE PRIX AVANCÉ (Scanner de texte)
            price = "Non détecté"
            
            # On cherche partout où il y a un chiffre suivi de $, € ou USD
            potential_prices = soup.find_all(string=re.compile(r'[0-9](?:[.,][0-9]{2})?[\s]?[€$]|USD'))
            
            for p in potential_prices:
                clean_p = p.strip()
                # On vérifie que c'est bien un prix (court) et pas un long paragraphe
                if 2 < len(clean_p) < 15:
                    price = clean_p
                    break
            
            results.append({"nom": title, "prix": price, "site": site_name})
        except:
            results.append({"nom": "Lien protégé", "prix": "Bloqué", "site": site_name})
            
    latest_results = results
    return Template(HTML_TEMPLATE).render(request=request, results=results)

@app.get("/download/{file_type}")
async def download(file_type: str):
    if not latest_results: return {"error": "No data"}
    df = pd.DataFrame(latest_results)
    if file_type == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=PolyScraper_Data.xlsx"})
    else:
        csv_data = df.to_csv(index=False)
        return StreamingResponse(io.StringIO(csv_data), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=PolyScraper_Data.csv"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
