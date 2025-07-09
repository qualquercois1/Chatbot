# app/services/agenda_service.py
import json
from app.config import URL_AGENDAMENTOS
from app.schemas import HorarioPostPayload, HorarioDeletePayload

class AgendaService:
    def _carregar_dados(self):
        try:
            with open(URL_AGENDAMENTOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _salvar_dados(self, dados: dict):
        with open(URL_AGENDAMENTOS, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def listar_por_especialidade(self, especialidade: str):
        agendamentos = self._carregar_dados()
        for key in agendamentos.keys():
            if key.upper() == especialidade.upper():
                return agendamentos[key]
        return None # Retorna None se não encontrar

    def adicionar_horario(self, payload: HorarioPostPayload):
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