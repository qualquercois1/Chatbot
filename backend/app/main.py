# app/main.py
import os
import csv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import (URL_CADASTROS, URL_CONSULTAS, CABECALHO_CADASTROS, 
                     CABECALHO_CONSULTAS, BASE_DIR)
from .routers import agenda_router, pessoas_router

# Função para rodar na inicialização da API
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

# Gerenciador de contexto de "vida" da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado antes da aplicação iniciar
    inicializar_arquivos()
    yield
    # Código a ser executado quando a aplicação estiver desligando (se necessário)

app = FastAPI(
    title="API de Agendamentos (Refatorada)",
    description="API para gerenciar horários, cadastros e consultas com arquitetura OOP.",
    version="2.0.0",
    lifespan=lifespan # Associa o gerenciador de vida à aplicação
)

# Inclui os routers
app.include_router(agenda_router.router)
app.include_router(pessoas_router.router)

@app.get("/", tags=["Root"])
def home():
    return {"status": "API Refatorada está online!"}