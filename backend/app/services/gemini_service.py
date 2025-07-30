# app/services/gemini_services
import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests, unicodedata
from prompts.prompts_cadastro import prompt1, prompt2, prompt3
import json


API_URL_BASE = "http://127.0.0.1:8000"
load_dotenv()
API_KEY = os.getenv("API_KEY")
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

def gerar_conteudo_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text

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
    Ex.:
        Nome: João Roberto,
        Idade: 18,
        Sexo: Masculino,
        Cpf: 12345678900,
        Telefone: 61992422323,
        Email: joaoroberto@gmail.com
    
    ''')

    #trata os dados com o gemini aqui
    prompt_dados = prompt1.format(entrada_usuario = entrada)

    resposta_gemini = gerar_conteudo_gemini(prompt_dados)

    try:
        # É uma boa prática limpar a string de possíveis marcações de código
        string_limpa = resposta_gemini.strip().replace('```json', '').replace('```', '')
        
        # Converte a string limpa em um dicionário Python
        dados_dicionario = json.loads(string_limpa)
        print(f"Dados transformados em dicionário Python:\n{dados_dicionario}")

    except json.JSONDecodeError:
        # Este bloco de erro é CRUCIAL. Ele executa se a IA retornar algo que não é um JSON válido.
        print("❌ Erro crítico: A resposta da IA não é um JSON válido. Não é possível continuar.")
        print("Resposta recebida:", resposta_gemini)
        return # Aborta a função de cadastro

    response = requests.post(URL, json=dados_dicionario)

    if response.status_code == 201:
        print("✅ Cadastro realizado com sucesso!")
        print("Resposta da API:", response.json())
        #resposta do gemini aqui
        nome_usuario = dados_dicionario.get("nome", "pessoa")
        prompt_final_sucesso = prompt2.format(nome_usuario=nome_usuario)
        resposta_amigavel = gerar_conteudo_gemini(prompt_final_sucesso)
        return resposta_amigavel
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")
        #gemini informa o erro
        prompt_final_erro = prompt3.format(
            status_code=response.status_code, 
            texto_erro=response.text
        )
        resposta_erro_amigavel = gerar_conteudo_gemini(prompt_final_erro)
        return resposta_erro_amigavel

    #com base na resposta da API o gemini deve retornar uma resposta também e conduzir para o proximo passo

def mensagem_entrada():
    entrada = input('Olá, gostaria de marcar uma consulta?\n')
    if entrada.lower() == 'sim':
        entrada = input('Já possui cadastro?\n')
        if entrada.lower() == 'sim':
            consultar_cadastro()
        elif remover_acentos(entrada).lower() == 'nao':
            resposta = cadastrar()
            print(resposta)


if __name__ == "__main__":
    mensagem_entrada()
        