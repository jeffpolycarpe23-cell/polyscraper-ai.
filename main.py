import os
from flask import Flask, render_template, request, send_file
from openai import OpenAI
import pandas as pd
import io

app = Flask(__name__)

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en analyse de données."},
                {"role": "user", "content": f"Analyse cette URL et fais un résumé : {url}"}
            ]
        )
        resultat = response.choices[0].message.content
        return render_template('index.html', resultat=resultat, url=url)
    except Exception as e:
        return render_template('index.html', erreur=f"Erreur : {str(e)}")

@app.route('/download-excel', methods=['POST'])
def download_excel():
    contenu = request.form.get('resultat_ia', '')
    df = pd.DataFrame([{"Analyse": contenu}])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='Analyse.xlsx')

@app.route('/download-csv', methods=['POST'])
def download_csv():
    contenu = request.form.get('resultat_ia', '')
    df = pd.DataFrame([{"Analyse": contenu}])
    output = io.BytesIO()
    # On transforme le tableau en texte CSV
    csv_data = df.to_csv(index=False, encoding='utf-8')
    return send_file(io.BytesIO(csv_data.encode()), mimetype='text/csv', as_attachment=True, download_name='Analyse.csv')

if __name__ == '__main__':
    app.run(debug=True)
