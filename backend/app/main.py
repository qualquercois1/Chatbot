import os
import csv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import (URL_CADASTROS, URL_CONSULTAS, CABECALHO_CADASTROS, CABECALHO_CONSULTAS, BASE_DIR)
from .routers import agenda_router, pessoas_router

def inicializar_arquivos():
    print("Verificando e inicializando arquivos de dados...")
    data_dir = BASE_DIR / "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    if not os.path.exists(URL_CADASTROS):
        with open(URL_CADASTROS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO_CADASTROS)
    
    if not os.path.exists(URL_CONSULTAS):
        with open(URL_CONSULTAS, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO_CONSULTAS)
    print("Inicialização concluída.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializar_arquivos()
    yield

app = FastAPI(
    title="API de Agendamentos (Refatorada)",
    description="API para gerenciar horários, cadastros e consultas com arquitetura OOP.",
    version="2.0.0",
    lifespan=lifespan 
)

app.include_router(agenda_router.router)
app.include_router(pessoas_router.router)

@app.get("/", tags=["Root"])
def home():
    return {"status": "API Refatorada está online!"}