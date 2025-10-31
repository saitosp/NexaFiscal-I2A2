"""
LangGraph Workflow - Orquestra o fluxo de processamento de notas fiscais
"""
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from agents.classification_agent import ClassificationAgent
from agents.extraction_agent import ExtractionAgent
from agents.validation_agent import ValidationAgent
from utils.file_processor import process_pdf, process_xml, process_image, get_file_type


class WorkflowState(TypedDict):
    """
    Estado do workflow de processamento de notas fiscais
    """
    file_path: str
    filename: str
    processed_data: Dict[str, Any]
    classification: Dict[str, Any]
    extracted_data: Dict[str, Any]
    validation: Dict[str, Any]
    status: str
    errors: list


def process_file_node(state: WorkflowState) -> WorkflowState:
    """
    Nó que processa o arquivo de entrada
    """
    file_path = state['file_path']
    filename = state['filename']
    
    # Determina tipo e processa
    file_type = get_file_type(filename)
    
    if file_type == 'xml':
        processed = process_xml(file_path)
    elif file_type == 'pdf':
        processed = process_pdf(file_path)
    elif file_type == 'image':
        processed = process_image(file_path)
    else:
        processed = {'success': False, 'error': 'Formato não suportado'}
    
    state['processed_data'] = processed
    state['status'] = 'processed'
    
    if not processed.get('success', False):
        state['errors'] = state.get('errors', [])
        state['errors'].append(processed.get('error', 'Erro no processamento'))
    
    return state


def classify_node(state: WorkflowState) -> WorkflowState:
    """
    Nó que classifica o documento
    """
    try:
        agent = ClassificationAgent()
        return agent.classify(state)
    except ValueError as e:
        # GROQ_API_KEY não configurada
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro de configuração: {str(e)}")
        state['status'] = 'error'
        return state
    except Exception as e:
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro na classificação: {str(e)}")
        state['status'] = 'error'
        return state


def extract_node(state: WorkflowState) -> WorkflowState:
    """
    Nó que extrai dados do documento
    """
    try:
        agent = ExtractionAgent()
        return agent.extract(state)
    except ValueError as e:
        # GROQ_API_KEY não configurada
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro de configuração: {str(e)}")
        state['status'] = 'error'
        return state
    except Exception as e:
        state['errors'] = state.get('errors', [])
        state['errors'].append(f"Erro na extração: {str(e)}")
        state['status'] = 'error'
        return state


def validate_node(state: WorkflowState) -> WorkflowState:
    """
    Nó que valida os dados extraídos
    """
    agent = ValidationAgent()
    return agent.validate(state)


def should_continue(state: WorkflowState) -> str:
    """
    Determina se o workflow deve continuar
    """
    if state.get('errors'):
        return END
    
    status = state.get('status', '')
    
    if status == 'processed':
        return 'classify'
    elif status == 'classified':
        return 'extract'
    elif status == 'extracted':
        return 'validate'
    elif status == 'validated':
        return END
    
    return END


def create_workflow_graph():
    """
    Cria o grafo de workflow modular usando LangGraph
    
    Fluxo:
    1. process_file -> Processa arquivo (XML, PDF, imagem)
    2. classify -> Classifica tipo de nota fiscal
    3. extract -> Extrai dados estruturados
    4. validate -> Valida dados extraídos
    """
    # Cria o grafo
    workflow = StateGraph(WorkflowState)
    
    # Adiciona os nós (agentes)
    workflow.add_node("process_file", process_file_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("validate", validate_node)
    
    # Define o ponto de entrada
    workflow.set_entry_point("process_file")
    
    # Define as transições
    workflow.add_conditional_edges(
        "process_file",
        should_continue
    )
    workflow.add_conditional_edges(
        "classify",
        should_continue
    )
    workflow.add_conditional_edges(
        "extract",
        should_continue
    )
    workflow.add_conditional_edges(
        "validate",
        should_continue
    )
    
    # Compila o grafo
    return workflow.compile()


def process_invoice(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Processa uma nota fiscal através do workflow
    
    Args:
        file_path: Caminho do arquivo
        filename: Nome do arquivo
        
    Returns:
        Resultado do processamento
    """
    # Cria o workflow
    workflow = create_workflow_graph()
    
    # Estado inicial
    initial_state = {
        'file_path': file_path,
        'filename': filename,
        'processed_data': {},
        'classification': {},
        'extracted_data': {},
        'validation': {},
        'status': 'pending',
        'errors': []
    }
    
    # Executa o workflow
    result = workflow.invoke(initial_state)
    
    return result
