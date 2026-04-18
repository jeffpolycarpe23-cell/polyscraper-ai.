from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os
import uvicorn
import io

app = FastAPI()

# --- CONFIGURATION CRUCIALE POUR ÉVITER L'ÉCRAN BLANC ---
# 1. Montage des fichiers statiques (CSS/JS) s'ils existent
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Configuration des templates HTML
templates = Jinja2Templates(directory="templates")

# --- MOTEUR DE SCRAPING OPTIMISÉ (AVEC HEADERS IPHONE) ---
def scrape_amazon_product(url):
    """Extrait le nom et le prix d'un produit Amazon."""
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sélecteurs les plus communs pour Amazon (peuvent changer)
        title_element = soup.find("span", {"id": "productTitle"})
        price_element = soup.find("span", {"class": "a-offscreen"}) or soup.find("span", {"id": "priceblock_ourprice"})
        
        product_name = title_element.get_text().strip() if title_element else "Produit introuvable"
        product_price = price_element.get_text().strip() if price_element else "Prix non affiché"
        
        return {
            "nom": product_name,
            "prix": product_price,
            "marque": "Amazon"
        }
    except Exception as e:
        print(f"Erreur de scraping : {e}")
        return None

# --- ROUTES DE L'APPLICATION ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Affiche ton interface superbe instantanément."""
    # Cette route charge ton fichier HTML de base (celui de tes photos)
    # Assure-toi d'avoir un fichier 'index.html' dans un dossier 'templates'
    return templates.TemplateResponse("index.html", {"request": request, "product": None})

@app.post("/extract", response_class=HTMLResponse)
async def extract_data(request: Request, url: str = Form(...)):
    """Gère l'extraction quand tu cliques sur 'Extraire les données'."""
    # 1. L'interface reste affichée (pas d'écran blanc)
    # 2. Le scraping se fait en arrière-plan
    product_data = scrape_amazon_product(url)
    
    if not product_data:
        product_data = {"nom": "Erreur", "prix": "Lien invalide ou bloqué", "marque": "None"}

    # 3. On renvoie la même page mais avec les données remplies
    return templates.TemplateResponse("index.html", {"request": request, "product": product_data})

@app.get("/download/excel")
async def download_excel():
    """Génère et télécharge le fichier Excel (basé sur la dernière extraction)."""
    # Pour l'instant, c'est une version simplifiée. Il faudrait stocker
    # les données de la dernière extraction en session pour faire un vrai export.
    data = [{"Nom": "Exemple Produit", "Prix": "19.99€", "Marque": "Amazon"}]
    df = pd.DataFrame(data)
    
    # Création du fichier Excel en mémoire
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Produits')
    output.seek(0)
    
    return FileResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="polyscraper_export.xlsx")

# --- DÉMARRAGE OPTIMISÉ POUR RENDER/IPHONE ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    # reload=False est crucial pour la stabilité sur Render Free
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, workers=1)
