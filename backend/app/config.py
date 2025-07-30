import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.dirname(APP_DIR)

DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(DATA_DIR, exist_ok=True)

URL_AGENDAMENTOS = os.path.join(DATA_DIR, 'agendamentos.json')
URL_CONSULTAS = os.path.join(DATA_DIR, 'pessoa_horario.csv')
URL_CADASTROS = os.path.join(DATA_DIR, 'cadastros.csv')
URL_AGENDAMENTOS_EXAMES = os.path.join(DATA_DIR, 'agendamentos_exames.json')

CABECALHO_CONSULTAS = ['cpf', 'especialidade', 'doutor', 'horario']
CABECALHO_CADASTROS = ['nome', 'idade', 'sexo', 'cpf', 'telefone', 'email']
