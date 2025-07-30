# app/routers/pessoas_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.pessoas_service import PessoasService, get_pessoas_service
from app.schemas import CadastroPessoaPayload, ConsultaPayload

router = APIRouter(tags=["Pessoas e Consultas"])

@router.get("/pessoas/{cpf}", response_model=CadastroPessoaPayload)
def obter_pessoa_por_cpf(cpf: str, service: PessoasService = Depends(get_pessoas_service)):
    pessoa = service.buscar_por_cpf(cpf)
    if not pessoa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pessoa com CPF '{cpf}' não encontrada."
        )
    return pessoa

### NOVO ENDPOINT ADICIONADO AQUI ###
@router.get("/pessoas/{cpf}/consultas_agendadas", response_model=list[ConsultaPayload])
def obter_consultas_por_cpf(cpf: str, service: PessoasService = Depends(get_pessoas_service)):
    """Busca e retorna todas as consultas agendadas para um CPF específico."""
    consultas = service.buscar_consultas_por_cpf(cpf)
    # A função de serviço já retorna uma lista (vazia ou não), então podemos retorná-la diretamente.
    return consultas

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
