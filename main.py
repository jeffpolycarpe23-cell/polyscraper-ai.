import os
import io
import requests
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
from bs4 import BeautifulSoup

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
SCRAPERANT_API_KEY = os.environ.get('SCRAPERANT_API_KEY')

def smart_scrape(url):
    """Utilise l'API ScrapingAnt pour débloquer Amazon/Walmart."""
    # Note l'URL de l'API avec 'v2'
    api_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={SCRAPERANT_API_KEY}&browser=true"
    
    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for s in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                s.decompose()
            return " ".join(soup.get_text().split())[:5000]
        else:
            return f"Erreur de déblocage (Code {response.status_code})"
    except Exception as e:
        return f"Erreur réseau : {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    url = request.form.get('url_cible')
    if not url:
        return render_template('index.html', erreur="Veuillez entrer un lien.")

    contexte = smart_scrape(url)

    if "Erreur" in contexte:
        return render_template('index.html', erreur=contexte)

    try:
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un extracteur pro. Réponds en Markdown : ### Produit, **Prix**, et Caractéristiques."},
                {"role": "user", "content": f"Analyse ceci : {contexte}"}
            ]
        )
        resultat = response_ia.choices[0].message.content
        return render_template('index.html', resultat=resultat)
    except Exception as e:
        return render_template('index.html', erreur=f"Erreur IA : {str(e)}")

# --- Garde ici tes fonctions download-excel et download-csv ---

if __name__ == '__main__':
    app.run(debug=True)
