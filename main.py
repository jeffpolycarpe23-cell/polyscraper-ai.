import os
import io
import json
import requests
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
from bs4 import BeautifulSoup

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
SCRAPERANT_API_KEY = os.environ.get('SCRAPERANT_API_KEY')

def smart_scrape(url):
    """Récupère le texte propre d'une page."""
    # On force la localisation via ScrapingAnt si besoin (optionnel)
    api_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={SCRAPERANT_API_KEY}&browser=true"
    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for s in soup(['script', 'style', 'nav', 'footer', 'header']):
                s.decompose()
            return " ".join(soup.get_text().split())[:5000]
        return None
    except:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    # Récupération des liens (un par ligne)
    raw_links = request.form.get('urls_cibles', '').split('\n')
    links = [l.strip() for l in raw_links if l.strip().startswith('http')]
    
    if not links:
        return render_template('index.html', erreur="Aucun lien valide détecté.")

    resultats_finaux = []

    for url in links:
        contexte = smart_scrape(url)
        if contexte:
            try:
                response_ia = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Extraire en JSON : Produit, Prix, Marque, Caracteristiques (objet)."},
                        {"role": "user", "content": f"URL: {url}\nTexte: {contexte}"}
                    ],
                    response_format={ "type": "json_object" }
                )
                data = json.loads(response_ia.choices[0].message.content)
                # On ajoute l'URL pour que le client sache d'où vient la donnée
                data['Lien'] = url 
                resultats_finaux.append(data)
            except:
                continue

    return render_template('index.html', 
                           resultats=resultats_finaux, 
                           raw_json=json.dumps(resultats_finaux))

@app.route('/download-excel', methods=['POST'])
def download_excel():
    raw_data = request.form.get('raw_json')
    data_list = json.loads(raw_data)
    
    rows = []
    for item in data_list:
        details = item.pop('Caracteristiques', {})
        if not isinstance(details, dict): details = {"Details": str(details)}
        rows.append({**item, **details})

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Extraction_Multi_PolyScraper.xlsx')

if __name__ == '__main__':
    app.run(debug=True)
