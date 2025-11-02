"""
Chat Service - Gerencia sessões de chat e processamento de mensagens
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from database.models import ChatSession, ChatMessage
from chat_workflow import create_chat_workflow


class ChatService:
    """
    Serviço para gerenciamento de chat
    """
    
    @staticmethod
    def create_session(db: Session, user_id: str = "default", title: str = None) -> Dict[str, Any]:
        """
        Cria nova sessão de chat
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            title: Título opcional da sessão
            
        Returns:
            Dict com dados da sessão criada
        """
        session_id = str(uuid.uuid4())
        
        chat_session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title or f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            is_active=True,
            meta_data={}
        )
        
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        return {
            "id": chat_session.id,
            "session_id": chat_session.session_id,
            "title": chat_session.title,
            "user_id": chat_session.user_id,
            "is_active": chat_session.is_active,
            "created_at": chat_session.created_at.isoformat(),
            "message_count": 0
        }
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados de uma sessão
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            
        Returns:
            Dict com dados da sessão ou None
        """
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return None
        
        return {
            "id": session.id,
            "session_id": session.session_id,
            "title": session.title,
            "user_id": session.user_id,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat(),
            "message_count": len(session.messages)
        }
    
    @staticmethod
    def get_conversation_history(db: Session, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtém histórico de conversa de uma sessão
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            limit: Número máximo de mensagens
            
        Returns:
            Lista de mensagens
        """
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            return []
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
        
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "agent_used": msg.agent_used,
                "reasoning": msg.reasoning,
                "critic_analysis": msg.critic_analysis,
                "confidence_score": msg.confidence_score,
                "attached_document_id": msg.attached_document_id,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    
    @staticmethod
    def process_message(
        db: Session,
        session_id: str,
        user_message: str,
        uploaded_file_path: str = None,
        uploaded_filename: str = None
    ) -> Dict[str, Any]:
        """
        Processa mensagem do usuário através do workflow
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            user_message: Mensagem do usuário
            uploaded_file_path: Caminho do arquivo enviado (opcional)
            uploaded_filename: Nome do arquivo (opcional)
            
        Returns:
            Dict com resposta e metadados
        """
        # Verifica se sessão existe
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Sessão {session_id} não encontrada")
        
        # Salva mensagem do usuário
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=user_message,
            meta_data={}
        )
        db.add(user_msg)
        db.commit()
        
        # Obtém histórico para contexto
        history = ChatService.get_conversation_history(db, session_id)
        
        # Prepara estado inicial para workflow
        workflow_state = {
            "user_message": user_message,
            "conversation_history": [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history[-10:]
            ],
            "uploaded_file_path": uploaded_file_path or "",
            "uploaded_filename": uploaded_filename or "",
            "intent_analysis": {},
            "agent_response": "",
            "agent_name": "",
            "agent_data": {},
            "critic_review": {},
            "final_response": "",
            "status": "",
            "errors": []
        }
        
        # Executa workflow
        try:
            workflow = create_chat_workflow()
            result = workflow.invoke(workflow_state)
            
            # Salva resposta do assistente
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=result.get('final_response', 'Desculpe, não consegui processar sua mensagem.'),
                agent_used=result.get('agent_name', 'unknown'),
                reasoning=result.get('intent_analysis', {}).get('reasoning', ''),
                critic_analysis=result.get('critic_review', {}).get('analysis', ''),
                confidence_score=result.get('critic_review', {}).get('confidence', 0.0),
                meta_data={
                    "intent": result.get('intent_analysis', {}),
                    "critic_review": result.get('critic_review', {})
                }
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            
            return {
                "message_id": assistant_msg.id,
                "role": "assistant",
                "content": assistant_msg.content,
                "agent_used": assistant_msg.agent_used,
                "reasoning": assistant_msg.reasoning,
                "critic_analysis": assistant_msg.critic_analysis,
                "confidence_score": assistant_msg.confidence_score,
                "intent_analysis": result.get('intent_analysis', {}),
                "critic_review": result.get('critic_review', {}),
                "created_at": assistant_msg.created_at.isoformat()
            }
            
        except Exception as e:
            # Salva erro como resposta
            error_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=f"Desculpe, ocorreu um erro: {str(e)}",
                agent_used="error",
                meta_data={"error": str(e)}
            )
            db.add(error_msg)
            db.commit()
            
            return {
                "role": "assistant",
                "content": error_msg.content,
                "error": str(e)
            }
    
    @staticmethod
    def list_sessions(db: Session, user_id: str = "default", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Lista sessões de chat de um usuário
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            limit: Número máximo de sessões
            
        Returns:
            Lista de sessões
        """
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()
        
        return [
            {
                "id": s.id,
                "session_id": s.session_id,
                "title": s.title,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "message_count": len(s.messages)
            }
            for s in sessions
        ]
    
    @staticmethod
    def delete_session(db: Session, session_id: str) -> bool:
        """
        Deleta uma sessão de chat
        
        Args:
            db: Sessão do banco de dados
            session_id: ID da sessão
            
        Returns:
            True se deletado com sucesso
        """
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        
        return False
