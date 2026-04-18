# Análise do Projeto NexaFiscal e Prontidão para Migração GCP

Este documento apresenta uma análise de alto nível da arquitetura e da estrutura de código atual do projeto **NexaFiscal**, bem como um roteiro e avaliação de prontidão (Readiness Assessment) para a migração da infraestrutura atual (Replit) para o **Google Cloud Platform (GCP)**, com foco no uso de Cloud Run, Document AI, Vertex AI e Cloud SQL.

---

## 1. Arquitetura e Estrutura de Código Atual

O NexaFiscal é uma aplicação complexa e bem estruturada em Python, atuando primariamente como um sistema de extração inteligente e análise instantânea de documentos fiscais (NFe, NFCe, SAT, CTe, NFSe).

A arquitetura atual é dividida nas seguintes camadas principais:

### 1.1 Frontend (Streamlit)
- **Tecnologia:** Streamlit (`app.py`, `pages/`).
- **Função:** Fornece a interface visual de usuário (GUI) interativa para upload de arquivos, exibição de dashboards (com `plotly`), chat com agentes e configurações de impostos.
- **Design:** Utiliza navegação multipáginas nativa ou pseudo-nativa. A comunicação com as lógicas complexas acontece tanto através de integrações diretas com funções de backend (ex: `workflow_graph.py`) quanto via chamadas API para o servidor FastAPI.

### 1.2 Backend e API REST (FastAPI)
- **Tecnologia:** FastAPI (`api/main.py`, `api/routes/`).
- **Função:** Expõe um servidor REST para processamento assíncrono, processamento em lote (batch processing via workers de background) e rotas de integração do sistema (como manipulação de documentos, Sefaz, filas, e sessões de chat).
- **Design:** Define uma clara separação de rotas e faz interface com os serviços de negócios (`services/`).

### 1.3 Orquestração de Agentes (LangGraph)
- **Tecnologia:** LangGraph (`workflow_graph.py`).
- **Função:** O coração da aplicação é um workflow de agentes baseado em grafos de estado. O processo (`process_invoice`) passa por quatro agentes principais (`agents/`):
  1. **Classificação (`classification_agent.py`):** Identifica o tipo do documento.
  2. **Extração (`extraction_agent.py`):** Utiliza LLM Vision / OCR para estruturar dados da nota fiscal.
  3. **Validação (`validation_agent.py`):** Valida a consistência fiscal (CNPJ, chaves de acesso).
  4. **Integração (`integration_agent.py`):** Interface para operações externas como Sefaz.

### 1.4 Extração e OCR (Local + IA Externa)
- **Ferramentas:** `pytesseract` (Tesseract), `pdf2image` (Poppler), `pypdfium2`, `pdfplumber` (`utils/file_processor.py`).
- **Modelos:** A Groq API (`meta-llama/llama-4-scout-17b-16e-instruct`) é o padrão atual para inferência em visão computacional e extração de texto multimodal (via `extraction_agent.py`).

### 1.5 Persistência e Dados (Banco Relacional)
- **Tecnologia:** PostgreSQL, SQLAlchemy (ORM) (`database/`).
- **Função:** Armazena sessões de chat, logs de processamento de agentes, configuração, estado das filas de processamento e dados brutos.

---

## 2. Prontidão para Migração: GCP (Google Cloud Platform)

Atualmente, o projeto é altamente acoplado a bibliotecas de sistema operacional (Tesseract, Poppler) que dificultam a portabilidade e a escalabilidade (a execução em ambientes sem as bibliotecas binárias de sistema falha). A migração para a nuvem gerenciada do Google resolverá esses problemas estruturais.

### 2.1 Análise de Componentes para o GCP

#### **A. Substituição do OCR/Extração Local pelo Document AI (GCP)**
- **Estado Atual:** O `utils/file_processor.py` depende de `pytesseract` e Poppler para gerar o texto bruto, que é depois passado para o Llama na Groq. Esta é uma operação "pesada" para o backend e sujeita a falhas em containers com OS compactos.
- **Plano de Migração:**
  - Substituir o stack do `file_processor.py` pela SDK do Google Cloud (e.g., `google-cloud-documentai`).
  - O **Document AI** fornece parsers genéricos de formulários e OCR altamente fidedigno sem precisar instalar dependências de sistema operacional no container.
  - Isso reduz drasticamente o tamanho do contêiner Docker e aumenta a velocidade e precisão no OCR de PDFs nativos e digitalizados.

#### **B. Substituição dos Modelos de IA pelo Vertex AI (Gemini)**
- **Estado Atual:** O agente de extração (`extraction_agent.py`) constrói um payload multimodal e dispara para a `Groq`.
- **Plano de Migração:**
  - Utilizar a biblioteca `google-cloud-aiplatform` (Vertex AI) para integrar os modelos **Gemini 1.5 Pro/Flash**.
  - O Gemini possui excelente capacidade de compreensão visual (multimodal) nativa. Pode-se passar o documento (PDF ou Imagem) diretamente para o Gemini via Vertex AI em conjunto com as diretrizes do `extraction_prompt`, consolidando a etapa do OCR e da Estruturação de dados num serviço escalável do Google.

#### **C. Implantação Serverless com o Cloud Run**
- **Estado Atual:** Hospedado no Replit, com scripts baseados em servidor único executando o Streamlit (`porta 5000`) e o FastAPI (`porta 8000`) simultaneamente.
- **Plano de Migração:**
  - O **Cloud Run** é perfeito para o caso, mas exige a separação clara em contêineres Docker.
  - **Refatoração:** Será necessário criar dois `Dockerfiles`:
    1. Um para a **API FastAPI** (backend responsável pelos processamentos pesados do LangGraph, workers em background).
    2. Um para o **Frontend Streamlit** (configurando URLs estáticas para as chamadas do backend, que atualmente estão muitas vezes "hardcoded" apontando para localhost ou importando a lógica local do backend).
  - Como o Cloud Run trata o contêiner de forma "Stateless" e pode escalar a zero instâncias ou múltiplas, não é recomendado que o Streamlit importe funções como `process_invoice` diretamente, mas sim faça sempre o disparo da requisição HTTP ao serviço do FastAPI. Isso necessitará de refatoração no `app.py`.

#### **D. Banco de Dados: Cloud SQL (PostgreSQL)**
- **Estado Atual:** Banco de dados PostgreSQL rodando sob a infraestrutura do Replit, configurado via variável de ambiente `DATABASE_URL`.
- **Plano de Migração:**
  - Fácil migração. O provisionamento de um **Cloud SQL para PostgreSQL** requer apenas que a nova instância forneça a connection string na variável de ambiente `DATABASE_URL`. O uso atual do SQLAlchemy já garante a portabilidade de dados e queries.

### 2.2 Requisitos Funcionais Futuros

A memória de requisitos mencionou preocupações futuras como **LGPD (PII Protection)** e prevenção de **Prompt Injection**. O ecossistema GCP facilita a adequação a ambos:
- **LGPD/PII:** O Google Cloud Data Loss Prevention (DLP) ou funcionalidades embutidas do próprio Document AI podem aplicar "redaction" (descaracterização/tarja) automática sobre CPFs ou dados pessoais antes de persistir as notas fiscais no banco.
- **Prompt Injection:** O Vertex AI possui *Safety Settings* embutidas na API que prevêem a detecção e proteção avançada contra uso malicioso de IA, blindando o pipeline de LangGraph.

---

## 3. Resumo da Refatoração Necessária (Roadmap de Execução)

Para concretizar a migração para o GCP, sugerem-se as seguintes etapas de código:

1. **Desacoplamento do Frontend/Backend:** No `app.py` e páginas associadas (Streamlit), alterar toda chamada direta aos métodos como `process_invoice` para chamadas web (`requests.post(API_URL)`). O Frontend será puramente um cliente.
2. **Containerização (Docker):**
   - Escrever `Dockerfile.frontend` expondo a porta do Streamlit e inicializando sem código dependente de processamento local.
   - Escrever `Dockerfile.backend` expondo FastAPI, contendo as bibliotecas do LangGraph. Aqui **removemos** do requirements.txt e das dependências os softwares Tesseract, PDF2Image, Poppler.
3. **Atualização da Camada de IA:**
   - Modificar `utils/file_processor.py` e `agents/extraction_agent.py`.
   - Incluir dependência `google-cloud-documentai` e `google-cloud-aiplatform`.
   - Implementar os clientes e credenciais para o Vertex AI no lugar de `Groq`.
4. **Deploy no Cloud Run:**
   - Construir e enviar as imagens para o Artifact Registry.
   - Deploy dos 2 serviços via Cloud Run e conexão segura (VPC Connector) com uma instância recém-criada do Cloud SQL.