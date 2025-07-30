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

from app.prompts.prompts_cadastro import prompt1, prompt4, prompt5, prompt6
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

if not TELEGRAM_TOKEN:
    logging.error("TELEGRAM_TOKEN não encontrado no .env!")
if not API_KEY:
    logging.error("API_KEY (Gemini) não encontrada no .env!")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"
model = genai.GenerativeModel(MODEL_NAME)


# --- FUNÇÕES DE LÓGICA DE NEGÓCIO (API) ---

def gerar_resposta_amigavel(situacao: str, dados_adicionais: dict = None) -> str:
    if dados_adicionais is None: dados_adicionais = {}
    prompt = prompt5.format(situacao=situacao, dados_adicionais=json.dumps(dados_adicionais, ensure_ascii=False))
    return model.generate_content(prompt).text

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
    URL = f"{API_URL_BASE}/pessoas/{cpf}"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API buscar_pessoa_por_cpf: {e}")
        return None

def listar_especialidades_api() -> list[str] | None:
    URL = f"{API_URL_BASE}/agendas/especialidades"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API listar_especialidades_api: {e}")
        return None

def listar_horarios_disponiveis(especialidade: str) -> dict | None:
    URL = f"{API_URL_BASE}/agendas/{especialidade}"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API listar_horarios_disponiveis: {e}")
        return None

def agendar_consulta_api(payload: dict) -> tuple[bool, str | None]:
    URL = f"{API_URL_BASE}/consultas"
    try:
        response = requests.post(URL, json=payload)
        if response.status_code == 201: return (True, None)
        return (False, response.json().get("detail", "Erro desconhecido."))
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API agendar_consulta_api: {e}")
        return (False, "Erro de conexão.")

def buscar_consultas_agendadas_api(cpf: str) -> list[dict] | None:
    URL = f"{API_URL_BASE}/pessoas/{cpf}/consultas_agendadas"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API buscar_consultas_agendadas_api: {e}")
        return None

def listar_tipos_exames_api() -> list[str] | None:
    URL = f"{API_URL_BASE}/exames/tipos"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API listar_tipos_exames_api: {e}")
        return None

def listar_horarios_exame_api(tipo_exame: str) -> dict | None:
    URL = f"{API_URL_BASE}/exames/{tipo_exame}"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API listar_horarios_exame_api: {e}")
        return None

def agendar_exame_api(payload: dict) -> tuple[bool, str | None]:
    URL = f"{API_URL_BASE}/exames/agendar"
    try:
        response = requests.post(URL, json=payload)
        if response.status_code == 201: return (True, None)
        return (False, response.json().get("detail", "Erro desconhecido."))
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API agendar_exame_api: {e}")
        return (False, "Erro de conexão.")

def buscar_exames_agendados_api(cpf: str) -> list[dict] | None:
    URL = f"{API_URL_BASE}/exames/{cpf}/exames_agendados"
    try:
        response = requests.get(URL)
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro API buscar_exames_agendados_api: {e}")
        return None

# --- ESTADOS DA CONVERSA ---
(MAIN_MENU, ASKED_REGISTRATION, AWAITING_DETAILS, AWAITING_CPF,
 AWAITING_SPECIALTY, AWAITING_DAY_INPUT, SELECTING_TIME, 
 AWAITING_CPF_FOR_APPOINTMENTS,
 AWAITING_EXAM_TYPE, AWAITING_EXAM_DAY, SELECTING_EXAM_TIME
) = range(11)

# --- FUNÇÕES HANDLER DO BOT ---

async def _send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = "Posso te ajudar com mais alguma coisa?"):
    keyboard = [
        [InlineKeyboardButton("Agendar Consulta", callback_data="agendar_consulta")],
        [InlineKeyboardButton("Agendar Exame", callback_data="agendar_exame")],
        [InlineKeyboardButton("Meus Agendamentos", callback_data="meus_agendamentos")],
        [InlineKeyboardButton("Sair", callback_data="cancelar_inicio")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_sender = update.message or update.callback_query.message
    await message_sender.reply_text(text, reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await _send_main_menu(update, context, "Olá! Sou sua assistente virtual. Como posso ajudar hoje?")
    return MAIN_MENU

async def handle_main_menu_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    selected_button_text = "Opção desconhecida"
    for row in query.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == choice:
                selected_button_text = button.text
                break
        if selected_button_text != "Opção desconhecida":
            break

    await query.edit_message_text(
        text=f"{query.message.text}\n\nSua escolha: {selected_button_text}", 
        reply_markup=None
    )

    if choice in ["agendar_consulta", "agendar_exame"]:
        context.user_data['flow'] = choice
        if context.user_data.get('cpf'):
            pessoa = buscar_pessoa_por_cpf(context.user_data['cpf'])
            nome_pessoa = pessoa.get('nome', 'Cliente') if pessoa else 'Cliente'
            await query.message.reply_text(f"Olá novamente, {nome_pessoa}! Vamos prosseguir com o agendamento.")
            if choice == "agendar_consulta": return await ask_specialty(update, context, query)
            else: return await ask_exam_type(update, context, query)
        else:
            keyboard = [[InlineKeyboardButton("Já tenho", callback_data="cadastro_sim"), InlineKeyboardButton("Ainda não", callback_data="cadastro_nao")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(text="Para prosseguir, você já possui cadastro?", reply_markup=reply_markup)
            return ASKED_REGISTRATION
            
    elif choice == "meus_agendamentos":
        if context.user_data.get('cpf'):
            return await _show_appointments(update, context, context.user_data['cpf'])
        else:
            await query.message.reply_text("Para ver seus agendamentos, por favor, informe seu CPF.")
            return AWAITING_CPF_FOR_APPOINTMENTS
            
    elif choice == "cancelar_inicio":
        await query.message.reply_text("Tudo bem! Se precisar de algo, é só me chamar com /start. 😊")
        return ConversationHandler.END

async def handle_registration_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    selected_button_text = "Opção desconhecida"
    for row in query.message.reply_markup.inline_keyboard:
        for button in row:
            if button.callback_data == query.data:
                selected_button_text = button.text
                break
        if selected_button_text != "Opção desconhecida":
            break

    await query.edit_message_text(text=f"{query.message.text}\n\nSua resposta: {selected_button_text}", reply_markup=None)
    
    if query.data == "cadastro_nao":
        await query.message.reply_text(
            "Sem problemas, vamos fazer seu cadastro. Por favor, me envie seus dados em uma única mensagem, como no exemplo:\n\n"
            "Nome: João da Silva, Idade: 30, Sexo: Masculino, CPF: 12345678900, "
            "Telefone: 61987654321, Email: joao.silva@email.com"
        )
        return AWAITING_DETAILS
    else:
        await query.message.reply_text("Ok! Por favor, me informe seu CPF para eu localizar seu cadastro.")
        return AWAITING_CPF

async def handle_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    dados_cadastrados = processar_cadastro(update.message.text)
    if dados_cadastrados:
        context.user_data['cpf'] = dados_cadastrados.get('cpf')
        await update.message.reply_text("✅ Cadastro realizado com sucesso!")
        if context.user_data.get('flow') == 'agendar_consulta':
            return await ask_specialty(update, context)
        else:
            return await ask_exam_type(update, context)
    else:
        await update.message.reply_text("❌ Desculpe, houve um erro no cadastro. Tente novamente ou /cancelar.")
        return AWAITING_DETAILS

async def handle_cpf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto_usuario = update.message.text
    prompt = prompt4.format(texto_usuario=texto_usuario)
    resposta_json_str = model.generate_content(prompt).text
    try:
        cpf_extraido = json.loads(resposta_json_str).get("cpf")
    except json.JSONDecodeError:
        cpf_extraido = None
    if not cpf_extraido:
        await update.message.reply_text("Não consegui identificar um CPF válido. Tente novamente.")
        return AWAITING_CPF
    pessoa_encontrada = buscar_pessoa_por_cpf(cpf_extraido)
    if pessoa_encontrada:
        context.user_data['cpf'] = pessoa_encontrada.get('cpf')
        nome_pessoa = pessoa_encontrada.get('nome', 'Cliente')
        await update.message.reply_text(f"✅ Cadastro localizado, {nome_pessoa}!")
        if context.user_data.get('flow') == 'agendar_consulta':
            return await ask_specialty(update, context)
        else:
            return await ask_exam_type(update, context)
    else:
        await update.message.reply_text("❌ CPF não encontrado. Use /start para fazer um novo cadastro.")
        return ConversationHandler.END

async def _show_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE, cpf: str) -> int:
    message_sender = update.message or update.callback_query.message
    pessoa = buscar_pessoa_por_cpf(cpf)
    nome_paciente = pessoa.get('nome', 'Cliente') if pessoa else 'Cliente'
    
    consultas = buscar_consultas_agendadas_api(cpf)
    exames = buscar_exames_agendados_api(cpf)
    
    message = f"Olá, {nome_paciente}! Aqui estão seus agendamentos:\n"
    has_appointments = False
    
    if consultas:
        has_appointments = True
        message += "\n**Consultas:**\n"
        for c in consultas:
            message += f"- {c.get('especialidade')} com {c.get('doutor')} em {datetime.fromisoformat(c.get('data_hora')).strftime('%d/%m/%Y às %H:%M')}\n"
            
    if exames:
        has_appointments = True
        message += "\n**Exames:**\n"
        for e in exames:
            message += f"- {e.get('tipo_exame')} em {e.get('local_exame')} no dia {datetime.fromisoformat(e.get('data_hora')).strftime('%d/%m/%Y às %H:%M')}\n"
            
    if not has_appointments:
        message = f"Olá, {nome_paciente}. Você ainda não possui agendamentos."
        
    await message_sender.reply_text(message, parse_mode='Markdown')
    await _send_main_menu(update, context)
    return MAIN_MENU

async def handle_cpf_for_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cpf_input = update.message.text.strip()
    cpf_limpo = re.sub(r'\D', '', cpf_input)
    if not (cpf_limpo.isdigit() and len(cpf_limpo) == 11):
        await update.message.reply_text("CPF inválido. Por favor, tente novamente.")
        return AWAITING_CPF_FOR_APPOINTMENTS
    context.user_data['cpf'] = cpf_limpo
    return await _show_appointments(update, context, cpf_limpo)

async def ask_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> int:
    message_text = "Para qual especialidade você gostaria de agendar?"
    especialidades = listar_especialidades_api()
    if not especialidades:
        await (query.message if query else update.message).reply_text("Desculpe, não consegui carregar as especialidades.")
        return ConversationHandler.END
    keyboard = [[InlineKeyboardButton(esp, callback_data=esp)] for esp in especialidades]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await (query.message if query else update.message).reply_text(text=message_text, reply_markup=reply_markup)
    return AWAITING_SPECIALTY

async def handle_specialty_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    especialidade = query.data
    context.user_data['especialidade'] = especialidade
    await query.edit_message_text(text=f"{query.message.text}\n\nEspecialidade: {especialidade}", reply_markup=None)
    horarios_por_medico = listar_horarios_disponiveis(especialidade)
    if not horarios_por_medico:
        await query.message.reply_text(f"Desculpe, não há horários para {especialidade}.")
        return await _send_main_menu(update, context)
    context.user_data['agenda_completa'] = horarios_por_medico
    await query.message.reply_text("Para qual dia você gostaria de agendar? (ex: amanhã, 30/07/2025)")
    return AWAITING_DAY_INPUT

async def handle_day_input(update: Update, context: ContextTypes.DEFAULT_TYPE, flow_key: str) -> int:
    texto_usuario = update.message.text
    data_atual = datetime.now().strftime("%d/%m/%Y")
    prompt = prompt6.format(texto_usuario=texto_usuario, data_atual=data_atual)
    resposta_json_str = model.generate_content(prompt).text
    try:
        data_extraida_str = json.loads(resposta_json_str).get("data")
        data_selecionada = datetime.strptime(data_extraida_str, "%d/%m/%Y").date()
    except (json.JSONDecodeError, ValueError, TypeError):
        await update.message.reply_text("Não entendi a data. Por favor, tente um formato como '30/07/2025'.")
        return AWAITING_DAY_INPUT if flow_key == 'consulta' else AWAITING_EXAM_DAY
    
    if data_selecionada < datetime.now().date():
        await update.message.reply_text("Não é possível agendar para uma data passada.")
        return AWAITING_DAY_INPUT if flow_key == 'consulta' else AWAITING_EXAM_DAY

    await update.message.reply_text(f"Verificando horários para {data_selecionada.strftime('%d/%m/%Y')}...")
    
    keyboard = []
    context.user_data['callback_map'] = {}
    map_counter = 0

    if flow_key == 'consulta':
        agenda_completa = context.user_data.get('agenda_completa', {})
        medico_id_map = {nome: i + 1 for i, nome in enumerate(agenda_completa.keys())}
        for medico_nome, horarios_lista in agenda_completa.items():
            for horario_str in horarios_lista:
                if datetime.fromisoformat(horario_str).date() == data_selecionada:
                    unique_id = str(map_counter)
                    context.user_data['callback_map'][unique_id] = {
                        'id_medico': medico_id_map[medico_nome],
                        'medico_nome': medico_nome,
                        'data_hora': horario_str
                    }
                    hora = datetime.fromisoformat(horario_str).time()
                    texto_botao = f"{hora.strftime('%H:%M')} - {medico_nome}"
                    keyboard.append([InlineKeyboardButton(texto_botao, callback_data=f"consulta_{unique_id}")])
                    map_counter += 1
    else: # flow_key == 'exame'
        agenda_completa = context.user_data.get('agenda_exame_completa', {})
        for local, horarios_lista in agenda_completa.items():
            for horario_str in horarios_lista:
                if datetime.fromisoformat(horario_str).date() == data_selecionada:
                    unique_id = str(map_counter)
                    context.user_data['callback_map'][unique_id] = {
                        'local_exame': local,
                        'data_hora': horario_str
                    }
                    hora = datetime.fromisoformat(horario_str).time()
                    texto_botao = f"{hora.strftime('%H:%M')} - {local}"
                    keyboard.append([InlineKeyboardButton(texto_botao, callback_data=f"exame_{unique_id}")])
                    map_counter += 1

    if not keyboard:
        await update.message.reply_text(f"Nenhum horário livre para {data_selecionada.strftime('%d/%m/%Y')}. Tente outra data.")
        return AWAITING_DAY_INPUT if flow_key == 'consulta' else AWAITING_EXAM_DAY
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Escolha um dos horários:", reply_markup=reply_markup)
    return SELECTING_TIME if flow_key == 'consulta' else SELECTING_EXAM_TIME

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    unique_id = query.data.replace("consulta_", "")
    horario_data = context.user_data.get('callback_map', {}).get(unique_id)

    if not horario_data:
        await query.message.reply_text("❌ Ops! O horário selecionado não foi encontrado. Tente novamente com /start.")
        return ConversationHandler.END

    id_medico = horario_data['id_medico']
    medico_nome = horario_data['medico_nome']
    data_hora = horario_data['data_hora']
    hora_formatada = datetime.fromisoformat(data_hora).strftime('%d/%m/%Y às %H:%M')
    
    await query.edit_message_text(text=f"{query.message.text}\n\nHorário: {hora_formatada.split(' às ')[1]} com {medico_nome}", reply_markup=None)
    
    payload = {"cpf_paciente": context.user_data['cpf'], "especialidade": context.user_data['especialidade'], "id_medico": int(id_medico), "doutor": medico_nome, "data_hora": data_hora}
    sucesso, msg_erro = agendar_consulta_api(payload)
    
    if sucesso: await query.message.reply_text(f"✅ Consulta agendada com sucesso para {hora_formatada} com {medico_nome}!")
    else: await query.message.reply_text(f"❌ Erro ao agendar: {msg_erro}")
        
    await _send_main_menu(update, context)
    return MAIN_MENU

async def ask_exam_type(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None) -> int:
    tipos_exames = listar_tipos_exames_api()
    if not tipos_exames:
        await (query.message if query else update.message).reply_text("Desculpe, não há tipos de exames disponíveis.")
        return await _send_main_menu(update, context)
    keyboard = [[InlineKeyboardButton(tipo, callback_data=tipo)] for tipo in tipos_exames]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await (query.message if query else update.message).reply_text(text="Qual tipo de exame você gostaria de agendar?", reply_markup=reply_markup)
    return AWAITING_EXAM_TYPE

async def handle_exam_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    tipo_exame = query.data
    context.user_data['tipo_exame'] = tipo_exame
    await query.edit_message_text(text=f"{query.message.text}\n\nExame: {tipo_exame}", reply_markup=None)
    horarios_por_local = listar_horarios_exame_api(tipo_exame)
    if not horarios_por_local:
        await query.message.reply_text(f"Desculpe, não há horários para {tipo_exame}.")
        return await _send_main_menu(update, context)
    context.user_data['agenda_exame_completa'] = horarios_por_local
    await query.message.reply_text("Para qual dia você gostaria de agendar? (ex: amanhã, 01/08/2025)")
    return AWAITING_EXAM_DAY

async def handle_exam_day_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await handle_day_input(update, context, flow_key='exame')

async def select_exam_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    unique_id = query.data.replace("exame_", "")
    horario_data = context.user_data.get('callback_map', {}).get(unique_id)

    if not horario_data:
        await query.message.reply_text("❌ Ops! O horário selecionado não foi encontrado. Tente novamente com /start.")
        return ConversationHandler.END

    local_exame = horario_data['local_exame']
    data_hora_str = horario_data['data_hora']
    data_hora = datetime.fromisoformat(data_hora_str)
    
    payload = {"cpf_paciente": context.user_data['cpf'], "tipo_exame": context.user_data['tipo_exame'], "local_exame": local_exame, "data_hora": data_hora.isoformat()}
    sucesso, msg_erro = agendar_exame_api(payload)
    
    if sucesso: await query.edit_message_text(f"✅ Exame agendado com sucesso para {data_hora.strftime('%d/%m/%Y às %H:%M')} em {local_exame}!")
    else: await query.edit_message_text(f"❌ Erro ao agendar: {msg_erro}")

    await _send_main_menu(update, context)
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Tudo bem, processo cancelado. Se precisar de algo, é só chamar com /start.")
    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(handle_main_menu_decision)],
            ASKED_REGISTRATION: [CallbackQueryHandler(handle_registration_decision)],
            AWAITING_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_details)],
            AWAITING_CPF: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cpf)],
            AWAITING_SPECIALTY: [CallbackQueryHandler(handle_specialty_selection)],
            AWAITING_DAY_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_day_input(u, c, 'consulta'))],
            SELECTING_TIME: [CallbackQueryHandler(select_time)],
            AWAITING_CPF_FOR_APPOINTMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cpf_for_appointments)],
            AWAITING_EXAM_TYPE: [CallbackQueryHandler(handle_exam_type_selection)],
            AWAITING_EXAM_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: handle_day_input(u, c, 'exame'))],
            SELECTING_EXAM_TIME: [CallbackQueryHandler(select_exam_time)],
        },
        fallbacks=[CommandHandler("cancelar", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
