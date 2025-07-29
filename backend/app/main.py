# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import os
import json
import csv

# Importa as variáveis de configuração e os routers
# Não precisamos mais do BASE_DIR aqui, pois os caminhos já vêm completos
from .config import (URL_CADASTROS, URL_CONSULTAS, URL_AGENDAMENTOS, CABECALHO_CONSULTAS)
from .routers import agenda_router, pessoas_router

def inicializar_arquivos():
    """Verifica e cria os arquivos de dados se eles não existirem."""
    print("Verificando e inicializando arquivos de dados...")
    
    # A pasta 'data' já é criada pelo config.py, então a lógica aqui foi simplificada.

    # Verifica e cria o arquivo de cadastros (pessoas.json)
    if not os.path.exists(URL_CADASTROS):
        with open(URL_CADASTROS, 'w', encoding='utf-8') as f:
            json.dump({}, f) # Cria um JSON vazio
        print(f"Arquivo '{URL_CADASTROS}' criado.")

    # Verifica e cria o arquivo de consultas (pessoa_horario.csv)
    if not os.path.exists(URL_CONSULTAS):
        with open(URL_CONSULTAS, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CABECALHO_CONSULTAS)
        print(f"Arquivo '{URL_CONSULTAS}' criado.")
        
    # Verifica e cria o arquivo de agendamentos (agendamentos.json)
    if not os.path.exists(URL_AGENDAMENTOS):
        with open(URL_AGENDAMENTOS, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print(f"Arquivo '{URL_AGENDAMENTOS}' criado.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Função de ciclo de vida para executar na inicialização."""
    inicializar_arquivos()
    yield
    # Código para executar no encerramento (se necessário)
    print("Aplicação encerrada.")

app = FastAPI(lifespan=lifespan)

# Inclui os routers na aplicação
app.include_router(agenda_router.router)
app.include_router(pessoas_router.router)

@app.get("/")
def read_root():
    return {"message": "API da Clínica Virtual no ar!"}
