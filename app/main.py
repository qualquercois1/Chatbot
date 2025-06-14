from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from typing import Optional

URL= 'data/agendamentos.json'

app = FastAPI(
    title="API de Agendamentos",
    description="API para gerenciar horários de consultas médicas.",
    version="1.0.0"
)

def carregarDados(URL= 'data/agendamentos.json'):
    with open("data/agendamentos.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
        return dados
    
def salvar_dados(dados: dict):
    with open(URL, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

class HorarioPayload(BaseModel):
    especialidade: str
    medico: str
    horario: str

class HorarioDeletePayload(BaseModel):
    especialidade: str
    medico: str
    horario: Optional[str] = None

@app.get("/")
def Home():
    return "Pagina inicial"

@app.get("/agenda/{especialidade}", status_code=201)
def ListarHorarios(especialidade: str):
    agendamentos = carregarDados()
    agend_temp = agendamentos.get(especialidade)
    if agend_temp:
        return agend_temp
    return {"detail":"Não possui horarios livres"}
    
@app.post("/agendas/horarios")
def adicionar_horarios(payload: HorarioPayload):
    agendamentos = carregarDados()
    especialidade = payload.especialidade
    nome_medico = payload.medico
    novo_horario = payload.horario

    if especialidade not in agendamentos:
        agendamentos[especialidade] = {}
    
    if nome_medico not in agendamentos[especialidade]:
        agendamentos[especialidade][nome_medico] = []

    if novo_horario not in agendamentos[especialidade][nome_medico]:
        agendamentos[especialidade][nome_medico].append(novo_horario)
        agendamentos[especialidade][nome_medico].sort()
    else:
        raise HTTPException(status_code=409, detail=f"O horário '{novo_horario}' já existe para este médico.")

    salvar_dados(agendamentos)
    
    return {"detail": f"Horário adicionado com sucesso para '{nome_medico}' em {especialidade}."}

@app.delete("/agendas/horarios")
def DeletarHorarioMedico(payload: HorarioDeletePayload):
    agendamentos = carregarDados()

    especialidade = payload.especialidade
    nome_medico = payload.medico
    horario_para_deletar = payload.horario

    if especialidade not in agendamentos:
        raise HTTPException(status_code=404, detail=f"Especialidade '{especialidade}' não encontrada.")
    if nome_medico not in agendamentos[especialidade]:
        raise HTTPException(status_code=404, detail=f"Médico '{nome_medico}' não encontrado em {especialidade}.")
    
    if horario_para_deletar:
        if horario_para_deletar not in agendamentos[especialidade][nome_medico]:
            raise HTTPException(status_code=404, detail=f"Horário '{horario_para_deletar}' não encontrado para este médico.")
        
        agendamentos[especialidade][nome_medico].remove(horario_para_deletar)
        
        if not agendamentos[especialidade][nome_medico]:
            del agendamentos[especialidade][nome_medico]
        
        mensagem = f"Horário '{horario_para_deletar}' do médico '{nome_medico}' foi removido com sucesso."

    else:
        del agendamentos[especialidade][nome_medico]
        mensagem = f"Médico '{nome_medico}' e todos os seus horários foram removidos de {especialidade}."

    if not agendamentos[especialidade]:
        del agendamentos[especialidade]

    salvar_dados(agendamentos)
    return {"detail": mensagem}