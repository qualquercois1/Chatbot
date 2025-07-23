Objetivos

Criar uma api para gerir consultas utilizando chatbot

Endpoints:
- localhost/agendas/especialidade (GET)
    descrição:
        Lista os horarios livres de acordo com uma especialidade.
- localhost/agendas/horarios (POST)
    descrição:
        Adiciona um horário de atendimento para uma determinada especialidade e medico.
- localhost/agendas/ (DELETE)
    descrição: 
        Deleta um horario de uma especialidade.

# Executa a api
Repositorio: Chatbot/backend/app
Comando:
uvicorn main:app --reload
ou
uvicorn app.main:app --reload

# Testar a parte do gemini
Repositorio: Chatbot/backend/app 
Comando: python -m services.gemini_service

lembre de colocar a chave da api do gemini em um arquivo .env no diretorio raiz com o seguinte nome da variavel *API_KEY*