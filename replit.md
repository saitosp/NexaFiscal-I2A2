# NexaFiscal - Sistema de Extração de Dados de Notas Fiscais Brasileiras

**Tagline:** Extração inteligente, análise instantânea

## 🎓 Projeto Acadêmico I2A2

Este projeto foi desenvolvido como **trabalho de conclusão do curso I2A2 - Agentes Autônomos com Redes Generativas**, demonstrando a aplicação prática de técnicas de agentes autônomos de IA em um contexto real de negócios fiscais no Brasil.

### Alinhamento com os Temas do Curso

O NexaFiscal implementa de forma abrangente os temas propostos pelo curso I2A2:

1. **Extração de Dados**: Sistema completo de OCR e NLP com modelos multimodais (Groq/Llama Vision) para extrair dados de documentos fiscais em múltiplos formatos (XML, PDF, imagens), incluindo emitente, destinatário, itens e impostos.

2. **Validação e Auditoria**: Validação automática de CNPJ, CPF, chaves de acesso NFe e verificação de consistência fiscal com detecção de anomalias.

3. **Classificação e Categorização**: Agente de classificação que identifica automaticamente o tipo de documento (NFe, NFCe, SAT, CTe, NFSe) e organiza por batches para rastreamento.

4. **Adaptação a Mudanças Legais**: Destaque principal do projeto - **sistema de configuração dinâmica de impostos** que permite adicionar novos tributos (ex: IVA) **sem modificar código**, apenas via interface visual ou arquivo JSON.

5. **Ferramentas Gerenciais**: Dashboard completo com Plotly, análises fiscais automatizadas, chat inteligente com padrão Supervisor + Crítico, e relatórios personalizados.

### Licenciamento

Este projeto está licenciado sob a **Licença MIT**, conforme requerido pelo curso I2A2, permitindo uso livre, modificação e distribuição.

## Overview
This project (NexaFiscal) is a modular AI agent system designed to process and extract structured data from various Brazilian fiscal documents (NFe, NFCe, SAT, CTe, NFSe). It aims to streamline fiscal data management, provide comprehensive analytical dashboards, and integrate with government portals for automated document retrieval and compliance. The system is built for scalability and extensibility, allowing for easy integration of new features and AI capabilities, with a business vision to provide robust, automated fiscal data processing for Brazilian enterprises.

## User Preferences
I prefer that the agent adheres to the established modular architecture, especially when introducing new agents or features. All new functionalities should be integrated seamlessly into the existing LangGraph workflow and Streamlit interface. Prioritize robust error handling and clear logging for all processing steps, especially for critical operations like certificate management and SEFAZ integration. Ensure all security configurations, particularly `SEFAZ_CERT_MASTER_KEY`, are mandatory and fail-fast if not properly set, providing clear instructions for remediation.

## System Architecture
The system uses a modular architecture built around LangGraph for orchestrating AI agents, a Streamlit-based web interface, and a FastAPI backend with PostgreSQL persistence.

### UI/UX Decisions
- **Streamlit Interface**: Interactive web interface for file uploads, data visualization, and configuration with multi-page navigation.
- **Data Visualization**: Utilizes Plotly for interactive charts and tables in the analytics dashboard.
- **Visual Feedback**: Provides progress indicators, status updates, and clear success/error messages.

### Technical Implementations
- **Agent-based System**: Core logic is encapsulated in modular agents (Classification, Extraction, Validation, Analysis, Integration).
- **LangGraph Workflow**: Orchestrates the sequence and interaction of agents for document processing.
- **FastAPI Backend**: Provides a RESTful API for document management, analysis, batch processing, and SEFAZ integration.
- **PostgreSQL Database**: Stores processed document data, agent logs, processing queues, and encrypted credentials using a repository pattern.
- **Asynchronous Processing**: Batch processing uses FastAPI BackgroundTasks for concurrent execution.
- **Security**: Digital certificates are encrypted at rest using AES-256-GCM with a mandatory `SEFAZ_CERT_MASTER_KEY`.

### Feature Specifications
- **Document Processing**: Supports XML, PDF, JPG, JPEG, PNG upload, detailed data extraction, and validation (CNPJ, CPF, NFe access keys).
- **Analytics Dashboard**: Provides comprehensive overview of processed documents, tax analysis, item analysis, financial summaries, and compliance checks.
- **Batch Processing**: Allows simultaneous upload and processing of multiple documents with prioritized queues and progress tracking, including table import (CSV/XLSX) with AI-powered intelligent column mapping and manual fallback.
- **SEFAZ Integration**: Manages digital certificates (A1 PKCS#12), communicates with SEFAZ portals for manifest actions, XML download, and pending document queries.
- **Data Export**: Supports JSON and CSV export.
- **History**: Maintains a searchable and filterable history of all processed documents.
- **Intelligent Chat Module**: Conversational interface using a **Supervisor + Critic** pattern with Groq API (Llama 4 Scout) for document queries, data analysis, and system assistance, featuring strict scope validation to keep responses project-related.
- **Batch Management System**: Provides comprehensive tracking and analytics for groups of documents processed together, allowing organized visualization and comparative analysis across different import sessions with a dedicated `batches` table and `batch_id` in the `documents` table.
- **Dynamic Tax Configuration System**: Configurable tax extraction and analysis through `config/tax_config.json`, enabling easy adaptation to tax law changes without code modifications. Supports CST (Código de Situação Tributária) extraction for all tax types from both XML and visual documents.

### System Design Choices
- **Modularity**: Agents are independent and pluggable into the LangGraph workflow.
- **Scalability**: Designed to handle increasing data volumes and new features through its modular and API-driven architecture.
- **Robustness**: Emphasizes comprehensive validation, secure handling of sensitive data, and clear error reporting.

## External Dependencies
- **Groq API**: For multimodal AI capabilities and AI-powered column mapping.
- **Streamlit**: For the interactive web user interface.
- **LangGraph**: For orchestrating AI agent workflows.
- **FastAPI**: For the RESTful API backend.
- **PostgreSQL**: Relational database for data persistence.
- **pytesseract**: OCR engine for text extraction from images.
- **pdf2image**: Converts PDF documents to images.
- **xmltodict**: Parses XML data.
- **pycpfcnpj**: Validates Brazilian CNPJ and CPF.
- **pandas**: For data manipulation and tabular display.
- **Pillow**: For image processing tasks.
- **Plotly**: For interactive data visualizations.
- **openpyxl**: For Excel (.xlsx) file support in table imports.

## How to Add New Taxes (e.g., IVA)

The system provides **two ways** to add new taxes, both requiring zero code modifications:

### Option 1: Visual Interface (Recommended for Most Users)

1. **Access the Tax Configuration Page**
   - In the Streamlit app, click on "⚙️ Configuração de Impostos" in the sidebar menu

2. **Fill the Form**
   - **ID do Imposto**: Unique identifier (lowercase, no spaces) - e.g., `iva`
   - **Nome**: Short display name - e.g., `IVA`
   - **Nome Completo**: Full legal name - e.g., `Imposto sobre Valor Agregado`
   - **Descrição**: Optional description
   - **Cor para Gráficos**: Choose a color using the color picker
   - **Escopo**: Select federal, estadual, or municipal
   - **Campos XML**: XML field names separated by commas - e.g., `vIVA`
   - **Aplica-se aos Documentos**: Select document types (NFe, NFCe, SAT, CTe, NFSe)
   - **Ativar imposto imediatamente**: Check to enable right away

3. **Click "➕ Adicionar Imposto"**

That's it! The tax is immediately available system-wide.

### Option 2: Manual JSON Editing (For Advanced Users)

Edit the `config/tax_config.json` file directly:

```json
{
  "id": "iva",
  "name": "IVA",
  "full_name": "Imposto sobre Valor Agregado",
  "description": "Novo imposto brasileiro previsto para 2026",
  "enabled": true,
  "xml_fields": ["vIVA"],
  "color": "#9C27B0",
  "scope": "federal",
  "applies_to": ["NFe", "NFCe", "SAT"]
}
```

Then restart the application.

### What Happens Automatically

Once a tax is added (via either method), the system **automatically**:

1. **Extracts from XML documents** - Reads the `xml_fields` path and extracts values
2. **Requests in AI prompts** - Visual document extraction asks the AI to identify the new tax
3. **Displays in analytics** - Dashboard generates a new chart bar with the configured color
4. **Includes in totals** - Tax analysis aggregates the new tax across all documents

### Configuration Fields Explained

- **id**: Unique identifier (lowercase, used in code and database)
- **name**: Short display name (e.g., "IVA")
- **full_name**: Complete legal name (e.g., "Imposto sobre Valor Agregado")
- **description**: Optional explanation of the tax
- **enabled**: Set to `true` to activate, `false` to temporarily disable
- **xml_fields**: Array of XML paths where the tax value is stored (supports nested paths with dots)
- **color**: Hex color code for dashboard charts
- **scope**: Tax jurisdiction level (federal, estadual, municipal)
- **applies_to**: Document types where this tax is relevant (NFe, NFCe, SAT, CTe, NFSe)

### Example: Future IVA Implementation

When Brazil implements IVA (expected 2026+):

**Via Visual Interface:**
1. Go to "⚙️ Configuração de Impostos"
2. Fill the form with IVA details
3. Click "Adicionar Imposto"

**Via JSON File:**
1. Open `config/tax_config.json`
2. Add IVA entry to the `taxes` array
3. Restart the application

**No code changes required!** The system immediately starts extracting, analyzing, and visualizing IVA data.

### Tax Management Features

The visual interface also allows you to:
- **Activate/Deactivate** taxes without deleting them
- **Edit** existing tax properties
- **Remove** taxes that are no longer needed
- **View** all configured taxes in a table

All changes are automatically backed up to `config/tax_config.json.backup_YYYYMMDD_HHMMSS` files.

### CST Extraction

The system extracts CST (Código de Situação Tributária) for each tax type:

- **ICMS**: Supports both CST (Regime Normal) and CSOSN (Simples Nacional)
- **IPI, PIS, COFINS**: Extracts CST from both XML and visual documents
- **Item-level tracking**: CST is stored per item in `extracted_data.itens[].cst_icms`, `cst_ipi`, etc.

This allows detailed tax compliance analysis and proper classification of tax scenarios.