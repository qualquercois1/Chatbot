# app/schemas.py

from datetime import datetime as DatetimeClass, datetime  # MUDAR PARA ESTA LINHA

from pydantic import BaseModel
from typing import Optional

class HorarioPostPayload(BaseModel):
    especialidade: str
    medico: str
    horario: str

class HorarioDeletePayload(BaseModel):
    especialidade: str
    medico: str
    horario: Optional[str] = None

class CadastroPessoaPayload(BaseModel):
    nome: str
    idade: int
    sexo: str
    cpf: str
    telefone: str
    email: str

class ConsultaPayload(BaseModel):
    cpf_paciente: str
    especialidade: str
    id_medico: int
    doutor: str
    data_hora: str

class AgendarConsultaPayload(BaseModel):
    cpf_paciente: str
    especialidade: str
    id_medico: int # ID numérico do médico (para referência interna)
    doutor: str # Nome do doutor
    data_hora: DatetimeClass # Use a classe importada aqui

class AgendarExamePayload(BaseModel):
    cpf_paciente: str
    tipo_exame: str
    local_exame: str
    data_hora: DatetimeClass