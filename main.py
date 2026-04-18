import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
import io

app = Flask(__name__)

# Configuration OpenAI
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
        # 1. On va chercher le contenu du site (Le Scraping)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response_site = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response_site.content, 'html.parser')
        
        # On extrait le texte et on nettoie un peu
        for script in soup(["script", "style"]):
            script.extract()
        texte_site = soup.get_text()
        # On prend les 3000 premiers caractères pour ne pas dépasser les limites
        contexte = " ".join(texte_site.split())[:3000]

        # 2. On envoie ce texte à l'IA avec une mission précise
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un extracteur de données professionnel. Ton but est de trouver le NOM DU PRODUIT, le PRIX, et de faire une LISTE des caractéristiques importantes à partir du texte fourni."},
                {"role": "user", "content": f"Voici le texte du site : {contexte}"}
            ]
        )
        
        resultat = response_ia.choices[0].message.content
        return render_template('index.html', resultat=resultat, url=url)

    except Exception as e:
        return render_template('index.html', erreur=f"Détail de l'erreur : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    contenu = request.form.get('resultat_ia', '')
    df = pd.DataFrame([{"Analyse PolyScraper": contenu}])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Analyse_PolyScraper.xlsx')

@app.route('/download-csv', methods=['POST'])
def download_csv():
    contenu = request.form.get('resultat_ia', '')
    df = pd.DataFrame([{"Analyse PolyScraper": contenu}])
    output = io.BytesIO()
    csv_data = df.to_csv(index=False, encoding='utf-8')
    return send_file(io.BytesIO(csv_data.encode()), mimetype='text/csv', as_attachment=True, download_name='Analyse_PolyScraper.csv')

if __name__ == '__main__':
    app.run(debug=True)
