"""
Página de Chat Inteligente - Interação com agentes especializados
"""
import streamlit as st
import requests
import os
from datetime import datetime

API_BASE_URL = "http://localhost:8000"


def init_session_state():
    """Inicializa estado da sessão"""
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'show_reasoning' not in st.session_state:
        st.session_state.show_reasoning = True


def create_chat_session():
    """Cria nova sessão de chat"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/chat/session",
            json={
                "user_id": "default",
                "title": f"Chat {datetime.now().strftime('%d/%m %H:%M')}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['session_id']
        else:
            st.error(f"Erro ao criar sessão: {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Erro ao conectar com API: {e}")
        return None


def send_message(session_id, message, file_path=None, filename=None):
    """Envia mensagem para API"""
    try:
        payload = {
            "session_id": session_id,
            "message": message
        }
        
        if file_path and filename:
            payload["uploaded_file_path"] = file_path
            payload["uploaded_filename"] = filename
        
        response = requests.post(
            f"{API_BASE_URL}/api/chat/message",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "role": "assistant",
                "content": f"❌ Erro: {response.text}",
                "error": response.text
            }
            
    except requests.exceptions.Timeout:
        return {
            "role": "assistant",
            "content": "⏱️ Processamento demorou muito. Tente novamente.",
            "error": "timeout"
        }
    except Exception as e:
        return {
            "role": "assistant",
            "content": f"❌ Erro ao enviar mensagem: {str(e)}",
            "error": str(e)
        }


def display_message(message_data, show_details=False):
    """Exibe uma mensagem no chat"""
    role = message_data.get('role', 'user')
    content = message_data.get('content', '')
    
    with st.chat_message(role):
        st.markdown(content)
        
        # Mostra detalhes do processamento se for resposta do assistente
        if role == 'assistant' and show_details:
            agent_used = message_data.get('agent_used')
            reasoning = message_data.get('reasoning')
            critic_analysis = message_data.get('critic_analysis')
            confidence = message_data.get('confidence_score')
            
            if agent_used or reasoning or critic_analysis:
                with st.expander("🔍 Ver Raciocínio do Agente"):
                    if agent_used:
                        st.caption(f"**Agente Utilizado:** `{agent_used}`")
                    
                    if reasoning:
                        st.markdown("**💭 Análise de Intenção:**")
                        st.info(reasoning)
                    
                    if critic_analysis:
                        st.markdown("**✅ Análise Crítica:**")
                        st.success(critic_analysis)
                    
                    if confidence:
                        st.metric("Confiança", f"{confidence:.1%}")


def main():
    st.set_page_config(
        page_title="Chat - NFe Extractor",
        page_icon="💬",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("💬 Chat Inteligente - NexaFiscal")
    
    st.markdown("""
    Converse com o sistema e faça perguntas! O agente orquestrador analisará sua intenção
    e acionará especialistas conforme necessário.
    """)
    
    # Sidebar para configurações
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        # Toggle para mostrar raciocínio
        st.session_state.show_reasoning = st.checkbox(
            "Mostrar raciocínio dos agentes",
            value=st.session_state.show_reasoning,
            help="Exibe a análise de intenção e crítica do agente"
        )
        
        st.divider()
        
        # Informações da sessão
        if st.session_state.chat_session_id:
            st.success("✅ Sessão ativa")
            st.caption(f"ID: {st.session_state.chat_session_id[:8]}...")
            
            if st.button("🔄 Nova Conversa"):
                st.session_state.chat_session_id = None
                st.session_state.chat_messages = []
                st.rerun()
        else:
            st.info("💡 Envie uma mensagem para iniciar")
        
        st.divider()
        
        # Upload de arquivo
        st.markdown("### 📎 Upload de Documento")
        uploaded_file = st.file_uploader(
            "Arquivo fiscal (opcional)",
            type=['xml', 'pdf', 'jpg', 'jpeg', 'png'],
            help="Envie junto com sua mensagem para processar"
        )
        
        st.divider()
        
        # Exemplos de perguntas
        st.markdown("### 💡 Exemplos de Perguntas")
        st.caption("• Quantos documentos foram processados?")
        st.caption("• Qual o valor total das notas?")
        st.caption("• Mostre os últimos documentos")
        st.caption("• Como funciona o sistema?")
        st.caption("• [Com upload] Processe este documento")
    
    # Container para mensagens
    chat_container = st.container()
    
    # Exibe mensagens existentes
    with chat_container:
        for msg in st.session_state.chat_messages:
            display_message(msg, show_details=st.session_state.show_reasoning)
    
    # Input de mensagem
    if prompt := st.chat_input("Digite sua mensagem..."):
        # Cria sessão se não existir
        if not st.session_state.chat_session_id:
            session_id = create_chat_session()
            if session_id:
                st.session_state.chat_session_id = session_id
            else:
                st.error("Não foi possível criar sessão de chat")
                return
        
        # Adiciona mensagem do usuário
        user_message = {"role": "user", "content": prompt}
        st.session_state.chat_messages.append(user_message)
        
        with chat_container:
            display_message(user_message)
        
        # Processa upload se houver
        file_path = None
        filename = None
        
        if uploaded_file is not None:
            upload_dir = "data/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, uploaded_file.name)
            filename = uploaded_file.name
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Envia mensagem e obtém resposta
        with st.spinner("🤔 Pensando..."):
            response = send_message(
                st.session_state.chat_session_id,
                prompt,
                file_path,
                filename
            )
        
        # Adiciona resposta
        st.session_state.chat_messages.append(response)
        
        with chat_container:
            display_message(response, show_details=st.session_state.show_reasoning)
        
        # Força rerun para limpar input
        st.rerun()


if __name__ == "__main__":
    main()
