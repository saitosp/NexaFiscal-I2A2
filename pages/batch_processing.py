"""
Página de Processamento em Lote
Upload e processamento de múltiplos documentos fiscais
"""

import streamlit as st
import requests
import time
from datetime import datetime
import pandas as pd


API_URL = "http://localhost:8000"


def render_batch_processing():
    """
    Renderiza a página de processamento em lote
    """
    st.header("📦 Processamento em Lote - NexaFiscal")
    st.write("Faça upload de múltiplos documentos fiscais para processamento simultâneo")
    
    st.divider()
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["📤 Novo Lote", "📊 Lotes Ativos", "📚 Histórico de Lotes"])
    
    # === TAB 1: NOVO LOTE ===
    with tab1:
        st.subheader("Upload em Lote")
        
        uploaded_files = st.file_uploader(
            "Selecione múltiplos arquivos (XML, PDF ou imagens)",
            type=['xml', 'pdf', 'jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="Arraste e solte ou clique para selecionar vários arquivos"
        )
        
        if uploaded_files:
            st.info(f"📁 **{len(uploaded_files)} arquivos selecionados**")
            
            # Mostra preview dos arquivos
            with st.expander(f"Ver lista de {len(uploaded_files)} arquivos"):
                for i, file in enumerate(uploaded_files, 1):
                    file_size_kb = len(file.getvalue()) / 1024
                    st.write(f"{i}. **{file.name}** ({file_size_kb:.1f} KB)")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("🚀 Enviar e Processar", use_container_width=True, type="primary"):
                    with st.spinner("Enviando arquivos..."):
                        try:
                            # Prepara arquivos para upload
                            files = []
                            for uploaded_file in uploaded_files:
                                uploaded_file.seek(0)
                                files.append(
                                    ('files', (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))
                                )
                            
                            # Upload em lote
                            response = requests.post(
                                f"{API_URL}/api/batch/upload",
                                files=files
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                batch_id = data['batch_id']
                                
                                st.success(f"✅ {data['total_files']} arquivos enviados com sucesso!")
                                st.session_state.current_batch_id = batch_id
                                
                                # Inicia processamento
                                process_response = requests.post(
                                    f"{API_URL}/api/batch/{batch_id}/process"
                                )
                                
                                if process_response.status_code == 200:
                                    st.info("🔄 Processamento iniciado em background")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning("Arquivos enviados, mas processamento não iniciado automaticamente")
                            else:
                                st.error(f"Erro ao enviar arquivos: {response.text}")
                        
                        except Exception as e:
                            st.error(f"Erro: {str(e)}")
    
    # === TAB 2: LOTES ATIVOS ===
    with tab2:
        st.subheader("Lotes em Processamento")
        
        if 'current_batch_id' in st.session_state:
            batch_id = st.session_state.current_batch_id
            
            # Botão de atualizar
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("🔄 Atualizar Status", use_container_width=True):
                    st.rerun()
            
            with col2:
                auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
            
            try:
                response = requests.get(f"{API_URL}/api/batch/{batch_id}/status")
                
                if response.status_code == 200:
                    status = response.json()
                    
                    # Métricas
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Total", status['total'])
                    with col2:
                        st.metric("⏳ Pendente", status['pending'])
                    with col3:
                        st.metric("🔄 Processando", status['processing'])
                    with col4:
                        st.metric("✅ Concluído", status['completed'])
                    with col5:
                        st.metric("❌ Falhas", status['failed'])
                    
                    # Barra de progresso
                    if status['total'] > 0:
                        progress = (status['completed'] + status['failed']) / status['total']
                        st.progress(progress, text=f"Progresso: {progress * 100:.0f}%")
                    
                    st.divider()
                    
                    # Tabela de documentos
                    if status['items']:
                        df_data = []
                        
                        for item in status['items']:
                            status_icon = {
                                'pending': '⏳',
                                'processing': '🔄',
                                'completed': '✅',
                                'failed': '❌'
                            }.get(item['status'], '❓')
                            
                            df_data.append({
                                'Status': f"{status_icon} {item['status'].title()}",
                                'Arquivo': item['filename'],
                                'Tentativas': item['attempts'],
                                'Documento ID': item['document_id'] or '-',
                                'Erro': item['error_message'][:50] + '...' if item['error_message'] and len(item['error_message']) > 50 else (item['error_message'] or '-')
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Botão de retry para falhas
                        if status['failed'] > 0:
                            if st.button(f"🔁 Reprocessar {status['failed']} Documentos com Falha"):
                                retry_response = requests.post(f"{API_URL}/api/batch/{batch_id}/retry")
                                if retry_response.status_code == 200:
                                    st.success(f"✅ {retry_response.json()['retried_count']} documentos resetados")
                                    time.sleep(1)
                                    st.rerun()
                    
                    # Auto-refresh
                    if auto_refresh:
                        time.sleep(5)
                        st.rerun()
                
                else:
                    st.error("Erro ao carregar status do lote")
            
            except Exception as e:
                st.error(f"Erro: {str(e)}")
        
        else:
            st.info("📭 Nenhum lote ativo. Faça upload de documentos na aba 'Novo Lote'")
    
    # === TAB 3: HISTÓRICO ===
    with tab3:
        st.subheader("Histórico de Todos os Lotes")
        
        try:
            response = requests.get(f"{API_URL}/api/batches", params={'limit': 50})
            
            if response.status_code == 200:
                batches = response.json()
                
                if batches:
                    for batch in batches:
                        with st.expander(
                            f"Lote {batch['batch_id'][:8]}... - "
                            f"{batch['total']} docs - "
                            f"✅ {batch['completed']} / ❌ {batch['failed']} - "
                            f"{batch.get('created_at', 'N/A')[:19] if batch.get('created_at') else 'N/A'}"
                        ):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Lote ID:** `{batch['batch_id']}`")
                                st.write(f"**Total:** {batch['total']}")
                                st.write(f"**Data:** {batch.get('created_at', 'N/A')[:19] if batch.get('created_at') else 'N/A'}")
                            
                            with col2:
                                st.write(f"**⏳ Pendente:** {batch['pending']}")
                                st.write(f"**🔄 Processando:** {batch['processing']}")
                                st.write(f"**✅ Concluído:** {batch['completed']}")
                                st.write(f"**❌ Falhas:** {batch['failed']}")
                            
                            if st.button(f"Ver Detalhes", key=f"view_{batch['batch_id']}"):
                                st.session_state.current_batch_id = batch['batch_id']
                                st.rerun()
                else:
                    st.info("📭 Nenhum lote processado ainda")
            else:
                st.error("Erro ao carregar histórico de lotes")
        
        except Exception as e:
            st.error(f"Erro: {str(e)}")
