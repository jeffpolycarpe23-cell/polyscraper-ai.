import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
import io

app = Flask(__name__)

# Initialisation du client OpenAI avec la clé cachée dans Render
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    url = request.form.get('url_cible')
    if not url:
        return render_template('index.html', erreur="Veuillez entrer une URL.")

    try:
        # 1. SCRAPING : On va chercher le texte sur le site
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response_site = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response_site.content, 'html.parser')
        
        # Nettoyage du texte
        for s in soup(['script', 'style', 'nav', 'footer']):
            s.decompose()
        texte_brut = soup.get_text(separator=' ')
        contexte = " ".join(texte_brut.split())[:4000]

        # 2. IA : Analyse et formatage Premium
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un extracteur pro. Réponds en Markdown : ### pour le TITRE, ** ** pour le PRIX en gras, et une liste pour les CARACTÉRISTIQUES."},
                {"role": "user", "content": f"Extrais les infos de ce texte : {contexte}"}
            ]
        )
        
        resultat = response_ia.choices[0].message.content
        return render_template('index.html', resultat=resultat, url=url)

    except Exception as e:
        return render_template('index.html', erreur=f"Erreur : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    contenu = request.form.get('resultat_ia', '')
    df = pd.DataFrame([{"Données Extraites": contenu}])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Analyse_PolyScraper.xlsx')

@app.route('/download-csv', methods=['POST'])
def download_csv():
    contenu = request.form.get('resultat_ia', '')
    df = pd.DataFrame([{"Données Extraites": contenu}])
    output = io.BytesIO()
    csv_data = df.to_csv(index=False, encoding='utf-8')
    return send_file(io.BytesIO(csv_data.encode()), mimetype='text/csv', as_attachment=True, download_name='Analyse_PolyScraper.csv')

if __name__ == '__main__':
    app.run(debug=True)
