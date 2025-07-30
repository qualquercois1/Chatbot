# app/config.py
import os

# Caminho para a pasta 'app' onde este arquivo de configuração está localizado
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho para a pasta 'backend', que está um nível acima da pasta 'app'
BASE_DIR = os.path.dirname(APP_DIR)

# Caminho para a pasta 'data', que está dentro de 'backend'
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Garante que a pasta 'data' exista no local correto (backend/data)
os.makedirs(DATA_DIR, exist_ok=True)

# --- Define os caminhos completos para os arquivos de dados ---
URL_AGENDAMENTOS = os.path.join(DATA_DIR, 'agendamentos.json')
URL_CONSULTAS = os.path.join(DATA_DIR, 'pessoa_horario.csv')
# ### MUDANÇA ###: Apontando para o arquivo CSV correto para os cadastros
URL_CADASTROS = os.path.join(DATA_DIR, 'cadastros.csv')
URL_AGENDAMENTOS_EXAMES = os.path.join(DATA_DIR, 'agendamentos_exames.json')

# --- Define os cabeçalhos para os arquivos CSV ---
CABECALHO_CONSULTAS = ['cpf', 'especialidade', 'doutor', 'horario']
CABECALHO_CADASTROS = ['nome', 'idade', 'sexo', 'cpf', 'telefone', 'email']
