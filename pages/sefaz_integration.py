"""
Página de Integração com SEFAZ
Configuração de certificado digital e sincronização de documentos
"""

import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import os


API_URL = "http://localhost:8000"


def render_sefaz_integration():
    """
    Renderiza a página de integração com SEFAZ
    """
    st.header("🔐 Integração com SEFAZ - NexaFiscal")
    st.write("Configure certificado digital e sincronize documentos fiscais dos portais oficiais")
    
    # Verificar se a chave de criptografia está configurada
    if not os.getenv('SEFAZ_CERT_MASTER_KEY'):
        st.error("""
        ⚠️ **Chave de Criptografia Não Configurada**
        
        Para usar a integração SEFAZ, é necessário configurar a variável de ambiente 
        `SEFAZ_CERT_MASTER_KEY` nos Secrets do Replit.
        
        **Passos:**
        1. Vá em Tools → Secrets no Replit
        2. Adicione uma nova secret: `SEFAZ_CERT_MASTER_KEY`
        3. Use uma chave forte (mínimo 32 caracteres aleatórios)
        4. Reinicie a aplicação
        
        Esta chave é usada para criptografar os certificados digitais no banco de dados.
        """)
        st.stop()
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📜 Certificados", "🔄 Sincronização", "ℹ️ Informações"])
    
    # === TAB 1: CERTIFICADOS ===
    with tab1:
        st.subheader("Gerenciamento de Certificados Digitais")
        
        # Novo certificado
        with st.expander("➕ Adicionar Novo Certificado", expanded=False):
            st.write("**Upload de Certificado Digital A1 (.pfx ou .p12)**")
            
            cert_name = st.text_input(
                "Nome Identificador",
                placeholder="Ex: Certificado Empresa CNPJ 12345678000190",
                help="Nome para identificar este certificado"
            )
            
            cert_file = st.file_uploader(
                "Arquivo de Certificado (.pfx ou .p12)",
                type=['pfx', 'p12'],
                help="Arquivo do certificado digital A1"
            )
            
            cert_password = st.text_input(
                "Senha do Certificado",
                type="password",
                help="Senha utilizada para proteger o certificado"
            )
            
            cert_environment = st.selectbox(
                "Ambiente",
                options=["homologation", "production"],
                format_func=lambda x: "Homologação" if x == "homologation" else "Produção"
            )
            
            if st.button("📤 Enviar Certificado", use_container_width=True, type="primary"):
                if not cert_name:
                    st.error("Por favor, informe um nome identificador")
                elif not cert_file:
                    st.error("Por favor, selecione um arquivo de certificado")
                elif not cert_password:
                    st.error("Por favor, informe a senha do certificado")
                else:
                    with st.spinner("Processando certificado..."):
                        try:
                            cert_file.seek(0)
                            
                            files = {
                                'file': (cert_file.name, cert_file.getvalue(), 'application/x-pkcs12')
                            }
                            
                            params = {
                                'password': cert_password,
                                'name': cert_name,
                                'environment': cert_environment
                            }
                            
                            response = requests.post(
                                f"{API_URL}/api/sefaz/certificates",
                                files=files,
                                params=params
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"✅ Certificado adicionado com sucesso! (ID: {data['credential_id']})")
                                
                                st.info(f"""
                                **Informações do Certificado:**
                                - **Nome:** {data['name']}
                                - **Subject:** {data['subject']}
                                - **Válido Até:** {data['valid_until'][:10]}
                                - **Ambiente:** {cert_environment.title()}
                                """)
                                
                                st.rerun()
                            else:
                                error_detail = response.json().get('detail', 'Erro desconhecido')
                                st.error(f"❌ Erro ao processar certificado: {error_detail}")
                        
                        except Exception as e:
                            st.error(f"❌ Erro: {str(e)}")
        
        st.divider()
        
        # Lista de certificados
        st.subheader("Certificados Cadastrados")
        
        try:
            response = requests.get(f"{API_URL}/api/sefaz/certificates")
            
            if response.status_code == 200:
                certificates = response.json()
                
                if certificates:
                    for cert in certificates:
                        status_icon = "✅" if cert.get('is_active') else "⚠️"
                        env_icon = "🔴" if cert.get('environment') == 'production' else "🟡"
                        
                        with st.expander(
                            f"{status_icon} {env_icon} {cert['name']} - "
                            f"Válido até: {cert.get('valid_until', 'N/A')[:10]}"
                        ):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**ID:** {cert['id']}")
                                st.write(f"**Nome:** {cert['name']}")
                                st.write(f"**Ambiente:** {cert.get('environment', 'N/A').title()}")
                                st.write(f"**Status:** {'Ativo' if cert.get('is_active') else 'Inativo'}")
                            
                            with col2:
                                st.write(f"**Subject:** {cert.get('subject', 'N/A')[:50]}...")
                                st.write(f"**Válido Até:** {cert.get('valid_until', 'N/A')[:19]}")
                                st.write(f"**Cadastrado em:** {cert.get('created_at', 'N/A')[:19]}")
                            
                            col_test, col_delete = st.columns(2)
                            
                            with col_test:
                                test_password = st.text_input(
                                    "Senha",
                                    type="password",
                                    key=f"test_pwd_{cert['id']}"
                                )
                                
                                if st.button(f"🔍 Testar Certificado", key=f"test_{cert['id']}"):
                                    if test_password:
                                        try:
                                            test_response = requests.post(
                                                f"{API_URL}/api/sefaz/certificates/{cert['id']}/test",
                                                params={'password': test_password}
                                            )
                                            
                                            if test_response.status_code == 200:
                                                test_result = test_response.json()
                                                
                                                if test_result['valid']:
                                                    st.success(test_result['message'])
                                                    if test_result.get('details'):
                                                        details = test_result['details']
                                                        st.info(f"Dias até expiração: {details.get('days_until_expiry', 'N/A')}")
                                                else:
                                                    st.error(test_result['message'])
                                        except Exception as e:
                                            st.error(f"Erro: {str(e)}")
                                    else:
                                        st.warning("Informe a senha")
                            
                            with col_delete:
                                st.write("")  # Spacing
                                st.write("")  # Spacing
                                if st.button(f"🗑️ Remover", key=f"delete_{cert['id']}", type="secondary"):
                                    try:
                                        delete_response = requests.delete(
                                            f"{API_URL}/api/sefaz/certificates/{cert['id']}"
                                        )
                                        
                                        if delete_response.status_code == 200:
                                            st.success("Certificado removido")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {str(e)}")
                else:
                    st.info("📭 Nenhum certificado cadastrado. Adicione um certificado acima para começar.")
            else:
                st.error("Erro ao carregar certificados")
        
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    
    # === TAB 2: SINCRONIZAÇÃO ===
    with tab2:
        st.subheader("Sincronizar Documentos da SEFAZ")
        
        st.info("""
        ℹ️ **Sobre a Sincronização:**
        
        Esta funcionalidade permite buscar notas fiscais eletrônicas diretamente dos portais 
        da SEFAZ usando seu certificado digital. 
        
        **Nota**: A implementação completa requer assinatura digital XML e integração SOAP 
        avançada com os web services da SEFAZ, que está em desenvolvimento.
        """)
        
        try:
            # Lista certificados disponíveis
            cert_response = requests.get(f"{API_URL}/api/sefaz/certificates")
            
            if cert_response.status_code == 200:
                certificates = cert_response.json()
                
                if certificates:
                    cert_options = {
                        f"{cert['name']} (ID: {cert['id']})": cert['id'] 
                        for cert in certificates if cert.get('is_active')
                    }
                    
                    if cert_options:
                        selected_cert_label = st.selectbox(
                            "Selecione o Certificado",
                            options=list(cert_options.keys())
                        )
                        
                        selected_cert_id = cert_options[selected_cert_label]
                        
                        sync_password = st.text_input(
                            "Senha do Certificado",
                            type="password",
                            key="sync_password"
                        )
                        
                        sync_cnpj = st.text_input(
                            "CNPJ Destinatário",
                            placeholder="12345678000190",
                            help="CNPJ da empresa destinatária (apenas números)"
                        )
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            sync_uf = st.selectbox(
                                "Estado (UF)",
                                options=['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'PE', 'CE', 'GO', 'DF']
                            )
                        
                        with col2:
                            sync_env = st.selectbox(
                                "Ambiente",
                                options=["homologation", "production"],
                                format_func=lambda x: "Homologação" if x == "homologation" else "Produção"
                            )
                        
                        if st.button("🔄 Sincronizar com SEFAZ", use_container_width=True, type="primary"):
                            if not sync_password or not sync_cnpj:
                                st.error("Preencha todos os campos")
                            else:
                                with st.spinner("Consultando SEFAZ..."):
                                    try:
                                        sync_response = requests.post(
                                            f"{API_URL}/api/sefaz/sync",
                                            params={
                                                'credential_id': selected_cert_id,
                                                'password': sync_password,
                                                'cnpj': sync_cnpj,
                                                'uf': sync_uf,
                                                'environment': sync_env
                                            }
                                        )
                                        
                                        if sync_response.status_code == 200:
                                            result = sync_response.json()
                                            
                                            if result['success']:
                                                st.success(f"✅ {result['message']}")
                                                st.metric("Documentos Encontrados", result['documents_found'])
                                            else:
                                                st.warning(f"⚠️ {result['message']}")
                                        else:
                                            st.error(f"Erro na sincronização: {sync_response.text}")
                                    
                                    except Exception as e:
                                        st.error(f"Erro: {str(e)}")
                    else:
                        st.warning("⚠️ Nenhum certificado ativo disponível. Adicione um certificado na aba 'Certificados'.")
                else:
                    st.info("📭 Nenhum certificado cadastrado. Adicione um certificado na aba 'Certificados' primeiro.")
        
        except Exception as e:
            st.error(f"Erro: {str(e)}")
    
    # === TAB 3: INFORMAÇÕES ===
    with tab3:
        st.subheader("Informações sobre Integração SEFAZ")
        
        st.write("""
        ### 📋 O que é a Integração com SEFAZ?
        
        A SEFAZ (Secretaria da Fazenda) mantém portais onde empresas podem consultar e baixar 
        notas fiscais eletrônicas destinadas a elas.
        
        ### 🔐 Certificado Digital
        
        **Certificado A1:**
        - Formato: arquivo digital (.pfx ou .p12)
        - Validade: geralmente 1 ano
        - Protegido por senha
        - Armazenado no computador
        
        **Segurança:**
        - Certificados são criptografados com AES-256-GCM antes de serem armazenados
        - Senhas nunca são armazenadas (apenas hash SHA-256)
        - Acesso requer a senha original
        
        ### 📡 Serviços Disponíveis
        
        **1. NFeDistribuicaoDFe** - Portal Nacional
        - Consulta NFe destinadas
        - Download de XMLs oficiais
        - Manifestação do destinatário
        
        **2. Status da Implementação:**
        - ✅ Upload e armazenamento seguro de certificados
        - ✅ Validação e teste de certificados
        - ⚙️ Integração SOAP com SEFAZ (em desenvolvimento)
        - ⚙️ Assinatura digital XML (em desenvolvimento)
        - ⚙️ Download automático de XMLs (em desenvolvimento)
        
        ### 🛡️ Ambientes
        
        **Homologação:**
        - Ambiente de testes
        - Não afeta dados reais
        - Recomendado para primeiros testes
        
        **Produção:**
        - Ambiente real
        - Operações oficiais
        - Requer certificado de produção
        
        ### 📞 Suporte
        
        Para dúvidas sobre certificados digitais, consulte:
        - ICP-Brasil: https://www.gov.br/iti
        - Portal NFe: https://www.nfe.fazenda.gov.br
        """)
