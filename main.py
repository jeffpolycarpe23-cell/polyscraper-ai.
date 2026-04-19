from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
import requests
import os
import uvicorn
import re
import pandas as pd
import io

app = FastAPI()
latest_results = []

# --- TA CLÉ ZENROWS EST INTÉGRÉE ICI ---
ZENROWS_API_KEY = "abb87e1d8fe422150deb64f9ccb70702a6838b02" 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PolyScraper AI v7.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .loader { border-top-color: #3b82f6; animation: spinner 1s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-[#0b1120] text-white min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md bg-[#171f2f] rounded-3xl shadow-2xl p-6 border border-slate-800">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-extrabold italic text-white">🕵️‍♂️ PolyScraper <span class="text-blue-500 underline">AI</span></h1>
            <p class="text-blue-300 text-[10px] font-bold uppercase tracking-widest mt-2">Moteur Industriel Infaillible</p>
        </div>

        <form id="scrapeForm" action="/extract" method="post" class="space-y-4">
            <textarea name="links" rows="4" required 
                class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 outline-none focus:border-blue-500 transition-all"
                placeholder="Collez vos liens Walmart, Sony, Amazon ici..."></textarea>
            
            <button type="submit" class="w-full bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-black py-4 rounded-2xl shadow-lg uppercase text-sm tracking-widest active:scale-95 transition-all">
                LANCER L'EXTRACTION ⚡
            </button>
        </form>

        <div id="loading" class="hidden mt-8 text-center animate-pulse">
            <div class="loader ease-linear rounded-full border-4 border-t-4 border-slate-700 h-12 w-12 mb-4 mx-auto"></div>
            <p class="text-blue-400 text-[10px] font-bold uppercase">Simulation humaine (Anti-blocage)...</p>
        </div>

        {% if results %}
        <div class="mt-8">
            <div class="flex justify-between border-b border-slate-800 pb-2 mb-4">
                <span class="text-[10px] text-slate-500 font-bold uppercase">Rapport de Données</span>
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
                        <span class="text-xs text-white font-black px-2 py-1 bg-blue-900/40 rounded-lg italic">🏷️ {{ item.prix }}</span>
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
    global latest_results
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    
    zenrows_url = "https://api.zenrows.com/v1/"

    for url in list_links:
        try:
            # Paramètres de Force Brute ZenRows
            params = {
                "apikey": ZENROWS_API_KEY,
                "url": url,
                "js_render": "true",        # Exécute le JavaScript (pour Walmart)
                "premium_proxy": "true",    # IP Résidentielle indétectable
                "wait_for": ".price, [class*='price'], span" # Attend le chargement du prix
            }
            
            response = requests.get(zenrows_url, params=params, timeout=60)
            html_content = response.text
            
            # Extraction du Titre
            title_match = re.search(r'<title>(.*?)</title>', html_content)
            title = title_match.group(1)[:30].strip() if title_match else "Produit trouvé"

            # Extraction du Prix (Scan des symboles monétaires)
            price_match = re.search(r'([$€]\s?\d+[.,]\d{2})|(\d+[.,]\d{2}\s?[$€])', html_content)
            price = price_match.group(0) if price_match else "Non détecté"
            
            site = "WALMART" if "walmart" in url.lower() else "SONY" if "sony" in url.lower() else "AMAZON" if "amazon" in url.lower() else "WEB"
            results.append({"nom": title, "prix": price, "site": site, "url": url})
        except:
            results.append({"nom": "Lien protégé", "prix": "Bloqué", "site": "ERREUR", "url": url})
            
    latest_results = results
    return Template(HTML_TEMPLATE).render(request=request, results=results)

@app.get("/download/{file_type}")
async def download(file_type: str):
    if not latest_results: return {"error": "No data"}
    df = pd.DataFrame(latest_results)
    output = io.BytesIO()
    if file_type == "excel":
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
