# API de Gerenciamento de Consultas Médicas com Chatbot

Esta é uma API desenvolvida em FastAPI para gerenciar o cadastro de pacientes, horários de médicos e o agendamento de consultas, com o objetivo de ser integrada a um serviço de chatbot com a API do Gemini.

## Tecnologias Utilizadas

- **Python 3.11+**
- **FastAPI:** Framework web para a construção da API.
- **Uvicorn:** Servidor ASGI para executar a API.
- **Google Generative AI:** Para a integração com o serviço de chatbot.
- **Pydantic:** Para validação de dados.

## Configuração do Ambiente

Siga os passos abaixo para configurar e executar o projeto localmente.

1.  **Crie um Ambiente Virtual**
    Na pasta raiz do projeto, crie um ambiente virtual para isolar as dependências:
    ```bash
    python -m venv venv
    ```

2.  **Ative o Ambiente Virtual**
    * No Windows (PowerShell/CMD):
        ```bash
        .\venv\Scripts\activate
        ```
    * No macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
    Seu terminal deverá agora mostrar o prefixo `(venv)`.

3.  **Instale as Dependências**
    Com o ambiente ativo, instale todas as bibliotecas necessárias a partir do arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure a Chave da API**
    Crie um arquivo chamado `.env` na pasta raiz do projeto (`Chatbot/backend/`) e adicione sua chave da API do Gemini:
    
    **.env**
    ```
    API_KEY="SUA_CHAVE_SECRETA_DO_GEMINI_AQUI"
    ```

## Executando a Aplicação

Para que o sistema completo funcione, você precisará de **dois terminais abertos** com o ambiente virtual ativado em ambos.

#### Terminal 1: Execute a API

1.  Navegue até a pasta `Chatbot/backend/`.
2.  Ative o ambiente virtual: `.\venv\Scripts\activate`
3.  Inicie o servidor da API com Uvicorn:
    ```bash
    uvicorn app.main:app --reload
    ```
4.  Você verá uma mensagem indicando que o servidor está rodando, geralmente em `http://127.0.0.1:8000`.

#### Terminal 2: Execute o Serviço do Gemini

1.  Abra um novo terminal.
2.  Navegue até a pasta `Chatbot/backend/app`.
3.  Ative o ambiente virtual: `.\venv\Scripts\activate`
4.  Execute o script do chatbot:
    ```bash
    python -m services.gemini_service
    ```
5.  Interaja com o chatbot conforme as instruções que aparecerão no terminal.

## Documentação da API (Endpoints)

A seguir estão detalhados os endpoints disponíveis na API.

---

### Pessoas e Cadastros

Endpoints relacionados ao gerenciamento de informações de pacientes.

#### 1. Cadastrar Nova Pessoa

- **Método:** `POST`
- **Rota:** `/pessoas/cadastro`
- **Descrição:** Cadastra um novo paciente no sistema.
- **Corpo da Requisição (JSON):**
    ```json
    {
      "nome": "João da Silva",
      "idade": 35,
      "sexo": "Masculino",
      "cpf": "12345678900",
      "telefone": "61999998888",
      "email": "joao.silva@example.com"
    }
    ```
- **Resposta de Sucesso (201 Created):**
    ```json
    {
      "detail": "Pessoa cadastrada com sucesso."
    }
    ```
- **Resposta de Erro (409 Conflict):**
    ```json
    {
      "detail": "CPF já cadastrado."
    }
    ```

#### 2. Obter Pessoa por CPF

- **Método:** `GET`
- **Rota:** `/pessoas/{cpf}`
- **Descrição:** Busca e retorna os dados de um paciente a partir do seu CPF.
- **Resposta de Sucesso (200 OK):**
    ```json
    {
      "nome": "João da Silva",
      "idade": 35,
      "sexo": "Masculino",
      "cpf": "12345678900",
      "telefone": "61999998888",
      "email": "joao.silva@example.com"
    }
    ```
- **Resposta de Erro (404 Not Found):**
    ```json
    {
      "detail": "Pessoa com CPF '12345678900' não encontrada."
    }
    ```

#### 3. Deletar Pessoa por CPF

- **Método:** `DELETE`
- **Rota:** `/{cpf}`
- **Descrição:** Deleta o cadastro de um paciente do sistema.
- **Resposta de Sucesso (200 OK):**
    ```json
    {
      "detail": "Pessoa com CPF '12345678900' deletada com sucesso."
    }
    ```

---

### Agendamento de Consultas

#### 1. Agendar Nova Consulta

- **Método:** `POST`
- **Rota:** `/consultas`
- **Descrição:** Agenda uma nova consulta para um paciente com um médico em um horário específico.
- **Corpo da Requisição (JSON):**
    ```json
    {
        "cpf_paciente": "12345678900",
        "especialidade": "Cardiologia",
        "id_medico": 1,
        "data_hora": "2025-08-15T10:00:00"
    }
    ```
- **Resposta de Sucesso (201 Created):**
    ```json
    {
        "detail": "Consulta agendada com sucesso."
    }
    ```
- **Resposta de Erro (400 Bad Request):**
    ```json
    {
        "detail": "Mensagem de erro específica (ex: Horário não disponível)."
    }
    ```

---

### Gerenciamento de Agenda

Endpoints para visualizar e gerenciar os horários dos médicos.

#### 1. Listar Horários por Especialidade

- **Método:** `GET`
- **Rota:** `/agendas/{especialidade}`
- **Descrição:** Lista todos os horários de atendimento disponíveis para uma dada especialidade.
- **Resposta de Sucesso (200 OK):**
    ```json
    [
      {
        "medico": "Dr. Carlos Andrade",
        "id_medico": 1,
        "horarios_disponiveis": [
          "2025-08-15T10:00:00",
          "2025-08-15T11:00:00"
        ]
      }
    ]
    ```

#### 2. Adicionar Horário de Atendimento

- **Método:** `POST`
- **Rota:** `/agendas/horarios`
- **Descrição:** Permite que um médico adicione um novo slot de horário à sua agenda.
- **Corpo da Requisição (JSON):**
    ```json
    {
        "especialidade": "Cardiologia",
        "id_medico": 1,
        "data_hora": "2025-08-15T14:00:00"
    }
    ```
- **Resposta de Sucesso (201 Created):**
    ```json
    {
        "detail": "Horário adicionado com sucesso."
    }
    ```

#### 3. Deletar Horário de Atendimento

- **Método:** `DELETE`
- **Rota:** `/agendas/horarios`
- **Descrição:** Remove um horário específico da agenda de um médico (útil quando um horário é agendado ou cancelado).
- **Corpo da Requisição (JSON):**
    ```json
    {
        "especialidade": "Cardiologia",
        "id_medico": 1,
        "data_hora": "2025-08-15T14:00:00"
    }
    ```
- **Resposta de Sucesso (200 OK):**
    ```json
    {
        "detail": "Operação de deleção concluída."
    }
    ```

## Dicas Adicionais

- Para desativar o ambiente virtual em qualquer terminal, use o comando:
    ```bash
    deactivate
    ```