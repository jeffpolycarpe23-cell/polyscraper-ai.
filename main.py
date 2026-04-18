import os
import io
import json
import requests
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
from bs4 import BeautifulSoup

app = Flask(__name__)

# Initialisation des clients
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
SCRAPERANT_API_KEY = os.environ.get('SCRAPERANT_API_KEY')

def smart_scrape(url):
    """Récupère le texte et l'image du produit via ScrapingAnt."""
    api_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={SCRAPERANT_API_KEY}&browser=true"
    
    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 📸 tentative de trouver l'image principale (Amazon/Walmart)
            img_tag = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'data-search-image': 'true'}) or soup.find('meta', property='og:image')
            image_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else img_tag['content'] if img_tag and img_tag.has_attr('content') else None

            # Nettoyage du texte pour l'IA
            for s in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                s.decompose()
            texte_propre = " ".join(soup.get_text().split())[:5000]
            
            return texte_propre, image_url
        return f"Erreur {response.status_code}", None
    except Exception as e:
        return str(e), None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    url = request.form.get('url_cible')
    if not url:
        return render_template('index.html', erreur="Lien manquant.")

    contexte, image_produit = smart_scrape(url)

    if "Erreur" in contexte:
        return render_template('index.html', erreur=contexte)

    try:
        # 🧠 On demande à l'IA un format JSON strict
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un extracteur pro. Réponds UNIQUEMENT en JSON avec : Produit, Prix, Marque, Caracteristiques."},
                {"role": "user", "content": f"Données : {contexte}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        # On transforme la réponse texte en vrai dictionnaire Python
        donnees_json = json.loads(response_ia.choices[0].message.content)
        
        return render_template('index.html', 
                               resultat=donnees_json, 
                               image=image_produit, 
                               raw_json=json.dumps(donnees_json)) # Pour les boutons Excel
    except Exception as e:
        return render_template('index.html', erreur=f"Erreur : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    raw_data = request.form.get('raw_json')
    data = json.loads(raw_data)
    df = pd.DataFrame([data]) # Création automatique des colonnes
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Export_PolyScraper.xlsx')

@app.route('/download-csv', methods=['POST'])
def download_csv():
    raw_data = request.form.get('raw_json')
    data = json.loads(raw_data)
    df = pd.DataFrame([data])
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    return send_file(io.BytesIO(csv_data.encode()), mimetype='text/csv', as_attachment=True, download_name='Export_PolyScraper.csv')

if __name__ == '__main__':
    app.run(debug=True)
