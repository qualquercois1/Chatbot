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

Antes de executar o projeto faça:
# Crie um ambiente virtual
*python -m venv venv*
# Ative o ambiente virtual
*.\venv\Scripts\activate*
# Instale as extensões necessarias
*pip install -r requirements.txt*

enfim quando aparecer (venv) no seu terminal significa que o ambiente virtual está funcionando, agora

# Execute a api
Repositorio: Chatbot/backend/
Comando: uvicorn app.main:app --reload

se aparecer um comando como "Inicialização concluida" então a api está rodando 

em outro terminal execute o ambiente virtual novamente

# Teste a parte do gemini
Repositorio: Chatbot/backend/app
Comando: python -m services.gemini_service

lembre de colocar a chave da api do gemini em um arquivo .env no diretorio raiz com o seguinte nome da variavel *API_KEY*

para desativar o ambiente virtual utilize *deactivate*