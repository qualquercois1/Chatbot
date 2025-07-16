import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-flash"

def consultar_cadastro():
    entrada = input('Por favor, insira seu cpf.\n')
    print('CPF do usuario:\n', entrada)

def cadastrar():
    entrada = input('''
    Insira seguintes dados: Nome, idade, sexo, telefone, email
    (Ex.:
        Nome: João Roberto,
        Idade: 18,
        Sexo: Masculino,
        Telefone: 61992422323,
        Email: joaoroberto@gmail.com
    )
    ''')
    print('Dados do usuario:\n', entrada)

def mensagem_entrada():
    entrada = input('Olá, gostaria de marcar uma consulta?\n')
    if entrada.lower() == 'sim':
        entrada = input('Já possui cadastro?\n')
        if entrada.lower() == 'sim':
            consultar_cadastro()
        elif entrada.lower() == 'não':
            cadastrar()


if __name__ == "__main__":
    mensagem_entrada()
        