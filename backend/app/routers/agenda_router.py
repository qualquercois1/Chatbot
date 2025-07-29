# app/routers/agenda_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.agenda_service import AgendaService, get_agenda_service
from app.schemas import HorarioPostPayload, HorarioDeletePayload

router = APIRouter(prefix="/agendas", tags=["Gerenciamento de Agenda"])

@router.get("/especialidades", response_model=list[str], summary="Lista todas as especialidades disponíveis")
def obter_especialidades(service: AgendaService = Depends(get_agenda_service)):
    """
    Retorna uma lista com todas as chaves de especialidade de primeiro nível 
    do arquivo de agendamentos.
    """
    return service.listar_especialidades()

@router.get("/{especialidade}")
def listar_horarios(especialidade: str, service: AgendaService = Depends(get_agenda_service)):
    horarios = service.listar_por_especialidade(especialidade)
    if horarios is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Especialidade não encontrada.")
    return horarios

@router.post("/horarios", status_code=status.HTTP_201_CREATED)
def adicionar_horarios(payload: HorarioPostPayload, service: AgendaService = Depends(get_agenda_service)):
    sucesso = service.adicionar_horario(payload)
    if not sucesso:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Horário já existe.")
    return {"detail": "Horário adicionado com sucesso."}

@router.delete("/horarios")
def deletar_horario_medico(payload: HorarioDeletePayload, service: AgendaService = Depends(get_agenda_service)):
    sucesso = service.remover_horario_agendado(payload)
    if not sucesso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Especialidade ou médico não encontrado.")
    return {"detail": "Operação de deleção concluída."}
