<div align="center">

<img src="attached_assets/generated_images/NexaFiscal_AI_logo_design_2a3bf643.png" alt="NexaFiscal Logo" width="200"/>

# 📄 NexaFiscal

> **Extração inteligente, análise instantânea**

<p align="center">
  <a href="https://nexafiscal-i2a2-saitosp.replit.app" target="_blank">
    <img src="https://img.shields.io/badge/🚀_Demo_Live-Acesse_Agora-FF5C28?style=for-the-badge" alt="Demo Live"/>
  </a>
  <a href="https://replit.com/@saitosp/nexafiscal-i2a2?s=app" target="_blank">
    <img src="https://img.shields.io/badge/💻_Código-Replit-667881?style=for-the-badge" alt="Ver no Replit"/>
  </a>
</p>

Sistema autônomo de agentes de IA para processamento e análise de documentos fiscais brasileiros (NFe, NFCe, SAT, CTe, NFSe).

---

## 🚀 Acesso Rápido

- **🌐 [Demo Live](https://nexafiscal-i2a2-saitosp.replit.app)** - Experimente o sistema funcionando (sem necessidade de login)
- **💻 [Código no Replit](https://replit.com/@saitosp/nexafiscal-i2a2?s=app)** - Explore e execute o código-fonte

</div>

---

## 📜 Licença

**Este projeto está licenciado sob a [Licença MIT](LICENSE)** - permitindo uso livre, modificação e distribuição.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-00C9A7.svg)](https://github.com/langchain-ai/langgraph)

---

## ⚙️ Configuração Rápida para Avaliadores

> **Para professores e avaliadores**: Siga este guia rápido para configurar as API keys e testar o sistema.

### **Passo 1: Acessar o Painel de Secrets no Replit**

1. No Replit, clique em **"Tools"** (🔧) no menu lateral esquerdo
2. Selecione **"Secrets"** na lista de ferramentas
3. Ou use o atalho: pressione `Ctrl/Cmd + K` e busque por "Secrets"

### **Passo 2: Adicionar as API Keys**

Você precisa de **pelo menos uma** das chaves de IA abaixo. Recomendamos começar com **Groq** (gratuita e rápida):

| Variável de Ambiente | Obrigatória? | Onde Obter | Observações |
|---------------------|--------------|------------|-------------|
| `GROQ_API_KEY` | ✅ **Sim** (pelo menos uma) | [console.groq.com](https://console.groq.com) | **RECOMENDADA** - Gratuita, rápida, excelente para visão computacional |
| `OPENAI_API_KEY` | 🔄 Opcional | [platform.openai.com](https://platform.openai.com) | Alternativa - Modelos GPT-4 Vision |
| `ANTHROPIC_API_KEY` | 🔄 Opcional | [console.anthropic.com](https://console.anthropic.com) | Alternativa - Modelos Claude |

**Outras variáveis (já configuradas automaticamente pelo Replit):**
- `DATABASE_URL` - Criada automaticamente quando você usa PostgreSQL do Replit
- `SESSION_SECRET` - Pode ser qualquer string aleatória (ex: `minha-chave-secreta-123`)
- `SEFAZ_CERT_MASTER_KEY` - Opcional, apenas para integração SEFAZ (gere 32+ caracteres aleatórios)

### **Passo 3: Como Adicionar uma Secret**

1. No painel de Secrets, clique em **"+ New Secret"**
2. Em **"Key"**, digite o nome da variável (ex: `GROQ_API_KEY`)
3. Em **"Value"**, cole a chave que você obteve no site
4. Clique em **"Add Secret"**
5. Repita para outras API keys, se necessário

### **Passo 4: Obter a API Key da Groq (Gratuita)**

1. Acesse [console.groq.com](https://console.groq.com)
2. Faça login ou crie uma conta (gratuita)
3. No menu lateral, clique em **"API Keys"**
4. Clique em **"Create API Key"**
5. Copie a chave gerada
6. Cole no painel de Secrets do Replit como `GROQ_API_KEY`

### **Passo 5: Reiniciar o Servidor**

Após adicionar as API keys:

1. No Replit, vá para a aba **"Tools"** → **"Stop"** (ou pressione o botão Stop ⏹️)
2. Clique em **"Run"** (▶️) novamente para reiniciar com as novas configurações
3. Aguarde o servidor iniciar (aparecerá "You can now view your Streamlit app in your browser")

### **Passo 6: Testar o Sistema**

1. Acesse a aplicação (o Replit abrirá automaticamente em uma nova aba)
2. Faça upload de uma nota fiscal de teste (XML, PDF ou imagem)
3. Clique em **"🚀 Processar"**
4. Se aparecer a extração de dados, está funcionando! ✅

### **🚨 Solução de Problemas**

| Problema | Solução |
|----------|---------|
| Erro "API key not found" | Verifique se adicionou `GROQ_API_KEY` corretamente nas Secrets |
| Servidor não inicia | Reinicie completamente: Stop → Run |
| Extração não funciona | Confirme que a API key está válida no [console.groq.com](https://console.groq.com) |
| Erro de banco de dados | O PostgreSQL será criado automaticamente na primeira execução |

### **💡 Dicas para Avaliação**

- **Upload de Teste**: Use arquivos XML de NFe, NFCe ou SAT para melhor resultado
- **Dashboard**: Acesse "📈 Dashboard de Análise" para ver gráficos e estatísticas
- **Chat**: Experimente o "💬 Chat Inteligente" para fazer perguntas sobre documentos
- **Configuração de Impostos**: Teste adicionar um novo imposto em "⚙️ Configuração de Impostos"
- **Processamento em Lote**: Envie múltiplos arquivos em "📦 Processamento em Lote"

### **📞 Suporte**

Se encontrar dificuldades técnicas durante a avaliação, verifique:
1. Se todas as secrets foram adicionadas corretamente
2. Se o servidor foi reiniciado após adicionar as secrets
3. Se a API key da Groq ainda está válida (elas não expiram, mas podem ser revogadas)

---

## 🎓 Projeto Acadêmico - I2A2

**NexaFiscal** é o projeto de conclusão do curso **I2A2 - Agentes Autônomos com Redes Generativas**, desenvolvido para demonstrar a aplicação prática de agentes autônomos de IA em um contexto real de negócios.

### 🎯 Alinhamento com os Temas do Curso

O projeto implementa os seguintes temas abordados no curso:

#### ✅ **Extração de Dados**
- Processamento de documentos fiscais em múltiplos formatos (XML, PDF, imagens)
- OCR avançado com **pytesseract** para reconhecimento de texto em documentos visuais
- NLP com modelos multimodais (**Groq API - Llama Vision**) para extração inteligente
- Extração automática de: emitente, destinatário, itens, valores e todos os impostos brasileiros
- Sistema configurável que se **adapta automaticamente a mudanças legais** (ex: implementação futura do IVA)

#### ✅ **Validação e Auditoria**
- Validação de CNPJ, CPF e chaves de acesso de NFe
- Verificação de consistência de dados fiscais
- Detecção de anomalias e inconsistências em valores
- Relatórios automáticos de compliance fiscal

#### ✅ **Classificação e Categorização**
- Agente de classificação que identifica automaticamente o tipo de documento
- Suporte a NFe, NFCe, SAT, CTe e NFSe
- Organização inteligente de documentos por tipo e período
- Sistema de batches para rastreamento de grupos de documentos

#### ✅ **Adaptação a Mudanças Legais**
- **Sistema de configuração dinâmica de impostos** (`config/tax_config.json`)
- Interface visual para adicionar novos impostos **sem modificar código**
- Preparado para implementação futura do IVA (CBS/IBS)
- Extração automática de CST (Código de Situação Tributária) para todos os impostos

#### ✅ **Ferramentas Gerenciais**
- Dashboard interativo com **Plotly** para visualização de dados
- Análise de impostos, tendências e compliance
- Relatórios personalizados por período e tipo de documento
- Chat inteligente com padrão Supervisor + Crítico para consultas em linguagem natural

---

## 🚀 Funcionalidades Principais

### 📤 **Upload e Processamento**
- Upload de documentos individuais ou em lote
- Suporte a XML, PDF, JPG, JPEG, PNG
- Processamento assíncrono com rastreamento de progresso
- Importação de tabelas (CSV/XLSX) com mapeamento inteligente de colunas via IA

### 🤖 **Sistema Modular de Agentes**
- **Agente de Classificação**: Identifica automaticamente o tipo de documento
- **Agente de Extração**: Extrai dados estruturados de XML e documentos visuais
- **Agente de Validação**: Valida CNPJ, CPF, chaves de acesso e consistência
- **Agente de Análise**: Gera insights fiscais e detecta anomalias
- **Agente de Integração**: Sincroniza com SEFAZ para manifestação e download de XMLs

### 📊 **Dashboard e Análises**
- Visão geral de documentos processados
- Análise detalhada de impostos (ICMS, IPI, PIS, COFINS, ISS)
- Gráficos interativos de tendências temporais
- Análise de itens mais frequentes
- Indicadores de compliance fiscal
- Filtros por lote, período e tipo de documento

### 🔐 **Integração SEFAZ**
- Gerenciamento seguro de certificados digitais A1
- Criptografia AES-256-GCM para certificados no banco de dados
- Consulta de documentos pendentes (NSU)
- Manifestação automática (Ciência da Operação, Confirmação, Desconhecimento, Operação não Realizada)
- Download automático de XMLs do portal

### ⚙️ **Configuração Dinâmica de Impostos**
- Interface visual para adicionar/editar impostos
- Sistema preparado para IVA e outras mudanças tributárias
- Extração automática de CST para compliance
- Backup automático de configurações

### 💬 **Chat Inteligente**
- Conversação em linguagem natural
- Padrão Supervisor + Crítico para validação de respostas
- Consultas sobre documentos, análises e sistema
- Escopo restrito ao contexto fiscal do projeto

### 📦 **Processamento em Lote**
- Upload e processamento de múltiplos documentos simultaneamente
- Sistema de filas com priorização
- Rastreamento detalhado de batches
- Análise comparativa entre lotes

---

## 🛠️ Tecnologias Utilizadas

### **Backend & Orquestração**
- **LangGraph**: Orquestração de workflows de agentes
- **FastAPI**: API REST para comunicação entre frontend e agentes
- **PostgreSQL**: Banco de dados relacional para persistência
- **SQLAlchemy**: ORM para gerenciamento de dados

### **Frontend & Visualização**
- **Streamlit**: Interface web interativa
- **Plotly**: Gráficos e visualizações interativas
- **Pandas**: Manipulação e análise de dados tabulares

### **IA & Machine Learning**
- **Groq API**: Modelos multimodais (Llama 4 Scout) para visão computacional
- **LangChain**: Framework para construção de agentes
- **OpenAI API**: Suporte para modelos GPT (opcional)
- **Anthropic Claude**: Suporte para modelos Claude (opcional)

### **Processamento de Documentos**
- **pytesseract**: OCR para extração de texto de imagens
- **pdf2image**: Conversão de PDFs para imagens
- **xmltodict**: Parsing de arquivos XML fiscais
- **pdfplumber**: Extração de dados de PDFs
- **Pillow**: Processamento de imagens

### **Fiscal & Compliance**
- **pycpfcnpj**: Validação de CNPJ e CPF brasileiros
- **cryptography**: Criptografia de certificados digitais
- **signxml**: Assinatura digital de manifestações SEFAZ
- **zeep**: Cliente SOAP para comunicação com webservices SEFAZ

---

## 📦 Instalação e Execução

### **Pré-requisitos**
- Python 3.11+
- PostgreSQL (ou usar o banco Replit)
- Tesseract OCR instalado no sistema
- Poppler (para conversão de PDFs)

### **1. Clone o Repositório**
```bash
git clone <url-do-repositorio>
cd nexafiscal
```

### **2. Instale as Dependências**
```bash
pip install -r requirements.txt
```

### **3. Configure Variáveis de Ambiente**
Crie um arquivo `.env` ou configure as secrets no Replit:

```bash
# Banco de Dados
DATABASE_URL=postgresql://user:password@host:port/database

# APIs de IA (escolha pelo menos uma)
GROQ_API_KEY=sua_chave_groq
OPENAI_API_KEY=sua_chave_openai (opcional)
ANTHROPIC_API_KEY=sua_chave_anthropic (opcional)

# Segurança SEFAZ
SEFAZ_CERT_MASTER_KEY=chave_aleatoria_32_caracteres_minimo

# Sessão
SESSION_SECRET=chave_aleatoria_para_sessoes
```

### **4. Inicialize o Banco de Dados**
```bash
# O banco será criado automaticamente na primeira execução
# Para PostgreSQL local, certifique-se de que o serviço está rodando
```

### **5. Execute a Aplicação**

**Frontend (Streamlit):**
```bash
streamlit run app.py --server.port 5000
```

**Backend (FastAPI):**
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Acesse:**
- Frontend: http://localhost:5000
- API Docs: http://localhost:8000/docs

---

## 🏗️ Arquitetura do Sistema

### **Fluxo de Processamento de Documentos**

```
┌─────────────────────────────────────────────────────────────────┐
│                         UPLOAD DE DOCUMENTO                      │
│                    (XML, PDF, Imagem, Lote)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   AGENTE DE CLASSIFICAÇÃO                        │
│           Identifica tipo: NFe, NFCe, SAT, CTe, NFSe            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTE DE EXTRAÇÃO                            │
│   • XML: Parse direto com xmltodict                             │
│   • PDF/Imagem: OCR + Visão Computacional (Groq)                │
│   • Extrai: Emitente, Destinatário, Itens, Impostos, CST        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTE DE VALIDAÇÃO                           │
│   • Valida CNPJ, CPF, Chaves de Acesso                          │
│   • Verifica consistência de valores                            │
│   • Detecta anomalias                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTE DE ANÁLISE                            │
│   • Gera insights fiscais                                       │
│   • Calcula totais e métricas                                   │
│   • Identifica padrões e tendências                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTÊNCIA NO BANCO                          │
│              PostgreSQL + Dashboard + Exportação                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Arquitetura de Agentes**

- **LangGraph Workflow**: Orquestração do fluxo entre agentes
- **Checkpoints SQLite**: Persistência de estado do workflow
- **Padrão Supervisor + Crítico**: Chat inteligente com validação de escopo
- **Modularidade**: Cada agente é independente e plugável

---

## 📁 Estrutura do Repositório

```
nexafiscal/
│
├── Projeto Final - Artefatos/     # 🎓 Artefatos de Entrega Acadêmica
│   ├── README.md                  # Instruções de entrega
│   └── .gitkeep                   # Mantém a pasta vazia no Git
│
├── agents/                        # 🤖 Agentes de IA
│   ├── classification_agent.py    # Classificação de documentos
│   ├── extraction_agent.py        # Extração de dados
│   ├── validation_agent.py        # Validação fiscal
│   ├── analysis_agent.py          # Análise e insights
│   └── integration_agent.py       # Integração SEFAZ
│
├── api/                           # 🌐 FastAPI Backend
│   ├── main.py                    # Aplicação principal
│   └── routes/                    # Rotas da API
│
├── pages/                         # 📄 Páginas Streamlit
│   ├── dashboard.py               # Dashboard de análises
│   ├── batch_processing.py        # Processamento em lote
│   ├── tax_config.py              # Configuração de impostos
│   ├── sefaz_integration.py       # Integração SEFAZ
│   ├── chat.py                    # Chat inteligente
│   └── table_upload.py            # Importação de tabelas
│
├── services/                      # 🛠️ Serviços de Negócio
│   ├── document_service.py        # Gerenciamento de documentos
│   ├── analysis_service.py        # Análises fiscais
│   ├── batch_service.py           # Gerenciamento de lotes
│   └── sefaz_service.py           # Comunicação SEFAZ
│
├── database/                      # 💾 Camada de Dados
│   ├── models.py                  # Modelos SQLAlchemy
│   ├── repository.py              # Repositório de dados
│   └── connection.py              # Conexão PostgreSQL
│
├── utils/                         # 🔧 Utilitários
│   ├── tax_config_loader.py       # Carregador de configuração de impostos
│   ├── table_processor.py         # Processamento de tabelas
│   └── validators.py              # Validadores fiscais
│
├── config/                        # ⚙️ Configurações
│   └── tax_config.json            # Configuração dinâmica de impostos
│
├── workflow_graph.py              # 🔄 LangGraph Workflow
├── app.py                         # 🎨 Interface Streamlit Principal
├── requirements.txt               # 📋 Dependências Python
├── LICENSE                        # 📜 Licença MIT
├── README.md                      # 📖 Este arquivo
└── replit.md                      # 🔧 Documentação técnica do projeto

```

---

## 🎨 Screenshots

> **Nota**: Screenshots disponíveis na apresentação final do projeto.

- Dashboard com análise de impostos e gráficos interativos
- Interface de upload e processamento em lote
- Configuração visual de impostos (preparado para IVA)
- Chat inteligente com agentes especializados
- Integração SEFAZ com gerenciamento de certificados

---

## 🧪 Como Adicionar Novos Impostos (Exemplo: IVA)

O NexaFiscal foi projetado para se adaptar a mudanças legais **sem necessidade de programação**:

### **Opção 1: Interface Visual** (Recomendado)
1. Acesse **⚙️ Configuração de Impostos** no menu lateral
2. Preencha o formulário:
   - **ID**: `iva`
   - **Nome**: `IVA`
   - **Nome Completo**: `Imposto sobre Valor Agregado`
   - **Cor**: Escolha uma cor no seletor
   - **Escopo**: Federal
   - **Campos XML**: `vIVA` (ou conforme legislação)
   - **Documentos**: NFe, NFCe, SAT
3. Clique em **Adicionar Imposto**

### **Opção 2: Edição Manual**
Edite `config/tax_config.json`:
```json
{
  "id": "iva",
  "name": "IVA",
  "full_name": "Imposto sobre Valor Agregado",
  "enabled": true,
  "xml_fields": ["vIVA"],
  "color": "#9C27B0",
  "scope": "federal",
  "applies_to": ["NFe", "NFCe", "SAT"]
}
```

**Resultado**: O sistema automaticamente extrai, analisa e visualiza o novo imposto em todos os dashboards!

---

## 📚 Documentação Adicional

- **replit.md**: Documentação técnica detalhada do projeto
- **API Docs**: Acesse `/docs` no servidor FastAPI (http://localhost:8000/docs)
- **Tax Config Guide**: Instruções detalhadas em `config/tax_config.json`

---

## 🤝 Contribuindo

Este é um projeto acadêmico desenvolvido para o curso I2A2. Sugestões e feedback são bem-vindos!

---

## 👥 Autor

Projeto desenvolvido como conclusão do curso **I2A2 - Agentes Autônomos com Redes Generativas**.

---

## 📞 Contato & Suporte

Para dúvidas sobre o projeto acadêmico, entre em contato através do repositório GitHub.

---

## 🙏 Agradecimentos

- **I2A2 Academy** pelo excelente curso sobre agentes autônomos
- Comunidade **LangChain/LangGraph** pelas ferramentas de orquestração
- Comunidade **Streamlit** pela plataforma de visualização
- **Groq** pelos modelos multimodais de alta performance

---

**NexaFiscal** - *Extração inteligente, análise instantânea* 🚀

Licenciado sob a [Licença MIT](LICENSE) | Projeto Acadêmico I2A2 - 2025
