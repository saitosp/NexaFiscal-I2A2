"""
FastAPI REST API for NFe extraction system
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import shutil
from datetime import datetime
import asyncio

from api.schemas import (
    DocumentUploadResponse,
    DocumentSummary,
    DocumentDetail,
    AgentLogSummary,
    StatisticsResponse,
    ProcessingQueueItem,
    BatchStatusResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatHistoryResponse
)
from services.document_service import DocumentService
from services.batch_service import BatchService
from services.sefaz_service import SefazService
from database import get_session, AgentLogRepository, ProcessingQueueRepository
from workflow_graph import process_invoice
from agents.integration_agent import IntegrationAgent

app = FastAPI(
    title="NFe Extraction API",
    description="API REST para extração automatizada de dados de notas fiscais brasileiras",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Inicia o batch worker quando a API inicia
    """
    asyncio.create_task(batch_worker())


@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "online",
        "service": "NFe Extraction API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload e processa um documento fiscal
    
    - **file**: Arquivo XML, PDF ou imagem da nota fiscal
    """
    allowed_extensions = ['xml', 'pdf', 'jpg', 'jpeg', 'png']
    file_extension = file.filename.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado. Use: {', '.join(allowed_extensions)}"
        )
    
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        result = process_invoice(file_path, file.filename)
        
        result['filename'] = file.filename
        result['file_path'] = file_path
        
        doc = DocumentService.save_processed_document(result)
        
        return DocumentUploadResponse(
            document_id=doc.id,
            filename=file.filename,
            status="completed" if not result.get('errors') else "failed",
            message="Documento processado com sucesso" if not result.get('errors') else "Documento processado com erros"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")
    
    finally:
        file.file.close()


@app.get("/api/documents", response_model=List[DocumentSummary])
async def list_documents(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = None,
    document_type: Optional[str] = None
):
    """
    Lista documentos processados
    
    - **limit**: Número máximo de resultados (máx 100)
    - **offset**: Offset para paginação
    - **search**: Busca por nome de arquivo ou emitente
    - **document_type**: Filtro por tipo de documento
    """
    try:
        if search or document_type:
            docs = DocumentService.search_documents(search or "", document_type)
        else:
            docs = DocumentService.get_all_documents(limit, offset)
        
        return [DocumentSummary.from_orm(doc) for doc in docs]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents")
async def delete_all_documents():
    """
    Deleta todos os documentos do banco de dados
    
    ⚠️ ATENÇÃO: Esta é uma operação destrutiva e irreversível!
    
    Returns:
        Mensagem de confirmação com número de documentos deletados
    """
    try:
        count = DocumentService.delete_all_documents()
        return {
            "success": True,
            "message": f"{count} documentos foram deletados com sucesso",
            "deleted_count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}", response_model=DocumentDetail)
async def get_document(document_id: int):
    """
    Busca documento por ID
    
    - **document_id**: ID do documento
    """
    doc = DocumentService.get_document_by_id(document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    return DocumentDetail.from_orm(doc)


@app.get("/api/documents/{document_id}/logs", response_model=List[AgentLogSummary])
async def get_document_logs(document_id: int):
    """
    Busca logs de processamento de um documento
    
    - **document_id**: ID do documento
    """
    doc = DocumentService.get_document_by_id(document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    session = get_session()
    try:
        logs = AgentLogRepository.get_logs_by_document(session, document_id)
        return [AgentLogSummary.from_orm(log) for log in logs]
    finally:
        session.close()


@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Retorna estatísticas gerais do sistema
    """
    try:
        stats = DocumentService.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue", response_model=List[ProcessingQueueItem])
async def get_queue(limit: int = Query(default=10, le=50)):
    """
    Lista itens pendentes na fila de processamento
    
    - **limit**: Número máximo de itens
    """
    session = get_session()
    try:
        items = ProcessingQueueRepository.get_pending_items(session, limit)
        return [ProcessingQueueItem.from_orm(item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


@app.get("/api/queue/batch/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """
    Retorna status de um lote de processamento
    
    - **batch_id**: ID do lote
    """
    session = get_session()
    try:
        status = ProcessingQueueRepository.get_batch_status(session, batch_id)
        return BatchStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# ========== BATCH PROCESSING ENDPOINTS ==========

@app.post("/api/batch/upload")
async def upload_batch(files: List[UploadFile] = File(...)):
    """
    Upload e enfileira múltiplos documentos para processamento em lote
    
    - **files**: Lista de arquivos (XML, PDF ou imagem)
    
    Returns:
        {
            "batch_id": str,
            "total_files": int,
            "message": str
        }
    """
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
    
    allowed_extensions = ['xml', 'pdf', 'jpg', 'jpeg', 'png']
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    files_data = []
    
    for file in files:
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            continue
        
        file_path = os.path.join(upload_dir, file.filename)
        
        try:
            with open(file_path, "wb") as buffer:
                file_content = await file.read()
                buffer.write(file_content)
            
            files_data.append({
                'filename': file.filename,
                'file_path': file_path,
                'file_content': file_content
            })
        except Exception as e:
            print(f"Erro ao salvar {file.filename}: {str(e)}")
    
    if not files_data:
        raise HTTPException(
            status_code=400,
            detail=f"Nenhum arquivo válido. Use: {', '.join(allowed_extensions)}"
        )
    
    try:
        batch_id = BatchService.create_batch(files_data)
        
        return {
            "batch_id": batch_id,
            "total_files": len(files_data),
            "message": f"{len(files_data)} arquivos enfileirados para processamento"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar lote: {str(e)}")


@app.get("/api/batch/{batch_id}/status")
async def get_batch_processing_status(batch_id: str):
    """
    Obtém status detalhado de um lote de processamento
    
    - **batch_id**: ID do lote
    
    Returns:
        {
            "batch_id": str,
            "total": int,
            "pending": int,
            "processing": int,
            "completed": int,
            "failed": int,
            "items": List[Dict]
        }
    """
    try:
        status = BatchService.get_batch_status(batch_id)
        
        if status['total'] == 0:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch/{batch_id}/retry")
async def retry_batch_failures(batch_id: str):
    """
    Reprocessa documentos com falha em um lote
    
    - **batch_id**: ID do lote
    
    Returns:
        {
            "batch_id": str,
            "retried_count": int,
            "message": str
        }
    """
    try:
        count = BatchService.retry_failed(batch_id)
        
        return {
            "batch_id": batch_id,
            "retried_count": count,
            "message": f"{count} documentos resetados para reprocessamento"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/batches")
async def list_batches(limit: int = Query(default=50, le=100)):
    """
    Lista todos os lotes de processamento
    
    - **limit**: Número máximo de lotes
    
    Returns:
        List[{
            "batch_id": str,
            "total": int,
            "pending": int,
            "processing": int,
            "completed": int,
            "failed": int,
            "created_at": str
        }]
    """
    try:
        batches = BatchService.get_all_batches(limit)
        
        for batch in batches:
            if batch.get('created_at'):
                batch['created_at'] = batch['created_at'].isoformat()
        
        return batches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== BATCH WORKER ==========

def process_queue_item(queue_item):
    """
    Processa um único item da fila
    """
    try:
        BatchService.mark_processing(queue_item.id)
        
        result = process_invoice(queue_item.file_path, queue_item.filename)
        result['filename'] = queue_item.filename
        result['file_path'] = queue_item.file_path
        
        if result.get('errors'):
            error_msg = '; '.join(str(e) for e in result['errors'])
            BatchService.mark_failed(queue_item.id, error_msg)
        else:
            doc_id = DocumentService.save_processed_document(result)
            BatchService.mark_completed(queue_item.id, doc_id)
        
    except Exception as e:
        BatchService.mark_failed(queue_item.id, str(e))


async def batch_worker():
    """
    Worker que processa items pendentes da fila continuamente
    """
    while True:
        try:
            pending_items = BatchService.get_next_pending(limit=5)
            
            if pending_items:
                for item in pending_items:
                    try:
                        process_queue_item(item)
                    except Exception as e:
                        print(f"Erro ao processar item {item.id}: {str(e)}")
            else:
                await asyncio.sleep(5)
        
        except Exception as e:
            print(f"Erro no worker: {str(e)}")
            await asyncio.sleep(10)


@app.post("/api/batch/{batch_id}/process")
async def start_batch_processing(batch_id: str, background_tasks: BackgroundTasks):
    """
    Inicia processamento em background de um lote
    
    - **batch_id**: ID do lote
    
    Returns:
        {
            "batch_id": str,
            "message": str
        }
    """
    try:
        status = BatchService.get_batch_status(batch_id)
        
        if status['total'] == 0:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        
        if status['pending'] == 0:
            return {
                "batch_id": batch_id,
                "message": "Nenhum documento pendente para processar"
            }
        
        pending_items = [item for item in status['items'] if item['status'] == 'pending']
        
        for item_data in pending_items[:10]:
            pending_item = BatchService.get_next_pending(limit=1)
            if pending_item:
                background_tasks.add_task(process_queue_item, pending_item[0])
        
        return {
            "batch_id": batch_id,
            "message": f"Processamento iniciado para {min(status['pending'], 10)} documentos"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== SEFAZ INTEGRATION ENDPOINTS ==========

@app.post("/api/sefaz/certificates")
async def upload_certificate(
    file: UploadFile = File(...),
    password: str = Query(...),
    name: str = Query(...),
    environment: str = Query(default='homologation')
):
    """
    Upload e processa certificado digital A1 (.pfx/.p12)
    
    - **file**: Arquivo de certificado (.pfx ou .p12)
    - **password**: Senha do certificado
    - **name**: Nome identificador
    - **environment**: production ou homologation
    
    Returns:
        {
            "credential_id": int,
            "name": str,
            "subject": str,
            "valid_until": str
        }
    """
    allowed_extensions = ['pfx', 'p12']
    file_extension = file.filename.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado. Use: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Lê conteúdo do arquivo
        certificate_content = await file.read()
        
        # Processa certificado
        result = SefazService.process_certificate(
            certificate_file=certificate_content,
            password=password,
            name=name,
            environment=environment
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar certificado: {str(e)}")
    finally:
        file.file.close()


@app.get("/api/sefaz/certificates")
async def list_certificates():
    """
    Lista todos os certificados cadastrados
    
    Returns:
        List[{
            "id": int,
            "name": str,
            "environment": str,
            "is_active": bool,
            "valid_until": str,
            "subject": str
        }]
    """
    try:
        certificates = SefazService.list_certificates()
        return certificates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sefaz/certificates/{credential_id}")
async def delete_certificate(credential_id: int):
    """
    Remove um certificado
    
    - **credential_id**: ID da credencial
    """
    try:
        success = SefazService.delete_certificate(credential_id)
        
        if success:
            return {"message": "Certificado removido com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Certificado não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sefaz/certificates/{credential_id}/test")
async def test_certificate(credential_id: int, password: str = Query(...)):
    """
    Testa se um certificado pode ser carregado
    
    - **credential_id**: ID da credencial
    - **password**: Senha do certificado
    
    Returns:
        {
            "valid": bool,
            "message": str,
            "details": Dict
        }
    """
    try:
        result = SefazService.test_certificate(credential_id, password)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sefaz/sync")
async def sync_nfe_from_sefaz(
    credential_id: int = Query(...),
    password: str = Query(...),
    cnpj: str = Query(...),
    uf: str = Query(default='SP'),
    environment: str = Query(default='homologation')
):
    """
    Sincroniza NFe destinadas do portal da SEFAZ
    
    - **credential_id**: ID da credencial
    - **password**: Senha do certificado
    - **cnpj**: CNPJ do destinatário
    - **uf**: Estado (SP, RJ, MG, etc)
    - **environment**: production ou homologation
    
    Returns:
        {
            "success": bool,
            "message": str,
            "documents_found": int
        }
    """
    try:
        agent = IntegrationAgent()
        
        result = agent.consultar_nfe_destinadas(
            credential_id=credential_id,
            password=password,
            cnpj=cnpj,
            uf=uf,
            environment=environment
        )
        
        return {
            "success": result['success'],
            "message": result['message'],
            "documents_found": len(result.get('documents', []))
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sefaz/status/{credential_id}")
async def get_sefaz_status(credential_id: int, password: str = Query(...)):
    """
    Verifica status da integração com SEFAZ
    
    - **credential_id**: ID da credencial
    - **password**: Senha do certificado
    
    Returns:
        {
            "certificate_valid": bool,
            "can_connect": bool,
            "services_available": List[str],
            "message": str
        }
    """
    try:
        agent = IntegrationAgent()
        status = agent.get_integration_status(credential_id, password)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/session", response_model=ChatSessionResponse)
async def create_chat_session(request: ChatSessionCreate):
    """
    Cria nova sessão de chat
    
    - **user_id**: ID do usuário (opcional)
    - **title**: Título da sessão (opcional)
    """
    from services.chat_service import ChatService
    from database import get_session
    
    try:
        db = get_session()
        session = ChatService.create_session(
            db,
            user_id=request.user_id,
            title=request.title
        )
        db.close()
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatMessageCreate):
    """
    Envia mensagem e recebe resposta do sistema
    
    - **session_id**: ID da sessão
    - **message**: Mensagem do usuário
    - **uploaded_file_path**: Caminho do arquivo (opcional)
    - **uploaded_filename**: Nome do arquivo (opcional)
    """
    from services.chat_service import ChatService
    from database import get_session
    
    try:
        db = get_session()
        response = ChatService.process_message(
            db,
            session_id=request.session_id,
            user_message=request.message,
            uploaded_file_path=request.uploaded_file_path,
            uploaded_filename=request.uploaded_filename
        )
        db.close()
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str, limit: int = Query(50)):
    """
    Obtém histórico de mensagens de uma sessão
    
    - **session_id**: ID da sessão
    - **limit**: Número máximo de mensagens (padrão: 50)
    """
    from services.chat_service import ChatService
    from database import get_session
    
    try:
        db = get_session()
        messages = ChatService.get_conversation_history(db, session_id, limit=limit)
        db.close()
        return {
            "session_id": session_id,
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions")
async def list_chat_sessions(user_id: str = Query("default"), limit: int = Query(20)):
    """
    Lista sessões de chat de um usuário
    
    - **user_id**: ID do usuário (padrão: "default")
    - **limit**: Número máximo de sessões (padrão: 20)
    """
    from services.chat_service import ChatService
    from database import get_session
    
    try:
        db = get_session()
        sessions = ChatService.list_sessions(db, user_id=user_id, limit=limit)
        db.close()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Deleta uma sessão de chat
    
    - **session_id**: ID da sessão
    """
    from services.chat_service import ChatService
    from database import get_session
    
    try:
        db = get_session()
        success = ChatService.delete_session(db, session_id)
        db.close()
        
        if success:
            return {"success": True, "message": "Sessão deletada com sucesso"}
        else:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
