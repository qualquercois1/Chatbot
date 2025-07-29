# app/services/agenda_service.py
import json
import os
import csv
from fastapi import Depends
from app.config import URL_AGENDAMENTOS, URL_CONSULTAS # Assumindo que URL_CONSULTAS é o caminho para o CSV
from app.schemas import HorarioPostPayload # Removido HorarioDeletePayload pois não é usado diretamente aqui

class AgendaService:
    def __init__(self):
        # Usando as variáveis de configuração importadas
        self.db_path = URL_AGENDAMENTOS
        self.csv_path = URL_CONSULTAS

    def _carregar_dados(self):
        """Carrega os dados do arquivo JSON de agendamentos."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _salvar_dados(self, dados: dict):
        """Salva os dados no arquivo JSON de agendamentos."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def _carregar_consultas_agendadas(self):
        """
        Carrega os horários já agendados do arquivo CSV.
        Retorna um set de tuplas (especialidade, doutor, horario) para busca rápida.
        """
        agendados = set()
        try:
            # Cria o arquivo CSV com cabeçalho se ele não existir
            if not os.path.exists(self.csv_path):
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['cpf', 'especialidade', 'doutor', 'horario'])
                return agendados

            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                # Usa DictReader para ler o CSV pelo nome das colunas
                reader = csv.DictReader(f)
                for row in reader:
                    # Adiciona a tupla com os dados relevantes ao conjunto
                    agendados.add((row['especialidade'], row['doutor'], row['horario']))
        except Exception as e:
            # Em caso de erro, imprime no console e retorna um conjunto vazio
            print(f"Erro ao carregar o arquivo CSV de agendamentos: {e}")
            return set()
        return agendados

    def listar_especialidades(self):
        """Carrega os dados e retorna uma lista com os nomes das especialidades."""
        agendamentos = self._carregar_dados()
        if agendamentos:
            return list(agendamentos.keys())
        return []

    def listar_por_especialidade(self, especialidade: str):
        """Lista os horários disponíveis para uma especialidade, excluindo os já agendados."""
        todos_horarios = self._carregar_dados()
        consultas_agendadas = self._carregar_consultas_agendadas()

        # Garante que a busca pela especialidade não seja case-sensitive
        especialidade_encontrada = next((k for k in todos_horarios if k.upper() == especialidade.upper()), None)
        
        if not especialidade_encontrada:
            return None

        horarios_da_especialidade = todos_horarios[especialidade_encontrada]
        horarios_disponiveis = {}

        for medico, horarios in horarios_da_especialidade.items():
            horarios_livres_do_medico = []
            for horario in horarios:
                # Verifica se a tupla (especialidade, médico, horário) NÃO está no set de agendados
                if (especialidade_encontrada, medico, horario) not in consultas_agendadas:
                    horarios_livres_do_medico.append(horario)
            
            # Adiciona o médico à lista de resultados apenas se ele tiver horários livres
            if horarios_livres_do_medico:
                horarios_disponiveis[medico] = horarios_livres_do_medico

        return horarios_disponiveis if horarios_disponiveis else None

    def adicionar_horario(self, payload: HorarioPostPayload):
        """Adiciona um novo horário disponível para um médico."""
        agendamentos = self._carregar_dados()
        correct_key = next((k for k in agendamentos if k.upper() == payload.especialidade.upper()), payload.especialidade)
        
        agendamentos.setdefault(correct_key, {}).setdefault(payload.medico, [])

        if payload.horario in agendamentos[correct_key][payload.medico]:
            return False # Indica que o horário já existe
        
        agendamentos[correct_key][payload.medico].append(payload.horario)
        agendamentos[correct_key][payload.medico].sort()
        self._salvar_dados(agendamentos)
        return True # Indica sucesso

    def remover_horario_agendado(self, especialidade: str, medico: str, horario: str):
        """Remove um horário da lista de horários disponíveis (não do CSV)."""
        agendamentos = self._carregar_dados()
        correct_key = next((k for k in agendamentos if k.upper() == especialidade.upper()), None)

        if not (correct_key and medico in agendamentos.get(correct_key, {}) and horario in agendamentos[correct_key][medico]):
            return False

        agendamentos[correct_key][medico].remove(horario)
        if not agendamentos[correct_key][medico]:
            del agendamentos[correct_key][medico]
        if not agendamentos[correct_key]:
            del agendamentos[correct_key]
        
        self._salvar_dados(agendamentos)
        return True

# Singleton
agenda_service_instance = AgendaService()
def get_agenda_service():
    return agenda_service_instance
