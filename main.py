import os
from flask import Flask, render_template, request, send_file
from openai import OpenAI  # Nouvelle façon d'importer
import pandas as pd
import io

app = Flask(__name__)

# Nouvelle configuration de l'IA
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
        # Nouvelle façon d'appeler l'IA (version 1.0.0+)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # On utilise le modèle le plus récent et rapide
            messages=[
                {"role": "system", "content": "Tu es un expert en analyse de sites web."},
                {"role": "user", "content": f"Analyse cette URL et fais un résumé court : {url}"}
            ]
        )
        resultat = response.choices[0].message.content
        return render_template('index.html', resultat=resultat, url=url)
    except Exception as e:
        # Ce message s'affichera si l'IA bloque encore
        return render_template('index.html', erreur=f"Détail de l'erreur : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    contenu = request.form.get('resultat_ia', '')
    if not contenu:
        return "Erreur", 400
    
    try:
        df = pd.DataFrame([{"Analyse": contenu}])
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Analyse.xlsx')
    except Exception as e:
        return f"Erreur Excel : {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
