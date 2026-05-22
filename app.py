"""
Sistema de Extração de Dados de Notas Fiscais Brasileiras
Plataforma web interativa com Streamlit e LangGraph
"""

import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from workflow_graph import process_invoice
from services.document_service import DocumentService
from pages.dashboard import render_dashboard
from pages.batch_processing import render_batch_processing
from pages.sefaz_integration import render_sefaz_integration
from pages.chat import main as render_chat

# Configuração da página
st.set_page_config(
    page_title="NexaFiscal - Extração inteligente, análise instantânea",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa session state
if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "db_documents_cache" not in st.session_state:
    st.session_state.db_documents_cache = None

if "cache_timestamp" not in st.session_state:
    st.session_state.cache_timestamp = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Upload"


def save_uploaded_file(uploaded_file):
    """
    Salva arquivo enviado pelo usuário
    """
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def display_agent_status(result):
    """
    Exibe status de cada agente no processamento
    """
    st.subheader("🤖 Status dos Agentes")

    cols = st.columns(4)

    # Agente de Processamento
    with cols[0]:
        if result.get("processed_data", {}).get("success"):
            st.success("✅ Processamento")
        else:
            st.error("❌ Processamento")
        st.caption("Leitura do arquivo")

    # Agente de Classificação
    with cols[1]:
        if result.get("classification"):
            st.success("✅ Classificação")
            doc_type = result["classification"].get("document_type", "N/A")
            st.caption(f"Tipo: {doc_type}")
        else:
            st.warning("⏳ Classificação")

    # Agente de Extração
    with cols[2]:
        if result.get("extracted_data"):
            st.success("✅ Extração")
            num_itens = len(result["extracted_data"].get("itens", []))
            st.caption(f"{num_itens} itens")
        else:
            st.warning("⏳ Extração")

    # Agente de Validação
    with cols[3]:
        validation = result.get("validation", {})
        if validation:
            if validation.get("is_valid"):
                st.success("✅ Validação")
            else:
                st.warning("⚠️ Validação")
            num_errors = len(validation.get("errors", []))
            num_warnings = len(validation.get("warnings", []))
            st.caption(f"{num_errors} erros, {num_warnings} avisos")
        else:
            st.warning("⏳ Validação")


def display_extracted_data(extracted_data):
    """
    Exibe dados extraídos em formato estruturado
    """
    st.subheader("📊 Dados Extraídos")

    # Abas para diferentes seções
    tabs = st.tabs(
        ["Emitente", "Destinatário", "Itens", "Totais", "Impostos", "Info Adicional"]
    )

    # Emitente
    with tabs[0]:
        emitente = extracted_data.get("emitente", {})
        if emitente:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**CNPJ:**", emitente.get("cnpj", "N/A"))
                st.write("**Razão Social:**", emitente.get("razao_social", "N/A"))
                st.write("**Nome Fantasia:**", emitente.get("nome_fantasia", "N/A"))
            with col2:
                st.write("**IE:**", emitente.get("ie", "N/A"))
                st.write("**Endereço:**", emitente.get("endereco", "N/A"))
        else:
            st.info("Dados do emitente não encontrados")

    # Destinatário
    with tabs[1]:
        destinatario = extracted_data.get("destinatario", {})
        if destinatario:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**CNPJ:**", destinatario.get("cnpj", "N/A"))
                st.write("**CPF:**", destinatario.get("cpf", "N/A"))
                st.write("**Nome:**", destinatario.get("nome", "N/A"))
            with col2:
                st.write("**IE:**", destinatario.get("ie", "N/A"))
                st.write("**Endereço:**", destinatario.get("endereco", "N/A"))
        else:
            st.info("Dados do destinatário não encontrados")

    # Itens
    with tabs[2]:
        itens = extracted_data.get("itens", [])
        if itens:
            df_itens = pd.DataFrame(itens)
            st.dataframe(df_itens, use_container_width=True)
        else:
            st.info("Nenhum item encontrado")

    # Totais
    with tabs[3]:
        totais = extracted_data.get("totais", {})
        if totais:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Valor Produtos", f"R$ {totais.get('valor_produtos', 0):,.2f}"
                )
                st.metric("Valor Frete", f"R$ {totais.get('valor_frete', 0):,.2f}")
                st.metric("Valor Seguro", f"R$ {totais.get('valor_seguro', 0):,.2f}")
            with col2:
                st.metric(
                    "Valor Desconto", f"R$ {totais.get('valor_desconto', 0):,.2f}"
                )
                st.metric(
                    "Valor Total", f"R$ {totais.get('valor_total', 0):,.2f}", delta=None
                )
        else:
            st.info("Totais não encontrados")

    # Impostos
    with tabs[4]:
        impostos = extracted_data.get("impostos", {})
        if impostos:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("ICMS", f"R$ {impostos.get('icms', 0):,.2f}")
                st.metric("IPI", f"R$ {impostos.get('ipi', 0):,.2f}")
            with col2:
                st.metric("PIS", f"R$ {impostos.get('pis', 0):,.2f}")
                st.metric("COFINS", f"R$ {impostos.get('cofins', 0):,.2f}")
        else:
            st.info("Impostos não encontrados")

    # Informações Adicionais
    with tabs[5]:
        info = extracted_data.get("informacoes_adicionais", {})
        if info:
            st.write("**Número:**", info.get("numero", "N/A"))
            st.write("**Série:**", info.get("serie", "N/A"))
            st.write("**Data Emissão:**", info.get("data_emissao", "N/A"))
            st.write("**Chave de Acesso:**", info.get("chave_acesso", "N/A"))
        else:
            st.info("Informações adicionais não encontradas")


def display_validation_results(validation):
    """
    Exibe resultados da validação
    """
    st.subheader("✔️ Validação")

    if validation.get("is_valid"):
        st.success("✅ Documento validado com sucesso!")
    else:
        st.error("❌ Documento contém erros de validação")

    # Erros
    errors = validation.get("errors", [])
    if errors:
        st.error("**Erros encontrados:**")
        for error in errors:
            st.write(f"- {error}")

    # Avisos
    warnings = validation.get("warnings", [])
    if warnings:
        st.warning("**Avisos:**")
        for warning in warnings:
            st.write(f"- {warning}")

    # Validações específicas
    validations = validation.get("validations", {})
    if validations:
        with st.expander("Detalhes das validações"):
            for key, value in validations.items():
                st.write(f"**{key}:** {value}")


def export_to_json(data, filename):
    """
    Exporta dados para JSON
    """
    export_dir = "data/exports"
    os.makedirs(export_dir, exist_ok=True)

    export_path = os.path.join(export_dir, f"{filename}.json")

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return export_path


def export_to_csv(data, filename):
    """
    Exporta itens para CSV
    """
    export_dir = "data/exports"
    os.makedirs(export_dir, exist_ok=True)

    itens = data.get("extracted_data", {}).get("itens", [])

    if itens:
        df = pd.DataFrame(itens)
        export_path = os.path.join(export_dir, f"{filename}.csv")
        df.to_csv(export_path, index=False, encoding="utf-8-sig")
        return export_path

    return None


# Sidebar - Navegação e Informações
with st.sidebar:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(
            "attached_assets/generated_images/NexaFiscal_AI_logo_design_2a3bf643.png",
            use_container_width=True,
        )

    st.markdown(
        "<h3 style='text-align: center;'>NexaFiscal</h3>", unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; font-size: 0.8em; color: #888;'>Extração inteligente, análise instantânea</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.title("🧭 Navegação")

    page = st.radio(
        "Escolha uma página:",
        [
            "📤 Upload e Processamento",
            "💬 Chat com Agentes",
            "📊 Importar Tabela",
            "📦 Processamento em Lote",
            "📈 Dashboard de Análise",
            "⚙️ Configuração de Impostos",
            "🔐 Integração SEFAZ",
            "📚 Histórico",
        ],
        key="page_navigation",
        label_visibility="collapsed",
    )

    st.divider()

    st.header("ℹ️ Sobre o Sistema")
    st.write("""
    Este sistema utiliza:
    - **LangGraph** para orquestração modular
    - **Groq API** com modelos Llama 4
    - **OCR** com Tesseract
    - **PostgreSQL** para persistência
    - **FastAPI** para integração
    """)

    st.divider()

    st.header("🤖 Agentes Disponíveis")
    st.write("""
    1. **Classificação** - Identifica tipo de nota
    2. **Extração** - Extrai dados estruturados
    3. **Validação** - Valida consistência
    4. **Análise** - Gera insights fiscais
    """)

    st.divider()

    st.header("📊 Estatísticas")
    try:
        stats = DocumentService.get_statistics()
        st.metric("Documentos Processados", stats.get("total", 0))
        if stats.get("valid", 0) > 0:
            st.metric("✅ Válidos", stats.get("valid", 0))
        if stats.get("invalid", 0) > 0:
            st.metric("⚠️ Com Erros", stats.get("invalid", 0))
    except Exception:
        st.metric("Documentos Processados", 0)

# Interface principal
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(
        "attached_assets/generated_images/NexaFiscal_AI_logo_design_2a3bf643.png",
        use_container_width=True,
    )

st.markdown(
    "<h1 style='text-align: center;'>📄 NexaFiscal</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align: center; font-size: 1.2em;'><strong>Extração inteligente, análise instantânea</strong></p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #888;'>Sistema modular com LangGraph e IA para processamento automatizado de NFe, NFCe, SAT e outros documentos fiscais brasileiros</p>",
    unsafe_allow_html=True,
)

st.divider()

# Roteamento de páginas
if page == "📈 Dashboard de Análise":
    render_dashboard()

elif page == "📊 Importar Tabela":
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "table_upload", "pages/table_upload.py"
    )
    if spec and spec.loader:
        table_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(table_module)

elif page == "📦 Processamento em Lote":
    render_batch_processing()

elif page == "⚙️ Configuração de Impostos":
    from pages.tax_config import render_tax_config

    render_tax_config()

elif page == "🔐 Integração SEFAZ":
    render_sefaz_integration()

elif page == "📤 Upload e Processamento":
    # Página de Upload
    st.header("📤 Upload de Nota Fiscal")

    uploaded_file = st.file_uploader(
        "Selecione um arquivo (XML, PDF ou imagem)",
        type=["xml", "pdf", "jpg", "jpeg", "png"],
        help="Arraste e solte ou clique para selecionar",
    )

    if uploaded_file:
        # Preview do arquivo para feedback visual imediato
        with st.expander("👁️ Pré-visualização do Arquivo", expanded=True):
            try:
                # Preview de Imagem
                if uploaded_file.type.startswith("image"):
                    st.image(
                        uploaded_file,
                        caption=f"Pré-visualização: {uploaded_file.name}",
                        use_container_width=True,
                    )
                    uploaded_file.seek(0)

                # Preview de XML (primeiros 1000 caracteres)
                elif (
                    uploaded_file.type == "text/xml"
                    or uploaded_file.name.lower().endswith(".xml")
                ):
                    uploaded_file.seek(0)
                    content = uploaded_file.read(1000).decode("utf-8", errors="ignore")
                    uploaded_file.seek(0)
                    st.code(
                        content + ("..." if len(content) == 1000 else ""),
                        language="xml",
                    )

                # Info para PDF
                elif uploaded_file.type == "application/pdf":
                    st.info(
                        "📄 Pré-visualização de PDF não disponível (o conteúdo será extraído durante o processamento)"
                    )

                else:
                    st.info(f"📄 Arquivo carregado: {uploaded_file.name}")
            except Exception as e:
                st.warning(f"Não foi possível gerar pré-visualização: {str(e)}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.info(f"📁 Arquivo selecionado: **{uploaded_file.name}**")

        with col2:
            process_button = st.button(
                "🚀 Processar", use_container_width=True, type="primary"
            )

        if process_button:
            with st.spinner("🔄 Processando documento através dos agentes..."):
                try:
                    file_path = save_uploaded_file(uploaded_file)
                    result = process_invoice(file_path, uploaded_file.name)
                    result["filename"] = uploaded_file.name
                    result["file_path"] = file_path

                    if result.get("errors"):
                        st.error("❌ Erros durante o processamento:")
                        for error in result["errors"]:
                            st.error(f"• {error}")

                        if any("GROQ_API_KEY" in str(e) for e in result["errors"]):
                            st.warning("""
                            ⚙️ **Configuração necessária**:

                            O sistema precisa de uma chave de API do Groq para funcionar.

                            1. Obtenha uma chave gratuita em: https://console.groq.com
                            2. Configure a variável de ambiente `GROQ_API_KEY` com sua chave
                            3. Reinicie a aplicação
                            """)
                    else:
                        st.success("✅ Processamento concluído!")

                    try:
                        doc_id = DocumentService.save_processed_document(result)
                        st.info(f"💾 Documento salvo no banco (ID: {doc_id})")
                    except Exception as db_error:
                        st.warning(f"⚠️ Erro ao salvar no banco: {str(db_error)}")

                    st.session_state.current_result = result

                except Exception as e:
                    st.error(f"❌ Erro no processamento: {str(e)}")

    if st.session_state.current_result:
        st.divider()

        result = st.session_state.current_result

        display_agent_status(result)

        st.divider()

        if result.get("extracted_data"):
            display_extracted_data(result["extracted_data"])

        st.divider()

        if result.get("validation"):
            display_validation_results(result["validation"])

        st.divider()

        st.subheader("💾 Exportar Dados")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Exportar JSON Completo", use_container_width=True):
                try:
                    filename = f"nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    export_path = export_to_json(result, filename)

                    with open(export_path, "r", encoding="utf-8") as f:
                        st.download_button(
                            "⬇️ Download JSON",
                            f.read(),
                            file_name=f"{filename}.json",
                            mime="application/json",
                        )
                except Exception as e:
                    st.error(f"Erro ao exportar: {str(e)}")

        with col2:
            if st.button("📊 Exportar Itens CSV", use_container_width=True):
                try:
                    filename = f"itens_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    export_path = export_to_csv(result, filename)

                    if export_path:
                        with open(export_path, "r", encoding="utf-8-sig") as f:
                            st.download_button(
                                "⬇️ Download CSV",
                                f.read(),
                                file_name=f"{filename}.csv",
                                mime="text/csv",
                            )
                    else:
                        st.warning("Nenhum item para exportar")
                except Exception as e:
                    st.error(f"Erro ao exportar: {str(e)}")

        with col3:
            if st.button("🔄 Processar Novo Documento", use_container_width=True):
                st.session_state.current_result = None
                st.rerun()

elif page == "💬 Chat com Agentes":
    # Página de Chat
    render_chat()

elif page == "📚 Histórico":
    # Página de Histórico de Documentos (do banco de dados)
    st.divider()
    st.header("📚 Histórico de Documentos Processados")

    # Área de limpeza do histórico (perigoso - escondida em expander)
    with st.expander("⚠️ Zona de Perigo - Limpar Todo o Histórico"):
        st.warning("""
        **ATENÇÃO: Operação Irreversível!**

        Esta ação irá **deletar permanentemente** todos os documentos processados do banco de dados.

        - ❌ Não há como desfazer esta ação
        - ❌ Todos os dados extraídos serão perdidos
        - ❌ Logs de processamento serão removidos
        """)

        col1, col2 = st.columns([3, 1])

        with col1:
            confirm_delete = st.checkbox(
                "Sim, entendo que esta ação é irreversível e quero deletar tudo"
            )

        with col2:
            if st.button(
                "🗑️ Limpar Histórico",
                type="primary",
                disabled=not confirm_delete,
                use_container_width=True,
            ):
                with st.spinner("Deletando todos os documentos..."):
                    try:
                        import requests

                        response = requests.delete(
                            "http://localhost:8000/api/documents"
                        )

                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            st.session_state.current_result = None
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao deletar documentos: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Erro na comunicação com a API: {str(e)}")

    st.divider()

    try:
        col1, col2 = st.columns(2)

        with col1:
            search_term = st.text_input("🔍 Buscar por nome de arquivo", "")

        with col2:
            stats = DocumentService.get_statistics()
            doc_types = list(stats.get("by_type", {}).keys())
            selected_type = st.selectbox("Filtrar por tipo", ["Todos"] + doc_types)

        if search_term or selected_type != "Todos":
            doc_type_filter = None if selected_type == "Todos" else selected_type
            db_docs = DocumentService.search_documents(search_term, doc_type_filter)
        else:
            db_docs = DocumentService.get_all_documents(limit=50)

        if db_docs:
            for i, db_doc in enumerate(db_docs):
                status_icon = (
                    "✅"
                    if bool(db_doc.is_valid)
                    else ("⚠️" if bool(db_doc.has_errors) else "📄")
                )
                doc_type_display = (
                    db_doc.document_type if db_doc.document_type is not None else "N/A"
                )
                with st.expander(
                    f"{status_icon} {db_doc.filename} - "
                    f"{doc_type_display} - "
                    f"{db_doc.created_at.strftime('%Y-%m-%d %H:%M')}"
                ):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**ID:**", db_doc.id)
                        tipo_display = (
                            db_doc.document_type
                            if db_doc.document_type is not None
                            else "N/A"
                        )
                        st.write("**Tipo:**", tipo_display)
                        st.write("**Status:**", db_doc.processing_status)

                    with col2:
                        emitente_display = (
                            db_doc.issuer_name
                            if db_doc.issuer_name is not None
                            else "N/A"
                        )
                        st.write("**Emitente:**", emitente_display)
                        if db_doc.total_value is not None:
                            st.write("**Valor Total:**", f"R$ {db_doc.total_value:.2f}")
                        data_emissao_display = (
                            db_doc.issue_date.strftime("%d/%m/%Y")
                            if db_doc.issue_date is not None
                            else "N/A"
                        )
                        st.write("**Data Emissão:**", data_emissao_display)

                    with col3:
                        st.write(
                            "**Válido:**",
                            "✅ Sim" if bool(db_doc.is_valid) else "❌ Não",
                        )
                        st.write(
                            "**Tem Erros:**",
                            "⚠️ Sim" if bool(db_doc.has_errors) else "✅ Não",
                        )
                        st.write(
                            "**Processado em:**",
                            db_doc.created_at.strftime("%d/%m/%Y %H:%M"),
                        )

                    if st.button("Ver Detalhes Completos", key=f"view_db_{db_doc.id}"):
                        result_format = DocumentService.document_to_result_format(
                            db_doc
                        )
                        st.session_state.current_result = result_format
                        st.rerun()
        else:
            st.info(
                "📭 Nenhum documento encontrado no banco de dados. Faça upload de uma nota fiscal para começar!"
            )

        # Exibir detalhes completos se um documento foi selecionado
        if st.session_state.current_result:
            st.divider()
            st.header("📋 Detalhes Completos do Documento")

            result = st.session_state.current_result

            display_agent_status(result)

            st.divider()

            if result.get("extracted_data"):
                display_extracted_data(result["extracted_data"])

            st.divider()

            if result.get("validation"):
                display_validation_results(result["validation"])

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔙 Voltar ao Histórico", use_container_width=True):
                    st.session_state.current_result = None
                    st.rerun()

            with col2:
                if result.get("extracted_data"):
                    filename = f"nfe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    export_path = export_to_json(result, filename)

                    with open(export_path, "r", encoding="utf-8") as f:
                        st.download_button(
                            "📄 Download JSON",
                            f.read(),
                            file_name=f"{filename}.json",
                            mime="application/json",
                            use_container_width=True,
                        )

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {str(e)}")
        st.info(
            "📭 Banco de dados vazio ou inacessível. Faça upload de uma nota fiscal para começar!"
        )
