import json
import os
import csv
from fastapi import Depends
from app.config import URL_AGENDAMENTOS, URL_CONSULTAS 
from app.schemas import HorarioPostPayload 

class AgendaService:
    def __init__(self):
        self.db_path = URL_AGENDAMENTOS
        self.csv_path = URL_CONSULTAS

    def _carregar_dados(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _salvar_dados(self, dados: dict):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def _carregar_consultas_agendadas(self):
        agendados = set()
        try:
            if not os.path.exists(self.csv_path):
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['cpf', 'especialidade', 'doutor', 'horario'])
                return agendados

            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    agendados.add((row['especialidade'], row['doutor'], row['horario']))
        except Exception as e:
            print(f"Erro ao carregar o arquivo CSV de agendamentos: {e}")
            return set()
        return agendados

    def listar_especialidades(self):
        agendamentos = self._carregar_dados()
        if agendamentos:
            return list(agendamentos.keys())
        return []

    def listar_por_especialidade(self, especialidade: str):
        todos_horarios = self._carregar_dados()
        consultas_agendadas = self._carregar_consultas_agendadas()

        especialidade_encontrada = next((k for k in todos_horarios if k.upper() == especialidade.upper()), None)
        
        if not especialidade_encontrada:
            return None

        horarios_da_especialidade = todos_horarios[especialidade_encontrada]
        horarios_disponiveis = {}

        for medico, horarios in horarios_da_especialidade.items():
            horarios_livres_do_medico = []
            for horario in horarios:
                if (especialidade_encontrada, medico, horario) not in consultas_agendadas:
                    horarios_livres_do_medico.append(horario)
            
            if horarios_livres_do_medico:
                horarios_disponiveis[medico] = horarios_livres_do_medico

        return horarios_disponiveis if horarios_disponiveis else None

    def adicionar_horario(self, payload: HorarioPostPayload):
        agendamentos = self._carregar_dados()
        correct_key = next((k for k in agendamentos if k.upper() == payload.especialidade.upper()), payload.especialidade)
        
        agendamentos.setdefault(correct_key, {}).setdefault(payload.medico, [])

        if payload.horario in agendamentos[correct_key][payload.medico]:
            return False 
        
        agendamentos[correct_key][payload.medico].append(payload.horario)
        agendamentos[correct_key][payload.medico].sort()
        self._salvar_dados(agendamentos)
        return True 

    def remover_horario_agendado(self, especialidade: str, medico: str, horario: str):
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

agenda_service_instance = AgendaService()
def get_agenda_service():
    return agenda_service_instance
