from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Variable pour stocker les résultats temporairement
resultats_extraction = {}

def scraping_logic(job_id, links):
    """Fonction qui fait le travail lourd en arrière-plan"""
    temp_results = []
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"}
    
    for url in links:
        try:
            # On simule l'extraction
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            titre = soup.find('title').text if soup.find('title') else "Sans titre"
            temp_results.append({"url": url, "titre": titre})
        except Exception as e:
            temp_results.append({"url": url, "error": str(e)})
        
    # On sauvegarde le résultat final
    resultats_extraction[job_id] = temp_results

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extract")
async def extract(request: Request, background_tasks: BackgroundTasks):
    data = await request.form()
    links = data.get("links").splitlines() # Récupère les liens du textarea
    job_id = str(time.time()) # Identifiant unique pour cette session
    
    # LANCE LE SCRAPING EN ARRIÈRE-PLAN
    background_tasks.add_task(scraping_logic, job_id, links)
    
    return {"status": "en_cours", "message": "L'extraction a commencé !", "id": job_id}
