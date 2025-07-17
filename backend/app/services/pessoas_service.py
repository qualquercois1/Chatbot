# app/services/pessoas_service.py
import csv
from app.config import URL_CADASTROS, URL_CONSULTAS, CABECALHO_CADASTROS
from app.schemas import CadastroPessoaPayload, ConsultaPayload
from .agenda_service import AgendaService, get_agenda_service 
from typing import Optional
from fastapi import Depends

class PessoasService:
    def __init__(self, agenda_service: AgendaService):
        self.agenda_service = agenda_service

    def _cpf_existe(self, cpf: str, url_arquivo: str) -> bool:
        try:
            with open(url_arquivo, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for linha in reader:
                    if linha and linha.get('cpf', '').strip() == cpf:
                        return True
            return False
        except FileNotFoundError:
            return False
        
    def buscar_por_cpf(self, cpf: str) -> Optional[CadastroPessoaPayload]:

        try:
            with open(URL_CADASTROS, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for linha in reader:
                    if linha and linha.get('cpf', '').strip() == cpf:
                        dados = {
                            "nome": linha.get("nome", "").strip(),
                            "idade": int(linha.get("idade", "0").strip() or 0),
                            "sexo": linha.get("sexo", "").strip(),
                            "cpf": linha.get("cpf", "").strip(),
                            "telefone": linha.get("telefone", "").strip(),
                            "email": linha.get("email", "").strip(),
                        }
                        return CadastroPessoaPayload(**dados)
        except FileNotFoundError:
            return None
        return None

    def cadastrar(self, payload: CadastroPessoaPayload):
        if self._cpf_existe(payload.cpf, URL_CADASTROS):
            return False # CPF já existe
        
        nova_linha = [payload.nome, payload.idade, payload.sexo, payload.cpf, payload.telefone, payload.email]
        with open(URL_CADASTROS, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(nova_linha)
        return True # Sucesso
    
    def deletar_por_cpf(self, cpf: str) -> bool:
        linhas_para_manter = []
        pessoa_encontrada = False
        try:
            with open(URL_CADASTROS, mode='r', newline='', encoding='utf-8') as f:
                reader = list(csv.reader(f)) 
                if not reader: 
                    return False
                
                cabecalho = reader[0]
                linhas_para_manter.append(cabecalho)

                # Itera a partir da segunda linha (pós-cabeçalho)
                for linha in reader[1:]:
                    # A coluna do CPF é a 3 (índice 3)
                    if linha and len(linha) > 3 and linha[3].strip() == cpf:
                        pessoa_encontrada = True
                    else:
                        linhas_para_manter.append(linha)
            
            if not pessoa_encontrada:
                return False # Se não encontrou o CPF, retorna False

            # Se encontrou, reescreve o arquivo apenas com as linhas para manter
            with open(URL_CADASTROS, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(linhas_para_manter)
            
            return True # Retorna True indicando sucesso
            
        except FileNotFoundError:
            return False

    def agendar_consulta(self, payload: ConsultaPayload):
        # 1. Responsabilidade do PessoasService: Validar CPF no seu arquivo (cadastros.csv)
        if not self._cpf_existe(payload.cpf, URL_CADASTROS):
            raise ValueError(f"CPF '{payload.cpf}' não encontrado.")
        
        # 2. Responsabilidade do PessoasService: Validar se horário já foi agendado (pessoa_horario.csv)
        try:
            with open(URL_CONSULTAS, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for consulta in reader:
                    if consulta and consulta.get('horario', '').strip() == payload.horario:
                        raise ValueError(f"Horário '{payload.horario}' já está ocupado.")
        except FileNotFoundError:
            # Se o arquivo não existe, não há consultas, então podemos continuar.
            pass

        # 3. Responsabilidade do PessoasService: PEDIR ao AgendaService para fazer sua parte.
        # Ele não sabe como o AgendaService remove o horário, ele apenas confia e chama o método.
        sucesso_remocao = self.agenda_service.remover_horario_agendado(
            especialidade=payload.especialidade,
            medico=payload.medico,
            horario=payload.horario
        )
        
        if not sucesso_remocao:
            raise ValueError("Horário não disponível ou não encontrado na agenda para remoção.")

        # 4. Responsabilidade do PessoasService: Registrar a nova consulta no seu arquivo (pessoa_horario.csv)
        nova_consulta = [payload.cpf, payload.especialidade, payload.medico, payload.horario]
        with open(URL_CONSULTAS, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(nova_consulta)

        return True

# Injeção de Dependência entre serviços
def get_pessoas_service(agenda_service: AgendaService = Depends(get_agenda_service)):
    from .agenda_service import agenda_service_instance
    return PessoasService(agenda_service_instance)