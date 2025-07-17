import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests, unicodedata


API_URL_BASE = "http://127.0.0.1:8000"

load_dotenv()

API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-flash"

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def consultar_cadastro():
    entrada = input('Por favor, insira seu cpf.\n')
    URL = API_URL_BASE+f'/pessoas/{entrada}'
    response = requests.get(URL)

    if response.status_code == 200:
        print("Resposta da API:\n", response.json())
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")



def cadastrar():
    URL = API_URL_BASE+'/pessoas/cadastro'
    entrada = input('''
    Insira seguintes dados: Nome, idade, sexo, cpf, telefone, email
    (Ex.:
        Nome: João Roberto,
        Idade: 18,
        Sexo: Masculino,
        Cpf: 12345678900,
        Telefone: 61992422323,
        Email: joaoroberto@gmail.com
    )
    ''')

    #trata os dados com o gemini aqui

    dados = {}
    for i in entrada.split(','):
        chave, valor = i.split(':')
        dados[chave.strip().lower()] = valor.strip()

    response = requests.post(URL, json=dados)

    if response.status_code == 201:
        print("✅ Cadastro realizado com sucesso!")
        print("Resposta da API:", response.json())
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")

    #com base na resposta da API o gemini deve retornar uma resposta também e conduzir para o proximo passo

def mensagem_entrada():
    entrada = input('Olá, gostaria de marcar uma consulta?\n')
    if entrada.lower() == 'sim':
        entrada = input('Já possui cadastro?\n')
        if entrada.lower() == 'sim':
            consultar_cadastro()
        elif remover_acentos(entrada).lower() == 'nao':
            cadastrar()


if __name__ == "__main__":
    mensagem_entrada()
        