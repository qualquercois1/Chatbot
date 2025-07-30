# app/routers/exames_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.exames_service import ExamesService, get_exames_service
from app.schemas import AgendarExamePayload # Importa o novo schema

router = APIRouter(prefix="/exames", tags=["Gerenciamento de Exames"])

@router.get("/tipos", response_model=list[str], summary="Lista todos os tipos de exames disponíveis")
def obter_tipos_exames(service: ExamesService = Depends(get_exames_service)):
    """
    Retorna uma lista com todos os tipos de exames disponíveis no sistema.
    """
    return service.listar_tipos_exames()

@router.get("/{tipo_exame}", summary="Lista horários disponíveis para um tipo de exame por local")
def listar_horarios_exame(tipo_exame: str, service: ExamesService = Depends(get_exames_service)):
    """
    Retorna os horários disponíveis para um tipo de exame específico, agrupados por local.
    Exclui horários que já passaram.
    """
    horarios = service.listar_horarios_exame_por_local(tipo_exame)
    if horarios is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de exame '{tipo_exame}' não encontrado ou sem horários disponíveis."
        )
    return horarios

@router.post("/agendar", status_code=status.HTTP_201_CREATED, summary="Agenda um novo exame")
def agendar_exame(payload: AgendarExamePayload, service: ExamesService = Depends(get_exames_service)):
    """
    Agenda um novo exame para o paciente.
    """
    sucesso = service.agendar_novo_exame(payload)
    if not sucesso:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não foi possível agendar o exame.")
    return {"detail": "Exame agendado com sucesso."}

@router.get("/{cpf}/exames_agendados", summary="Lista exames agendados para um CPF específico")
def listar_exames_agendados(cpf: str, service: ExamesService = Depends(get_exames_service)):
    """
    Retorna a lista de exames agendados para um CPF específico.
    """
    exames = service.buscar_exames_agendados_por_cpf(cpf)
    if not exames:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum exame agendado encontrado para o CPF '{cpf}'."
        )
    return exames