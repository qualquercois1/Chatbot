# app/services/pessoas_service.py
import csv
import os
from app.config import URL_CONSULTAS, URL_CADASTROS, CABECALHO_CADASTROS
from app.schemas import CadastroPessoaPayload, ConsultaPayload

class PessoasService:
    def __init__(self):
        self.csv_path_cadastros = URL_CADASTROS
        self.csv_path_consultas = URL_CONSULTAS

    def _carregar_pessoas(self) -> list[dict]:
        """Carrega todos os cadastros do arquivo CSV."""
        try:
            # Garante que o arquivo exista com o cabeçalho correto
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

    def buscar_por_cpf(self, cpf: str) -> dict | None:
        """Busca uma pessoa pelo CPF no arquivo CSV."""
        # Garante que o CPF a ser buscado esteja limpo (apenas números)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        pessoas = self._carregar_pessoas()
        for pessoa in pessoas:
            # Compara com o CPF limpo do arquivo
            cpf_arquivo_limpo = ''.join(filter(str.isdigit, pessoa.get('cpf', '')))
            if cpf_arquivo_limpo == cpf_limpo:
                return pessoa
        return None

    def cadastrar(self, payload: CadastroPessoaPayload) -> bool:
        """Cadastra uma nova pessoa no arquivo CSV."""
        # Verifica se o CPF já existe antes de cadastrar
        if self.buscar_por_cpf(payload.cpf):
            return False # CPF já cadastrado

        try:
            # Abre o arquivo em modo 'append' para adicionar uma nova linha
            with open(self.csv_path_cadastros, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CABECALHO_CADASTROS)
                writer.writerow(payload.model_dump())
            return True
        except Exception as e:
            print(f"ERRO ao salvar cadastro no CSV: {e}")
            return False

    def agendar_consulta(self, payload: ConsultaPayload) -> bool:
        """Registra uma nova consulta no arquivo CSV."""
        try:
            header = ['cpf', 'especialidade', 'doutor', 'horario']
            file_exists = os.path.exists(self.csv_path_consultas)
            
            with open(self.csv_path_consultas, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                if not file_exists or os.path.getsize(self.csv_path_consultas) == 0:
                    writer.writeheader()
                
                new_row = {
                    'cpf': payload.cpf_paciente,
                    'especialidade': payload.especialidade,
                    'doutor': payload.doutor,
                    'horario': payload.data_hora
                }
                writer.writerow(new_row)
            return True
        except Exception as e:
            print(f"ERRO CRÍTICO ao salvar a consulta no CSV: {e}")
            return False

    def deletar_por_cpf(self, cpf: str) -> bool:
        """Deleta uma pessoa do cadastro lendo e reescrevendo o arquivo CSV."""
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        pessoas = self._carregar_pessoas()
        
        pessoa_encontrada = False
        pessoas_mantidas = []
        for pessoa in pessoas:
            cpf_arquivo_limpo = ''.join(filter(str.isdigit, pessoa.get('cpf', '')))
            if cpf_arquivo_limpo == cpf_limpo:
                pessoa_encontrada = True
            else:
                pessoas_mantidas.append(pessoa)

        if not pessoa_encontrada:
            return False

        try:
            # Reescreve o arquivo apenas com as pessoas que não foram deletadas
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
