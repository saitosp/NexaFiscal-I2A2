"""
Página de Upload de Tabelas (CSV/XLSX) - Importação em Lote de Notas Fiscais
"""

import streamlit as st
import os
from datetime import datetime
from utils.table_processor import (
    get_file_type,
    read_csv,
    read_excel,
    get_excel_sheets,
    convert_to_fiscal_documents,
    clean_numeric_column,
)
from agents.table_mapping_agent import TableMappingAgent
from services.document_service import DocumentService
from services.batch_service import BatchService

st.title("📊 Importação de Tabelas - NexaFiscal")
st.markdown("Importe múltiplas notas fiscais de uma vez usando arquivos CSV ou Excel")

# Inicializa session state
if "uploaded_table" not in st.session_state:
    st.session_state.uploaded_table = None
if "table_df" not in st.session_state:
    st.session_state.table_df = None
if "column_mapping" not in st.session_state:
    st.session_state.column_mapping = {}
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False


# Seção 1: Upload de arquivo
st.header("1️⃣ Selecionar Arquivo")

col1, col2 = st.columns([3, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Selecione um arquivo CSV ou Excel",
        type=["csv", "xlsx", "xls"],
        help="Arraste e solte ou clique para selecionar",
    )

with col2:
    if uploaded_file:
        file_type = get_file_type(uploaded_file.name)
        st.metric("Tipo", file_type.upper())

# Se arquivo foi enviado
if uploaded_file is not None:
    # Salva arquivo
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Lê arquivo
    try:
        file_type = get_file_type(uploaded_file.name)

        if file_type == "csv":
            df = read_csv(file_path)
            st.success(
                f"✅ Arquivo CSV carregado: {len(df)} linhas, {len(df.columns)} colunas"
            )

        elif file_type == "xlsx":
            # Verifica se tem múltiplas abas
            sheets = get_excel_sheets(file_path)

            if len(sheets) > 1:
                selected_sheet = st.selectbox(
                    "Selecione a aba do Excel:",
                    sheets,
                    help="O arquivo possui múltiplas abas",
                )
                df = read_excel(file_path, sheet_name=selected_sheet)
            else:
                df = read_excel(file_path)

            st.success(
                f"✅ Arquivo Excel carregado: {len(df)} linhas, {len(df.columns)} colunas"
            )

        else:
            st.error("❌ Formato de arquivo não suportado")
            st.stop()

        st.session_state.table_df = df
        st.session_state.uploaded_table = uploaded_file.name

    except Exception as e:
        st.error(f"❌ Erro ao ler arquivo: {str(e)}")
        st.stop()

    # Seção 2: Preview da Tabela
    st.header("2️⃣ Preview dos Dados")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Linhas", len(df))
    with col2:
        st.metric("Total de Colunas", len(df.columns))
    with col3:
        null_count = df.isnull().sum().sum()
        st.metric("Valores Vazios", null_count)
    with col4:
        st.metric("Tamanho", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    # Mostra preview
    st.subheader("Primeiras 10 linhas")
    st.dataframe(df.head(10), use_container_width=True)

    # Seção 3: Mapeamento de Colunas
    st.header("3️⃣ Mapeamento de Colunas")
    st.markdown(
        "Configure qual coluna da tabela corresponde a cada campo da nota fiscal"
    )

    # Botão para mapeamento automático
    col1, col2 = st.columns([2, 1])

    with col1:
        if st.button(
            "🤖 Detectar Colunas Automaticamente (IA)",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Analisando colunas com IA..."):
                try:
                    agent = TableMappingAgent()
                    sample_data = df.head(3).to_dict("records")
                    auto_mapping = agent.auto_map_columns(
                        columns=df.columns.tolist(), sample_data=sample_data
                    )
                    st.session_state.column_mapping = auto_mapping
                    st.success(
                        f"✅ {len(auto_mapping)} colunas mapeadas automaticamente!"
                    )
                except Exception as e:
                    st.error(f"Erro ao mapear automaticamente: {str(e)}")

    with col2:
        if st.button("🔄 Limpar Mapeamento", use_container_width=True):
            st.session_state.column_mapping = {}
            st.rerun()

    # Campos disponíveis para mapeamento
    fiscal_fields = {
        "emitente_nome": "Nome do Emitente/Fornecedor",
        "emitente_cnpj": "CNPJ/CPF do Emitente",
        "destinatario_nome": "Nome do Destinatário/Cliente",
        "destinatario_cnpj": "CNPJ/CPF do Destinatário",
        "numero_nota": "Número da Nota",
        "serie": "Série da Nota",
        "data_emissao": "Data de Emissão",
        "valor_total": "Valor Total ⭐",
        "valor_produtos": "Valor dos Produtos",
        "icms": "ICMS",
        "pis": "PIS",
        "cofins": "COFINS",
        "ipi": "IPI",
        "chave_acesso": "Chave de Acesso (44 dígitos)",
        "tipo_documento": "Tipo do Documento (NFe, NFCe, etc)",
    }

    # Interface de mapeamento manual
    st.subheader("Configuração Manual")

    columns_list = ["-- Não mapear --"] + df.columns.tolist()

    # Mostra em 2 colunas para economizar espaço
    col_left, col_right = st.columns(2)

    fields_left = list(fiscal_fields.items())[:8]
    fields_right = list(fiscal_fields.items())[8:]

    with col_left:
        for field_key, field_label in fields_left:
            current_value = st.session_state.column_mapping.get(
                field_key, "-- Não mapear --"
            )
            if current_value not in columns_list:
                current_value = "-- Não mapear --"

            index = (
                columns_list.index(current_value)
                if current_value in columns_list
                else 0
            )

            selected = st.selectbox(
                field_label, columns_list, index=index, key=f"map_{field_key}"
            )

            if selected != "-- Não mapear --":
                st.session_state.column_mapping[field_key] = selected
            elif field_key in st.session_state.column_mapping:
                del st.session_state.column_mapping[field_key]

    with col_right:
        for field_key, field_label in fields_right:
            current_value = st.session_state.column_mapping.get(
                field_key, "-- Não mapear --"
            )
            if current_value not in columns_list:
                current_value = "-- Não mapear --"

            index = (
                columns_list.index(current_value)
                if current_value in columns_list
                else 0
            )

            selected = st.selectbox(
                field_label, columns_list, index=index, key=f"map_{field_key}"
            )

            if selected != "-- Não mapear --":
                st.session_state.column_mapping[field_key] = selected
            elif field_key in st.session_state.column_mapping:
                del st.session_state.column_mapping[field_key]

    # Resumo do mapeamento
    if st.session_state.column_mapping:
        st.info(f"📋 {len(st.session_state.column_mapping)} campos mapeados")

        # Valida campos obrigatórios
        if "valor_total" not in st.session_state.column_mapping:
            st.warning("⚠️ Campo obrigatório 'Valor Total' não foi mapeado")

    # Seção 4: Processamento
    st.header("4️⃣ Processar Documentos")

    if not st.session_state.column_mapping:
        st.warning("⚠️ Configure o mapeamento de colunas antes de processar")
    else:
        # Mostra estatísticas previstas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Documentos a processar", len(df))

        with col2:
            if "valor_total" in st.session_state.column_mapping:
                col_name = st.session_state.column_mapping["valor_total"]
                try:
                    cleaned_values = clean_numeric_column(df, col_name)
                    total_value = cleaned_values.sum()
                    st.metric("Valor Total Estimado", f"R$ {total_value:,.2f}")
                except Exception:
                    st.metric("Valor Total", "N/A")
            else:
                st.metric("Valor Total", "N/A")

        with col3:
            mapped_count = len(st.session_state.column_mapping)
            st.metric("Campos Mapeados", f"{mapped_count}/15")

        # Campo para nome do lote
        st.markdown("---")
        default_batch_name = f"Importação {uploaded_file.name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        batch_name = st.text_input(
            "📝 Nome do Lote (opcional)",
            value=default_batch_name,
            help="Dê um nome para identificar este lote no dashboard. Deixe o padrão ou personalize.",
        )

        # Botão de processamento
        if st.button(
            "🚀 Processar Todos os Documentos", type="primary", use_container_width=True
        ):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Cria lote antes de processar
                status_text.text("Criando lote...")
                batch_id = BatchService.create_batch_metadata(
                    batch_name=batch_name, origin="csv_import"
                )

                # Converte tabela em documentos fiscais
                status_text.text("Convertendo linhas em documentos fiscais...")
                documents = convert_to_fiscal_documents(
                    df, st.session_state.column_mapping
                )

                # Processa e salva cada documento
                success_count = 0
                error_count = 0
                errors = []

                for i, doc in enumerate(documents):
                    progress = (i + 1) / len(documents)
                    progress_bar.progress(progress)
                    status_text.text(
                        f"Processando documento {i+1} de {len(documents)}..."
                    )

                    try:
                        # Prepara documento para salvar
                        processed_doc = {
                            "filename": f"{uploaded_file.name}_linha_{doc['row_number']}",
                            "file_path": file_path,
                            "document_type": doc["metadata"].get("tipo", "NFe"),
                            "issuer_name": doc["emitente"].get("nome", "N/A"),
                            "issuer_cnpj": doc["emitente"].get("cnpj", ""),
                            "recipient_name": doc["destinatario"].get("nome", "N/A"),
                            "recipient_cnpj": doc["destinatario"].get("cnpj", ""),
                            "total_value": doc["totais"].get("valor_total", 0.0),
                            "tax_total": (
                                doc["impostos"].get("icms", 0)
                                + doc["impostos"].get("pis", 0)
                                + doc["impostos"].get("cofins", 0)
                                + doc["impostos"].get("ipi", 0)
                            ),
                            "is_valid": True,
                            "processed_at": datetime.now(),
                            "extracted_data": doc,
                            "batch_id": batch_id,
                            "batch_name": batch_name,
                        }

                        # Salva no banco
                        doc_id = DocumentService.save_processed_document(processed_doc)
                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Linha {doc['row_number']}: {str(e)}")

                progress_bar.progress(1.0)
                status_text.text("Atualizando estatísticas do lote...")

                # Atualiza estatísticas do lote
                BatchService.update_batch_statistics(batch_id)

                status_text.empty()

                # Mostra resultados
                st.success("✅ Processamento concluído!")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("✅ Sucesso", success_count)
                with col2:
                    st.metric("❌ Erros", error_count)

                if error_count > 0 and errors:
                    with st.expander(f"Ver {error_count} erro(s)"):
                        for error in errors[:10]:  # Mostra primeiros 10 erros
                            st.text(error)

                st.session_state.processing_complete = True

            except Exception as e:
                import traceback

                full_error = traceback.format_exc()
                st.error(f"❌ Erro durante o processamento: {str(e)}")
                with st.expander("📋 Detalhes técnicos do erro"):
                    st.code(full_error)

        # Se processamento foi concluído
        if st.session_state.processing_complete:
            st.balloons()
            st.success("🎉 Importação concluída! Documentos salvos no sistema.")

            if st.button("📊 Ver Dashboard", use_container_width=True):
                st.switch_page("pages/dashboard.py")

else:
    # Instruções quando não há arquivo
    st.info("""
    ### 📝 Instruções:

    1. **Prepare sua tabela** (CSV ou Excel) com dados de notas fiscais
    2. **Faça upload** do arquivo
    3. **Configure o mapeamento** de colunas (manual ou automático com IA)
    4. **Processe** todos os documentos em lote

    **Colunas recomendadas:**
    - Emitente (nome e CNPJ/CPF)
    - Destinatário (nome e CNPJ/CPF)
    - Valor Total ⭐ (obrigatório)
    - Impostos (ICMS, PIS, COFINS, IPI)
    - Número da Nota
    - Data de Emissão
    - Chave de Acesso
    """)

    st.divider()

    st.subheader("💡 Dicas")
    st.markdown("""
    - Use a primeira linha como cabeçalho com nomes descritivos
    - Valores monetários podem ter símbolos (R$) ou separadores (1.000,00)
    - CNPJ/CPF podem ter ou não formatação (pontos, traços)
    - Para Excel, se tiver múltiplas abas, use a primeira aba com os dados
    """)
