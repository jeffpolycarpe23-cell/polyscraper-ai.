import os
import io
import asyncio
from flask import Flask, render_template, request, send_file
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from openai import OpenAI
import pandas as pd
from bs4 import BeautifulSoup

app = Flask(__name__)

# Initialisation OpenAI
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def force_scrape(url):
    """Utilise Playwright pour débloquer Amazon, Walmart et les sites complexes."""
    with sync_playwright() as p:
        # Lancement du navigateur
        browser = p.chromium.launch(headless=True)
        # On simule un vrai utilisateur iPhone/Mac
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Mode furtif pour éviter les blocages
        stealth_sync(page)
        
        try:
            # On charge la page (on attend que le réseau soit calme)
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Petit délai pour laisser les prix s'afficher (comme un humain qui regarde)
            page.wait_for_timeout(3000)
            
            # On récupère le contenu HTML
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # On nettoie les éléments inutiles
            for s in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
                s.decompose()
            
            # On extrait le texte propre
            texte = " ".join(soup.get_text(separator=' ').split())
            return texte[:5000] # On limite pour ne pas saturer l'IA
            
        except Exception as e:
            return f"Erreur lors de la lecture du site : {str(e)}"
        finally:
            browser.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    url = request.form.get('url_cible')
    if not url:
        return render_template('index.html', erreur="Veuillez entrer une URL valide.")

    # On utilise la méthode "Puissance" par défaut pour garantir le résultat
    contexte = force_scrape(url)

    if "Erreur lors de la lecture" in contexte:
        return render_template('index.html', erreur=contexte)

    try:
        # L'IA transforme le texte brut en rapport propre
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en extraction. Réponds en Markdown : ### Nom du produit, **Prix**, et une liste des caractéristiques techniques."},
                {"role": "user", "content": f"Analyse ces données : {contexte}"}
            ]
        )
        resultat = response_ia.choices[0].message.content
        return render_template('index.html', resultat=resultat)
    
    except Exception as e:
        return render_template('index.html', erreur=f"Erreur IA : {str(e)}")

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
