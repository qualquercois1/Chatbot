# app/schemas.py
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