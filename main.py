@app.route('/analyser', methods=['POST'])
def analyser():
    url = request.form.get('url_cible')
    if not url:
        return render_template('index.html', erreur="Veuillez entrer une URL.")

    try:
        # Headers plus complets pour "tromper" les protections
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        response_site = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response_site.content, 'html.parser')
        
        # On essaie de cibler le corps de la page pour éviter les menus inutiles
        main_content = soup.find('body')
        if main_content:
            for script_or_style in main_content(["script", "style", "nav", "footer"]):
                script_or_style.decompose()
            texte_site = main_content.get_text(separator=' ')
        else:
            texte_site = soup.get_text(separator=' ')

        contexte = " ".join(texte_site.split())[:4000]

        # On demande à l'IA d'être très précise même si les données sont denses
        response_ia = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un assistant qui extrait les données de vente. Si tu vois un prix (ex: 25.99$), un nom de produit ou une liste de caractéristiques, affiche-les clairement. Si tu ne trouves rien, résume ce que tu vois dans le texte."},
                {"role": "user", "content": f"Extrais le NOM, le PRIX et les CARACTÉRISTIQUES de ce texte : {contexte}"}
            ]
        )
        
        resultat = response_ia.choices[0].message.content
        return render_template('index.html', resultat=resultat, url=url)

    except Exception as e:
        return render_template('index.html', erreur=f"Erreur de lecture : {str(e)}")
