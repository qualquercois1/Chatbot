# app/services/exames_service.py
import json
import os
from datetime import datetime
from app.config import URL_AGENDAMENTOS_EXAMES, \
    URL_EXAMES_AGENDADOS  # Importa a URL do arquivo JSON de exames e a nova URL de agendamentos
from app.schemas import AgendarExamePayload  # Importa o schema


class ExamesService:
    def __init__(self):
        self.db_path = URL_AGENDAMENTOS_EXAMES
        self.agendamentos_exames_path = URL_EXAMES_AGENDADOS  # Novo caminho para agendamentos

    def _carregar_dados(self) -> dict:
        """Carrega os dados do arquivo JSON de agendamentos de exames disponíveis."""
        try:
            if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                return {}
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar o arquivo JSON de exames disponíveis: {e}")
            return {}

    def _carregar_agendamentos_exames(self) -> list[dict]:
        """Carrega os agendamentos de exames."""
        try:
            if not os.path.exists(self.agendamentos_exames_path) or os.path.getsize(self.agendamentos_exames_path) == 0:
                with open(self.agendamentos_exames_path, 'w', encoding='utf-8') as f:
                    json.dump([], f)  # Lista vazia para agendamentos
                return []
            with open(self.agendamentos_exames_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar o arquivo JSON de exames agendados: {e}")
            return []

    def _salvar_agendamentos_exames(self, agendamentos: list[dict]):
        """Salva os agendamentos de exames no arquivo JSON."""
        try:
            with open(self.agendamentos_exames_path, 'w', encoding='utf-8') as f:
                json.dump(agendamentos, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Erro ao salvar o arquivo JSON de exames agendados: {e}")

    def listar_tipos_exames(self) -> list[str]:
        """Lista todos os tipos de exames disponíveis."""
        dados = self._carregar_dados()
        return list(dados.keys()) if dados else []

    def listar_horarios_exame_por_local(self, tipo_exame: str) -> dict | None:
        """Lista os horários disponíveis para um tipo de exame, por local, filtrando horários passados."""
        todos_exames = self._carregar_dados()

        # Busca o tipo de exame de forma case-insensitive
        tipo_exame_encontrado = next((k for k in todos_exames if k.upper() == tipo_exame.upper()), None)

        if not tipo_exame_encontrado:
            return None

        horarios_do_exame = todos_exames[tipo_exame_encontrado]
        horarios_disponiveis = {}

        agora = datetime.now()

        for local, horarios in horarios_do_exame.items():
            horarios_futuros = []
            for h_str in horarios:
                try:
                    h_dt = datetime.fromisoformat(h_str)
                    if h_dt > agora:
                        horarios_futuros.append(h_str)
                except ValueError:
                    continue

            if horarios_futuros:
                horarios_disponiveis[local] = sorted(horarios_futuros)

        return horarios_disponiveis if horarios_disponiveis else None

    def agendar_novo_exame(self, payload: AgendarExamePayload) -> bool:
        """Agenda um novo exame, removendo o horário disponível e salvando o agendamento."""
        todos_exames = self._carregar_dados()
        tipo_exame_normalizado = next((k for k in todos_exames if k.upper() == payload.tipo_exame.upper()), None)

        if not tipo_exame_normalizado:
            print(f"Erro de agendamento: Tipo de exame '{payload.tipo_exame}' não encontrado.")
            return False

        # Verifica se o local existe para o tipo de exame
        if payload.local_exame not in todos_exames[tipo_exame_normalizado]:
            print(
                f"Erro de agendamento: Local '{payload.local_exame}' não encontrado para o exame '{payload.tipo_exame}'.")
            return False

        horarios_do_local = todos_exames[tipo_exame_normalizado][payload.local_exame]
        horario_para_agendar_str = payload.data_hora.isoformat()  # JÁ ESTÁ EM STRING AQUI

        if horario_para_agendar_str in horarios_do_local:
            # Remove o horário da lista de disponíveis
            horarios_do_local.remove(horario_para_agendar_str)

            # Atualiza os dados de exames disponíveis
            try:
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    json.dump(todos_exames, f, indent=2, ensure_ascii=False)
            except IOError as e:
                print(f"Erro ao salvar o arquivo JSON de exames disponíveis após agendamento: {e}")
                return False

            # Salva o agendamento em um novo arquivo
            agendamentos = self._carregar_agendamentos_exames()

            # CONVERSÃO AQUI: converte o Pydantic model para dict e o datetime para string ISO
            agendamento_dict = payload.dict()
            agendamento_dict['data_hora'] = agendamento_dict[
                'data_hora'].isoformat()  # CONVERTE DATETIME PARA STRING ISO

            agendamentos.append(agendamento_dict)
            self._salvar_agendamentos_exames(agendamentos)

            print(f"Exame de '{payload.tipo_exame}' agendado para {horario_para_agendar_str} em {payload.local_exame}.")
            return True
        else:
            print(
                f"Erro de agendamento: Horário '{horario_para_agendar_str}' não disponível para '{payload.tipo_exame}' em '{payload.local_exame}'.")
            return False

    def buscar_exames_agendados_por_cpf(self, cpf: str) -> list[dict]:
        """Busca e retorna os exames agendados para um CPF específico."""
        agendamentos = self._carregar_agendamentos_exames()
        exames_do_paciente = [
            ag for ag in agendamentos if ag['cpf_paciente'] == cpf
        ]
        return exames_do_paciente


# Singleton: Garante que haja apenas uma instância do serviço
exames_service_instance = ExamesService()


def get_exames_service():
    return exames_service_instance