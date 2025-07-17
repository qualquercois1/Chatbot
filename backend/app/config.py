from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

URL_AGENDAMENTOS = BASE_DIR / "data" / "agendamentos.json"
URL_CADASTROS = BASE_DIR / "data" / "cadastros.csv"
URL_CONSULTAS = BASE_DIR / "data" / "pessoa_horario.csv"

CABECALHO_CADASTROS = ["nome", "idade", "sexo", "cpf", "telefone", "email"]
CABECALHO_CONSULTAS = ["cpf", "especialidade", "doutor", "horario"]

API_URL_BASE = "http://127.0.0.1:8000"