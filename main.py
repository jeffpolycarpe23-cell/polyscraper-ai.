import os
import io
import json
import requests
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
from bs4 import BeautifulSoup

app = Flask(__name__)

# Initialisation des API
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
SCRAPERANT_API_KEY = os.environ.get('SCRAPERANT_API_KEY')

def smart_scrape(url):
    """Récupère le texte et l'image du produit."""
    api_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={SCRAPERANT_API_KEY}&browser=true"
    
    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche de l'image (Amazon, Walmart, etc.)
            img_tag = soup.find('img', {'id': 'landingImage'}) or \
                      soup.find('img', {'data-search-image': 'true'}) or \
                      soup.find('meta', property='og:image')
            
            image_url = None
            if img_tag:
                image_url = img_tag.get('src') or img_tag.get('content')

            # Nettoyage du texte
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
        # IA avec format JSON strict
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un extracteur pro. Réponds UNIQUEMENT en JSON avec ces clés : Produit, Prix, Marque, Caracteristiques (sous forme d'objet JSON)."},
                {"role": "user", "content": f"Données : {contexte}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        donnees_json = json.loads(response_ia.choices[0].message.content)
        
        return render_template('index.html', 
                               resultat=donnees_json, 
                               image=image_produit, 
                               raw_json=json.dumps(donnees_json))
    except Exception as e:
        return render_template('index.html', erreur=f"Erreur IA : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    raw_data = request.form.get('raw_json')
    data = json.loads(raw_data)
    
    # Transformation : On transforme l'objet 'Caracteristiques' en colonnes Excel
    details = data.pop('Caracteristiques', {})
    if not isinstance(details, dict):
        details = {"Info": str(details)}
    
    # Fusion des données simples et des détails
    row_final = {**data, **details}
    df = pd.DataFrame([row_final])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    return send_file(output, 
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                     as_attachment=True, 
                     download_name='Rapport_PolyScraper.xlsx')

@app.route('/download-csv', methods=['POST'])
def download_csv():
    raw_data = request.form.get('raw_json')
    data = json.loads(raw_data)
    
    details = data.pop('Caracteristiques', {})
    if not isinstance(details, dict):
        details = {"Info": str(details)}
    
    row_final = {**data, **details}
    df = pd.DataFrame([row_final])
    
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    return send_file(io.BytesIO(csv_data.encode()), 
                     mimetype='text/csv', 
                     as_attachment=True, 
                     download_name='Rapport_PolyScraper.csv')

if __name__ == '__main__':
    app.run(debug=True)
