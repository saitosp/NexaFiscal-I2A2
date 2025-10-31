"""
Chat Workflow - Orquestra agentes para sistema de chat inteligente
"""
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END
from agents.orchestrator_agent import ChatOrchestratorAgent
from agents.critic_agent import CriticAgent
from agents.classification_agent import ClassificationAgent
from agents.extraction_agent import ExtractionAgent
from agents.validation_agent import ValidationAgent
from utils.file_processor import process_pdf, process_xml, process_image, get_file_type
from workflow_graph import WorkflowState, create_workflow_graph


class ChatState(TypedDict):
    """
    Estado do workflow de chat
    """
    user_message: str
    conversation_history: List[Dict[str, Any]]
    uploaded_file_path: str
    uploaded_filename: str
    
    intent_analysis: Dict[str, Any]
    agent_response: str
    agent_name: str
    agent_data: Dict[str, Any]
    critic_review: Dict[str, Any]
    
    final_response: str
    status: str
    errors: List[str]


def analyze_intent_node(state: ChatState) -> ChatState:
    """
    Nó que analisa a intenção do usuário
    """
    try:
        orchestrator = ChatOrchestratorAgent()
        
        intent = orchestrator.analyze_intent(
            state['user_message'],
            state.get('conversation_history', [])
        )
        
        state['intent_analysis'] = intent
        state['agent_name'] = intent.get('agent', 'general')
        state['status'] = 'intent_analyzed'
        
        return state
        
    except Exception as e:
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro ao analisar intenção: {str(e)}")
        state['status'] = 'error'
        return state


def process_document_node(state: ChatState) -> ChatState:
    """
    Nó que processa documento fiscal usando workflow existente
    """
    try:
        file_path = state.get('uploaded_file_path')
        filename = state.get('uploaded_filename')
        
        if not file_path or not filename:
            state['agent_response'] = "Por favor, faça upload de um documento fiscal para processar."
            state['status'] = 'agent_completed'
            return state
        
        # Usa workflow existente de processamento
        workflow = create_workflow_graph()
        
        workflow_state = {
            'file_path': file_path,
            'filename': filename,
            'processed_data': {},
            'classification': {},
            'extracted_data': {},
            'validation': {},
            'status': '',
            'errors': []
        }
        
        result = workflow.invoke(workflow_state)
        
        # Formata resposta baseada no resultado
        if result.get('errors'):
            response = f"❌ Erro ao processar documento:\n{', '.join(result['errors'])}"
        else:
            classification = result.get('classification', {})
            extracted = result.get('extracted_data', {})
            validation = result.get('validation', {})
            
            doc_type = classification.get('document_type', 'Desconhecido')
            emitente = extracted.get('emitente', {}).get('nome', 'N/A')
            total = extracted.get('totais', {}).get('valor_total', 0)
            is_valid = validation.get('is_valid', False)
            
            response = f"""✅ Documento processado com sucesso!

📄 **Tipo**: {doc_type}
🏢 **Emitente**: {emitente}
💰 **Valor Total**: R$ {total:,.2f}
{"✓ Validação: Aprovada" if is_valid else "⚠️ Validação: Com ressalvas"}

Documento salvo no sistema. Você pode consultar detalhes ou fazer perguntas sobre ele."""
        
        state['agent_response'] = response
        state['agent_data'] = result
        state['status'] = 'agent_completed'
        
        return state
        
    except Exception as e:
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro ao processar documento: {str(e)}")
        state['agent_response'] = f"Desculpe, ocorreu um erro ao processar o documento: {str(e)}"
        state['status'] = 'agent_completed'
        return state


def query_data_node(state: ChatState) -> ChatState:
    """
    Nó que consulta dados de documentos processados
    """
    try:
        from database import get_session, DocumentRepository
        
        user_message = state['user_message'].lower()
        
        # Obtém dados do banco
        session = get_session()
        
        # Estatísticas gerais
        stats = DocumentRepository.get_statistics(session)
        
        response_parts = []
        
        # Perguntas sobre impostos
        if any(word in user_message for word in ['imposto', 'impostos', 'tributo', 'tributação', 'icms', 'pis', 'cofins']):
            tax_total = stats.get('tax_total', 0)
            response_parts.append(f"""💰 **Total de Impostos:**

🏛️ **Impostos totais pagos**: R$ {tax_total:,.2f}

Baseado em {stats['total']} documento(s) processado(s).
""")
            if stats['total'] > 0:
                avg_tax = tax_total / stats['total']
                response_parts.append(f"📊 Média de impostos por documento: R$ {avg_tax:,.2f}")
        
        # Perguntas sobre valores totais
        elif any(word in user_message for word in ['valor', 'valores', 'total', 'quanto', 'soma']):
            total_value = stats.get('total_value', 0)
            tax_total = stats.get('tax_total', 0)
            
            response_parts.append(f"""💰 **Resumo Financeiro:**

📝 Total de documentos: {stats['total']}
💵 Valor total: R$ {total_value:,.2f}
🏛️ Impostos totais: R$ {tax_total:,.2f}
""")
            if total_value > 0:
                tax_percentage = (tax_total / total_value * 100) if total_value > 0 else 0
                response_parts.append(f"📊 Carga tributária: {tax_percentage:.2f}%")
        
        # Perguntas sobre quantidade de documentos
        elif any(word in user_message for word in ['quantos', 'quantidade', 'número']):
            response_parts.append(f"""📊 **Estatísticas do Sistema:**

📝 Total de documentos: {stats['total']}
✅ Válidos: {stats['valid']}
❌ Inválidos: {stats['invalid']}
💰 Valor total: R$ {stats['total_value']:,.2f}
🏛️ Total de impostos: R$ {stats['tax_total']:,.2f}
""")
            
            if stats['by_type']:
                response_parts.append("\n**Por Tipo de Documento:**")
                for doc_type, count in stats['by_type'].items():
                    response_parts.append(f"  • {doc_type}: {count}")
        
        # Documentos recentes
        elif any(word in user_message for word in ['último', 'últimos', 'recente', 'recentes']):
            recent = DocumentRepository.get_recent_documents(session, limit=5)
            
            if recent:
                response_parts.append("📄 **Documentos Recentes:**\n")
                for doc in recent:
                    response_parts.append(
                        f"• {doc.get('document_type', 'N/A')} - "
                        f"{doc.get('issuer_name', 'N/A')} - "
                        f"R$ {doc.get('total_value', 0):,.2f}"
                    )
            else:
                response_parts.append("Nenhum documento encontrado.")
        
        else:
            # Resposta genérica com estatísticas completas
            response_parts.append(f"""📊 **Resumo Geral:**

📝 Total de documentos: {stats['total']}
✅ Válidos: {stats['valid']}
❌ Inválidos: {stats['invalid']}
💰 Valor total: R$ {stats['total_value']:,.2f}
🏛️ Total de impostos: R$ {stats['tax_total']:,.2f}
""")
        
        state['agent_response'] = "\n".join(response_parts)
        state['agent_data'] = {'statistics': stats}
        state['status'] = 'agent_completed'
        
        session.close()
        return state
        
    except Exception as e:
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro ao consultar dados: {str(e)}")
        state['agent_response'] = f"Desculpe, ocorreu um erro ao consultar os dados: {str(e)}"
        state['status'] = 'agent_completed'
        return state


def general_response_node(state: ChatState) -> ChatState:
    """
    Nó que gera resposta para perguntas gerais
    """
    try:
        orchestrator = ChatOrchestratorAgent()
        
        response = orchestrator.generate_response(
            state['user_message'],
            context=state.get('intent_analysis', {})
        )
        
        state['agent_response'] = response
        state['status'] = 'agent_completed'
        
        return state
        
    except Exception as e:
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro ao gerar resposta: {str(e)}")
        state['agent_response'] = "Desculpe, não consegui processar sua mensagem. Pode reformular?"
        state['status'] = 'agent_completed'
        return state


def out_of_scope_node(state: ChatState) -> ChatState:
    """
    Nó que responde quando a pergunta está fora do escopo do projeto
    """
    state['agent_response'] = """🚫 Desculpe, só posso responder perguntas relacionadas ao **sistema de processamento de notas fiscais brasileiras**.

📋 **Posso ajudar com:**
• Processamento de documentos fiscais (NFe, NFCe, SAT, CTe, NFSe)
• Consultas sobre dados fiscais processados
• Informações sobre impostos e tributação brasileira
• Integração com SEFAZ
• Certificados digitais A1
• Validação de CNPJ, CPF e chaves de acesso
• Análises e estatísticas de documentos fiscais
• Como usar o sistema

❌ **Não posso responder sobre:**
• Assuntos não relacionados a documentos fiscais
• Tópicos gerais não relacionados ao projeto

💡 Como posso ajudá-lo com **notas fiscais**?"""
    
    state['status'] = 'agent_completed'
    return state


def critic_review_node(state: ChatState) -> ChatState:
    """
    Nó que revisa criticamente a resposta do agente
    """
    try:
        critic = CriticAgent()
        
        review = critic.review_output(
            user_question=state['user_message'],
            agent_response=state['agent_response'],
            agent_name=state['agent_name'],
            agent_data=state.get('agent_data', {})
        )
        
        state['critic_review'] = review
        
        # Se qualidade baixa, tenta melhorar
        if review.get('quality_score', 0) < 70:
            improved = critic.improve_response(
                state['agent_response'],
                review,
                state['user_message']
            )
            state['final_response'] = improved
        else:
            state['final_response'] = state['agent_response']
        
        state['status'] = 'completed'
        
        return state
        
    except Exception as e:
        print(f"Erro na revisão crítica: {e}")
        state['critic_review'] = {"error": str(e)}
        state['final_response'] = state['agent_response']
        state['status'] = 'completed'
        return state


def route_by_intent(state: ChatState) -> str:
    """
    Determina qual nó executar baseado na intenção analisada
    """
    if state.get('errors'):
        return 'critic'
    
    agent = state.get('agent_name', 'general')
    
    if agent == 'out_of_scope':
        return 'out_of_scope'
    elif agent == 'document_processor':
        return 'process_document'
    elif agent == 'data_query':
        return 'query_data'
    else:
        return 'general'


def create_chat_workflow():
    """
    Cria e retorna o workflow compilado do chat
    """
    workflow = StateGraph(ChatState)
    
    # Adiciona nós
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("process_document", process_document_node)
    workflow.add_node("query_data", query_data_node)
    workflow.add_node("general", general_response_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    workflow.add_node("critic", critic_review_node)
    
    # Define ponto de entrada
    workflow.set_entry_point("analyze_intent")
    
    # Define transições
    workflow.add_conditional_edges(
        "analyze_intent",
        route_by_intent,
        {
            "process_document": "process_document",
            "query_data": "query_data",
            "general": "general",
            "out_of_scope": "out_of_scope",
            "critic": "critic"
        }
    )
    
    # Todos os agentes vão para o crítico
    workflow.add_edge("process_document", "critic")
    workflow.add_edge("query_data", "critic")
    workflow.add_edge("general", "critic")
    workflow.add_edge("out_of_scope", "critic")
    
    # Crítico é o fim
    workflow.add_edge("critic", END)
    
    return workflow.compile()
