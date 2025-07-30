import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.dirname(APP_DIR)

DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(DATA_DIR, exist_ok=True)

# --- Define os caminhos completos para os arquivos de dados ---
URL_AGENDAMENTOS = os.path.join(DATA_DIR, 'agendamentos.json') # Agendamentos de consultas
URL_CONSULTAS = os.path.join(DATA_DIR, 'pessoa_horario.csv') # Dados de consulta (pode ser renomeado)
URL_CADASTROS = os.path.join(DATA_DIR, 'cadastros.csv')
URL_AGENDAMENTOS_EXAMES = os.path.join(DATA_DIR, 'agendamentos_exames.json') # Horários disponíveis para exames
URL_EXAMES_AGENDADOS = os.path.join(DATA_DIR, 'exames_agendados.json') # NOVO: Agendamentos de exames concluídos

CABECALHO_CONSULTAS = ['cpf', 'especialidade', 'doutor', 'horario']
CABECALHO_CADASTROS = ['nome', 'idade', 'sexo', 'cpf', 'telefone', 'email']