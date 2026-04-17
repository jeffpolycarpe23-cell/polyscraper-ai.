import os
from flask import Flask, render_template, request, send_file
import openai
import pandas as pd
import io
from fpdf import FPDF

app = Flask(__name__)

# Configuration OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyser', methods=['POST'])
def analyser():
    # CORRECTION ICI : On utilise 'url_cible' pour correspondre à ton HTML
    url = request.form.get('url_cible')
    
    if not url:
        return render_template('index.html', erreur="Veuillez entrer une URL valide.")

    try:
        # Appel à l'IA pour simuler l'extraction (ou scraping réel selon ton code)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un expert en extraction de données web."},
                {"role": "user", "content": f"Analyse cette URL et donne-moi un résumé des produits ou informations clés : {url}"}
            ]
        )
        resultat = response.choices[0].message.content
        return render_template('index.html', resultat=resultat, url=url)
    except Exception as e:
        return render_template('index.html', erreur=f"Erreur lors de l'analyse : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    contenu = request.form.get('resultat_ia', '')
    if not contenu:
        return "Erreur", 400
    
    try:
        # Version stable pour iPhone : une seule grande case
        df = pd.DataFrame([{"Analyse PolyScraper AI": contenu}])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Extraction')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Extraction_PolyScraper.xlsx'
        )
    except Exception as e:
        return f"Erreur Excel : {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
