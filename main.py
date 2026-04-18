from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import requests
from bs4 import BeautifulSoup
import os
import uvicorn

app = FastAPI()

# Ton interface HTML est maintenant directement ici
HTML_CONTENT = """
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
            <p class="text-slate-400 text-xs mt-2">Extraction multi-liens Pro</p>
        </div>

        <form action="/extract" method="post" class="space-y-4">
            <textarea name="links" rows="4" required class="w-full bg-[#0f172a] border-2 border-slate-700 rounded-2xl p-4 text-sm text-blue-100 outline-none focus:border-blue-500" placeholder="Collez vos liens ici..."></textarea>
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-2xl transition-all uppercase">EXTRAIRE LES DONNÉES ⚡</button>
        </form>

        {% if results %}
        <div class="mt-8 space-y-3">
            <p class="text-[10px] font-bold text-slate-500 uppercase">Résultats :</p>
            {% for item in results %}
            <div class="bg-[#1e293b] p-3 rounded-xl border border-slate-700">
                <p class="text-blue-400 text-sm font-bold truncate">{{ item.nom }}</p>
                <p class="text-xs text-white">Prix : {{ item.prix }}</p>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    # On utilise une version simple sans Jinja2Templates pour éviter l'erreur de dossier
    from jinja2 import Template
    return Template(HTML_CONTENT).render(results=None)

@app.post("/extract", response_class=HTMLResponse)
async def extract(links: str = Form(...)):
    from jinja2 import Template
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}

    for url in list_links:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            title = soup.title.string[:40] if soup.title else "Produit"
            # On cherche le prix
            price_tag = soup.find("span", {"class": "a-offscreen"}) or soup.find("span", {"class": "a-price-whole"})
            price = price_tag.get_text().strip() if price_tag else "Non trouvé"
            results.append({"nom": title, "prix": price})
        except:
            results.append({"nom": "Erreur lien", "prix": "-"})
            
    return Template(HTML_CONTENT).render(results=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
