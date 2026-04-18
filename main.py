from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import os
import uvicorn
import re

app = FastAPI()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PolyScraper AI v4.0</title>
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
            <p class="text-slate-400 text-[10px] mt-2 font-bold uppercase tracking-widest text-blue-300">Scraper Universel Multi-Sites</p>
        </div>

        <form id="scrapeForm" action="/extract" method="post" class="space-y-4">
            <textarea name="links" rows="4" required 
                class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 outline-none focus:border-blue-500 transition-all"
                placeholder="Collez vos liens (Amazon, Sony, eBay...) ici..."></textarea>
            
            <button type="submit" id="btnSubmit"
                class="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-black py-4 rounded-2xl shadow-lg uppercase text-sm tracking-widest">
                ANALYSER LES SITES ⚡
            </button>
        </form>

        <div id="loading" class="hidden mt-8 text-center animate-pulse">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-slate-700 h-12 w-12 mb-4 mx-auto"></div>
            <p class="text-blue-400 text-xs font-bold uppercase tracking-widest">Extraction en cours...</p>
        </div>

        {% if results %}
        <div class="mt-8 animate-fade-in">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2 mb-4">
                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Rapport Global</span>
                <div class="flex gap-2 text-[9px] font-bold">
                    <span class="text-green-400 cursor-pointer hover:underline">EXPORT EXCEL</span>
                    <span class="text-slate-400 cursor-pointer hover:underline">CSV</span>
                </div>
            </div>
            
            <div class="space-y-3 max-h-64 overflow-y-auto pr-2">
                {% for item in results %}
                <div class="bg-[#1e293b] p-4 rounded-2xl border border-slate-700/50">
                    <h3 class="text-blue-400 font-bold text-xs truncate">{{ item.nom }}</h3>
                    <div class="flex justify-between mt-2 items-center">
                        <span class="text-xs text-white font-black px-2 py-1 bg-blue-900/50 rounded-lg">🏷️ {{ item.prix }}</span>
                        <span class="text-[9px] text-slate-500 font-bold uppercase">{{ item.site }}</span>
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
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    api_token = "93663a8a07f04313b4e9f7831d3d63d8" 
    
    for url in list_links:
        try:
            # Extraction du nom du site (Sony, Amazon, etc.)
            domain = re.search(r'https?://(?:www\.)?([^./]+)', url)
            site_name = domain.group(1).upper() if domain else "SITE WEB"

            ant_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={api_token}&browser=false"
            res = requests.get(ant_url, timeout=25)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Titre universel
            title = soup.title.string.strip()[:35] + "..." if soup.title else "Page Web"

            # Logique de prix universelle (cherche le symbole € ou $)
            price = "Non détecté"
            # On cherche tous les textes qui ressemblent à un prix
            for text in soup.find_all(string=re.compile(r'[0-9](?:[.,][0-9]{2})?[\s]?[€$]')):
                if len(text.strip()) < 15: # Un prix n'est pas une longue phrase
                    price = text.strip()
                    break
            
            results.append({"nom": title, "prix": price, "site": site_name})
        except:
            results.append({"nom": "Lien bloqué", "prix": "-", "site": "ERREUR"})
            
    return Template(HTML_TEMPLATE).render(request=request, results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
