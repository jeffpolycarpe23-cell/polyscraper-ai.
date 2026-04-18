@app.post("/extract", response_class=HTMLResponse)
async def extract(links: str = Form(...)):
    from jinja2 import Template
    list_links = [l.strip() for l in links.split("\n") if l.strip()]
    results = []
    
    # Headers plus complets pour simuler un vrai navigateur
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "DNT": "1"
    }

    for url in list_links:
        try:
            # On utilise une session pour garder les cookies (plus humain)
            session = requests.Session()
            res = session.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')
            
            title = soup.title.string[:40] if soup.title else "Produit"
            
            # Liste de TOUTES les balises possibles pour le prix sur Amazon
            price = "Non trouvé"
            selectors = [
                "span.a-offscreen", 
                "span.a-price-whole", 
                "span#priceblock_ourprice", 
                "span#priceblock_dealprice",
                "span.a-price.a-text-price span.a-offscreen"
            ]
            
            for selector in selectors:
                found = soup.select_one(selector)
                if found:
                    price = found.get_text().strip()
                    break
            
            results.append({"nom": title, "prix": price})
        except:
            results.append({"nom": "Erreur connexion", "prix": "-"})
            
    return Template(HTML_CONTENT).render(results=results)
