# app/services/pessoas_service.py
import csv
import os
from app.config import URL_CONSULTAS, URL_CADASTROS, CABECALHO_CADASTROS, CABECALHO_CONSULTAS
from app.schemas import CadastroPessoaPayload, ConsultaPayload

class PessoasService:
    def __init__(self):
        self.csv_path_cadastros = URL_CADASTROS
        self.csv_path_consultas = URL_CONSULTAS

    def _carregar_pessoas(self) -> list[dict]:
        """Carrega todos os cadastros do arquivo CSV."""
        try:
            if not os.path.exists(self.csv_path_cadastros) or os.path.getsize(self.csv_path_cadastros) == 0:
                with open(self.csv_path_cadastros, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(CABECALHO_CADASTROS)
                return []
            with open(self.csv_path_cadastros, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"Erro ao carregar o arquivo CSV de cadastros: {e}")
            return []

    def _carregar_consultas(self) -> list[dict]:
        """Carrega todas as consultas do arquivo CSV."""
        try:
            if not os.path.exists(self.csv_path_consultas) or os.path.getsize(self.csv_path_consultas) == 0:
                with open(self.csv_path_consultas, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(CABECALHO_CONSULTAS)
                return []
            with open(self.csv_path_consultas, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"Erro ao carregar o arquivo CSV de consultas: {e}")
            return []

    def buscar_por_cpf(self, cpf: str) -> dict | None:
        """Busca uma pessoa pelo CPF no arquivo CSV."""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        pessoas = self._carregar_pessoas()
        for pessoa in pessoas:
            cpf_arquivo_limpo = ''.join(filter(str.isdigit, pessoa.get('cpf', '')))
            if cpf_arquivo_limpo == cpf_limpo:
                return pessoa
        return None

    def buscar_consultas_por_cpf(self, cpf: str) -> list[dict]:
        """Busca todas as consultas agendadas para um CPF específico."""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        consultas_agendadas = self._carregar_consultas()
        consultas_do_paciente = []
        for consulta in consultas_agendadas:
            cpf_consulta_limpo = ''.join(filter(str.isdigit, consulta.get('cpf', '')))
            if cpf_consulta_limpo == cpf_limpo:
                # Retorna o dicionário diretamente, o FastAPI cuidará da validação do schema
                consultas_do_paciente.append({
                    "cpf_paciente": consulta.get('cpf'),
                    "especialidade": consulta.get('especialidade'),
                    "doutor": consulta.get('doutor'),
                    "data_hora": consulta.get('horario'),
                    "id_medico": 0 # Valor padrão, já que não está no CSV
                })
        return consultas_do_paciente

    def cadastrar(self, payload: CadastroPessoaPayload) -> bool:
        """Cadastra uma nova pessoa no arquivo CSV."""
        if self.buscar_por_cpf(payload.cpf):
            return False
        try:
            with open(self.csv_path_cadastros, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CABECALHO_CADASTROS)
                writer.writerow(payload.model_dump())
            return True
        except Exception as e:
            print(f"ERRO ao salvar cadastro no CSV: {e}")
            return False

    def agendar_consulta(self, payload: ConsultaPayload):
        """Registra uma nova consulta no arquivo CSV, após validar conflitos."""
        try:
            consultas_agendadas = self._carregar_consultas()
            for consulta in consultas_agendadas:
                if consulta['cpf'] == payload.cpf_paciente and consulta['horario'] == payload.data_hora:
                    raise ValueError("O paciente já possui uma consulta agendada para este mesmo horário.")
            
            header = CABECALHO_CONSULTAS
            file_exists = os.path.exists(self.csv_path_consultas) and os.path.getsize(self.csv_path_consultas) > 0
            
            with open(self.csv_path_consultas, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                if not file_exists:
                    writer.writeheader()
                new_row = {
                    'cpf': payload.cpf_paciente,
                    'especialidade': payload.especialidade,
                    'doutor': payload.doutor,
                    'horario': payload.data_hora
                }
                writer.writerow(new_row)
            return True
        except ValueError:
            raise
        except Exception as e:
            print(f"ERRO CRÍTICO ao salvar a consulta no CSV: {e}")
            raise ValueError("Ocorreu um erro interno ao tentar salvar a consulta.")

    def deletar_por_cpf(self, cpf: str) -> bool:
        """Deleta uma pessoa do cadastro lendo e reescrevendo o arquivo CSV."""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        pessoas = self._carregar_pessoas()
        pessoa_encontrada = False
        pessoas_mantidas = []
        for pessoa in pessoas:
            if ''.join(filter(str.isdigit, pessoa.get('cpf', ''))) == cpf_limpo:
                pessoa_encontrada = True
            else:
                pessoas_mantidas.append(pessoa)
        if not pessoa_encontrada:
            return False
        try:
            with open(self.csv_path_cadastros, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CABECALHO_CADASTROS)
                writer.writeheader()
                writer.writerows(pessoas_mantidas)
            return True
        except Exception as e:
            print(f"ERRO ao reescrever o CSV de cadastros após deleção: {e}")
            return False

# Singleton
pessoas_service_instance = PessoasService()
def get_pessoas_service():
    return pessoas_service_instance
