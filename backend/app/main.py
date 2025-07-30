from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import json
import csv

from .config import (URL_CADASTROS, URL_CONSULTAS, URL_AGENDAMENTOS, CABECALHO_CONSULTAS)
from .routers import agenda_router, pessoas_router

def inicializar_arquivos():
    print("Verificando e inicializando arquivos de dados...")
    
    if not os.path.exists(URL_CADASTROS):
        with open(URL_CADASTROS, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print(f"Arquivo '{URL_CADASTROS}' criado.")

    if not os.path.exists(URL_CONSULTAS):
        with open(URL_CONSULTAS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO_CONSULTAS)
        print(f"Arquivo '{URL_CONSULTAS}' criado.")
        
    if not os.path.exists(URL_AGENDAMENTOS):
        with open(URL_AGENDAMENTOS, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print(f"Arquivo '{URL_AGENDAMENTOS}' criado.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializar_arquivos()
    yield
    print("Aplicação encerrada.")

app = FastAPI(lifespan=lifespan)

app.include_router(agenda_router.router)
app.include_router(pessoas_router.router)

@app.get("/")
def read_root():
    return {"message": "API da Clínica Virtual no ar!"}
