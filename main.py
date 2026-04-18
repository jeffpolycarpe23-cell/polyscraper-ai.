from fastapi import FastAPI
import os
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Polyscraper-AI fonctionne correctement",
        "platform": "Render Free Tier"
    }

@app.get("/scrape")
def test_scrape():
    # C'est ici que nous ajouterons la logique BeautifulSoup plus tard
    return {"message": "Module de scraping prêt pour configuration"}

if __name__ == "__main__":
    # Configuration cruciale pour Render
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, workers=1)
