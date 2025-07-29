# frontend/telegram_bot.py

import os
import logging
import json
import re
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

# Importações do Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

# Importações da sua lógica de backend
import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from app.prompts.prompts_cadastro import prompt1, prompt2, prompt3
import google.generativeai as genai
import requests

# --- CONFIGURAÇÃO INICIAL ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))

API_URL_BASE = "http://127.0.0.1:8000"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# --- FUNÇÕES DE LÓGICA DE NEGÓCIO (API) ---

def processar_cadastro(texto_usuario: str) -> dict | None:
    URL = API_URL_BASE + '/pessoas/cadastro'
    prompt_dados = prompt1.format(entrada_usuario=texto_usuario)
    resposta_gemini_json = model.generate_content(prompt_dados).text
    try:
        string_limpa = resposta_gemini_json.strip().replace('```json', '').replace('```', '')
        dados_dicionario = json.loads(string_limpa)
    except json.JSONDecodeError:
        logging.error(f"Erro de JSON retornado pela IA: {resposta_gemini_json}")
        return None
    response = requests.post(URL, json=dados_dicionario)
    if response.status_code == 201:
        return dados_dicionario
    logging.error(f"Erro ao cadastrar na API: {response.status_code} - {response.text}")
    return None

def buscar_pessoa_por_cpf(cpf: str) -> dict | None:
    """Chama a API para obter os dados de uma pessoa pelo CPF."""
    URL = f"{API_URL_BASE}/pessoas/{cpf}"
    # ### MUDANÇA PARA DEBUG ###: Adicionado logging para ver a chamada e a resposta.
    logging.info(f"--- DEBUG: Chamando API para buscar CPF na URL: {URL}")
    try:
        response = requests.get(URL)
        logging.info(f"--- DEBUG: Resposta da API - Status: {response.status_code}, Conteúdo: {response.text}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao chamar API de busca por CPF: {e}")
        return None

def listar_especialidades_api() -> list[str] | None:
    URL = f"{API_URL_BASE}/agendas/especialidades"
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao chamar API de especialidades: {e}")
        return None

def listar_horarios_disponiveis(especialidade: str) -> dict | None:
    URL = f"{API_URL_BASE}/agendas/{especialidade}"
    try:
        response = requests.get(URL)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao chamar API de horários: {e}")
        return None

def agendar_consulta_api(payload: dict) -> bool:
    URL = f"{API_URL_BASE}/consultas"
    try:
        response = requests.post(URL, json=payload)
        return response.status_code == 201
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao chamar API de agendamento: {e}")
        return False

# --- ESTADOS DA CONVERSA ---
(ASKED_CONSULTA, ASKED_REGISTRATION, AWAITING_DETAILS, AWAITING_CPF,
 AWAITING_SPECIALTY, AWAITING_DAY_INPUT, SELECTING_TIME) = range(7)

# --- FUNÇÕES HANDLER DO BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Sim, por favor!", callback_data="agendar_sim"),
            InlineKeyboardButton("Não, obrigado.", callback_data="agendar_nao"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Olá! Sou sua assistente virtual. Gostaria de marcar uma consulta?",
        reply_markup=reply_markup,
    )
    return ASKED_CONSULTA

async def handle_consulta_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    escolha = "Sim, por favor!" if query.data == "agendar_sim" else "Não, obrigado."
    await query.edit_message_text(text=f"{query.message.text}\n\nSua resposta: {escolha}", reply_markup=None)
    if query.data == "agendar_sim":
        keyboard = [
            [
                InlineKeyboardButton("Já tenho", callback_data="cadastro_sim"),
                InlineKeyboardButton("Ainda não", callback_data="cadastro_nao"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            text="Ótimo! Você já possui cadastro conosco?", reply_markup=reply_markup
        )
        return ASKED_REGISTRATION
    else:
        await query.message.reply_text("Tudo bem! Se mudar de ideia, é só me chamar com /start. 😊")
        return ConversationHandler.END

async def handle_registration_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    escolha = "Ainda não" if query.data == "cadastro_nao" else "Já tenho"
    await query.edit_message_text(text=f"{query.message.text}\n\nSua resposta: {escolha}", reply_markup=None)
    if query.data == "cadastro_nao":
        await query.message.reply_text(
            "Sem problemas, vamos fazer seu cadastro agora. "
            "Por favor, me envie seus dados em uma única mensagem, como no exemplo:\n\n"
            "Nome: João da Silva, \nIdade: 30, \nSexo: Masculino, \nCPF: 12345678900, "
            "Telefone: 61987654321, \nEmail: joao.silva@email.com"
        )
        return AWAITING_DETAILS
    else: # cadastro_sim
        await query.message.reply_text("Ok! Por favor, me informe seu CPF para eu localizar seu cadastro.")
        return AWAITING_CPF

async def handle_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_details = update.message.text
    await update.message.reply_text("Obrigado! Processando seu cadastro...")
    dados_cadastrados = processar_cadastro(user_details)
    if dados_cadastrados:
        context.user_data['cpf'] = dados_cadastrados.get('cpf')
        await update.message.reply_text("✅ Cadastro realizado com sucesso!")
        return await ask_specialty(update, context)
    else:
        await update.message.reply_text("❌ Desculpe, houve um erro no cadastro. Por favor, tente novamente ou digite /cancelar.")
        return AWAITING_DETAILS

async def handle_cpf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o CPF, valida via API e continua o fluxo."""
    cpf_input = update.message.text.strip()
    
    cpf_limpo = re.sub(r'\D', '', cpf_input)
    
    await update.message.reply_text(f"Verificando CPF: {cpf_limpo}...")

    pessoa_encontrada = buscar_pessoa_por_cpf(cpf_limpo)

    if pessoa_encontrada:
        context.user_data['cpf'] = pessoa_encontrada.get('cpf')
        nome_pessoa = pessoa_encontrada.get('nome', 'Cliente')
        await update.message.reply_text(f"✅ Cadastro localizado, {nome_pessoa}!")
        return await ask_specialty(update, context)
    else:
        await update.message.reply_text(
            "❌ CPF não encontrado em nosso sistema. "
            "Por favor, use o comando /start para iniciar um novo cadastro."
        )
        return ConversationHandler.END

async def ask_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> int:
    message_text = "Perfeito! Para qual especialidade você gostaria de agendar?"
    especialidades = listar_especialidades_api()
    if not especialidades:
        error_message = "Desculpe, não consegui carregar as especialidades no momento. Tente novamente mais tarde."
        if query:
            await query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(esp, callback_data=esp)] for esp in especialidades]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.message.reply_text(text=message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)
    return AWAITING_SPECIALTY

async def handle_specialty_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    especialidade = query.data
    context.user_data['especialidade'] = especialidade
    await query.edit_message_text(
        text=f"{query.message.text}\n\nEspecialidade escolhida: {especialidade}",
        reply_markup=None
    )
    await query.message.reply_text(f"Buscando horários para {especialidade}...")
    horarios_por_medico = listar_horarios_disponiveis(especialidade)
    if not horarios_por_medico:
        await query.message.reply_text(f"Desculpe, não encontrei horários disponíveis para {especialidade} no momento. Tente novamente com /start.")
        return ConversationHandler.END
    context.user_data['agenda_completa'] = horarios_por_medico
    await query.message.reply_text("Perfeito. Para qual dia você gostaria de agendar a consulta? (use o formato DD/MM/AAAA)")
    return AWAITING_DAY_INPUT

async def handle_day_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input_date = update.message.text.strip()
    try:
        data_selecionada = datetime.strptime(user_input_date, "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text("Formato de data inválido. Por favor, use DD/MM/AAAA (ex: 30/07/2025).")
        return AWAITING_DAY_INPUT
    await update.message.reply_text(f"Ótimo! Verificando horários para {data_selecionada.strftime('%d/%m/%Y')}...")
    agenda_completa = context.user_data.get('agenda_completa', {})
    keyboard = []
    medico_id_map = {nome: i + 1 for i, nome in enumerate(agenda_completa.keys())}
    for medico_nome, horarios_lista in agenda_completa.items():
        id_medico = medico_id_map[medico_nome]
        for horario_str in horarios_lista:
            try:
                if datetime.fromisoformat(horario_str).date() == data_selecionada:
                    hora = datetime.fromisoformat(horario_str).time()
                    callback_data = f"agendar_{id_medico}_{medico_nome}_{horario_str}"
                    texto_botao = f"{hora.strftime('%H:%M')} - {medico_nome}"
                    keyboard.append([InlineKeyboardButton(texto_botao, callback_data=callback_data)])
            except (ValueError, TypeError):
                continue
    if not keyboard:
        await update.message.reply_text(f"Desculpe, não há horários disponíveis para o dia {data_selecionada.strftime('%d/%m/%Y')}. Por favor, escolha outro dia ou digite /cancelar.")
        return AWAITING_DAY_INPUT
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Perfeito. Agora escolha um dos horários livres:", reply_markup=reply_markup)
    return SELECTING_TIME

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    _, id_medico, medico_nome, data_hora = query.data.split('_', 3)
    hora_formatada = datetime.fromisoformat(data_hora).strftime('%d/%m/%Y às %H:%M')
    
    await query.edit_message_text(
        text=f"{query.message.text}\n\nHorário escolhido: {hora_formatada.split(' às ')[1]} com {medico_nome}", 
        reply_markup=None
    )
    
    await query.message.reply_text("Confirmando seu agendamento, um momento...")
    
    payload = {
        "cpf_paciente": context.user_data['cpf'],
        "especialidade": context.user_data['especialidade'],
        "id_medico": int(id_medico),
        "doutor": medico_nome,
        "data_hora": data_hora
    }
    
    sucesso = agendar_consulta_api(payload)
    
    if sucesso:
        await query.message.reply_text(f"✅ Consulta agendada com sucesso para {hora_formatada} com {medico_nome}!")
    else:
        await query.message.reply_text("❌ Desculpe, não foi possível agendar neste horário. Ele pode ter sido ocupado. Tente novamente com /start.")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela e encerra a conversa."""
    await update.message.reply_text("Tudo bem, processo cancelado. Se precisar de algo, é só chamar com /start.")
    return ConversationHandler.END

def main() -> None:
    """Inicia o bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKED_CONSULTA: [CallbackQueryHandler(handle_consulta_decision)],
            ASKED_REGISTRATION: [CallbackQueryHandler(handle_registration_decision)],
            AWAITING_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_details)],
            AWAITING_CPF: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cpf)],
            AWAITING_SPECIALTY: [CallbackQueryHandler(handle_specialty_selection)],
            AWAITING_DAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_day_input)],
            SELECTING_TIME: [CallbackQueryHandler(select_time)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
