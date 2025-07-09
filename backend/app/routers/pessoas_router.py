# app/routers/pessoas_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.pessoas_service import PessoasService, get_pessoas_service
from app.schemas import CadastroPessoaPayload, ConsultaPayload

router = APIRouter(tags=["Pessoas e Consultas"])

@router.post("/pessoas/cadastro", status_code=status.HTTP_201_CREATED)
def cadastrar_pessoa(payload: CadastroPessoaPayload, service: PessoasService = Depends(get_pessoas_service)):
    sucesso = service.cadastrar(payload)
    if not sucesso:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CPF já cadastrado.")
    return {"detail": "Pessoa cadastrada com sucesso."}

@router.delete("/{cpf}")
def deletar_pessoa(cpf: str, service: PessoasService = Depends(get_pessoas_service)):
    sucesso = service.deletar_por_cpf(cpf)
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pessoa com CPF '{cpf}' não encontrada."
        )
    
    return {"detail": f"Pessoa com CPF '{cpf}' deletada com sucesso."}

@router.post("/consultas", status_code=status.HTTP_201_CREATED)
def agendar_consulta(payload: ConsultaPayload, service: PessoasService = Depends(get_pessoas_service)):
    try:
        service.agendar_consulta(payload)
        return {"detail": "Consulta agendada com sucesso."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

