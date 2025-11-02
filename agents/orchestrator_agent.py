"""
Chat Orchestrator Agent - Analisa intenção e roteia para agentes especializados
"""
import os
import json
from typing import Dict, Any, List
from groq import Groq


class ChatOrchestratorAgent:
    """
    Agente orquestrador que analisa a pergunta do usuário
    e decide qual(is) agente(s) especializado(s) acionar
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        self.is_available = bool(api_key)
        
        if not self.is_available:
            print("⚠️ GROQ_API_KEY não configurada. Chat funcionará em modo degradado.")
            self.client = None
            self.model = None
        else:
            self.client = Groq(api_key=api_key)
            self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
        
        self.available_agents = {
            "document_processor": {
                "description": "Processa documentos fiscais (NFe, NFCe, SAT, CTe, NFSe) - extrai dados estruturados",
                "capabilities": ["processar nfe", "extrair dados", "classificar documento", "ler xml", "ler pdf", "fazer upload"]
            },
            "data_query": {
                "description": "Consulta dados de documentos JÁ PROCESSADOS no banco de dados - use para perguntas sobre dados EXISTENTES",
                "capabilities": [
                    "quantos documentos", "total de documentos", "estatísticas",
                    "quanto de impostos", "total de impostos", "impostos pagos",
                    "qual o valor total", "valor total processado", "soma dos valores",
                    "buscar documentos", "consultar histórico", "filtrar por cnpj", 
                    "listar notas", "documentos recentes", "últimas notas"
                ]
            },
            "analysis": {
                "description": "Analisa dados fiscais, calcula totais, impostos, tendências",
                "capabilities": ["calcular impostos", "análise financeira", "comparar valores", "tendências", "insights"]
            },
            "general": {
                "description": "Responde perguntas gerais sobre o sistema, como funciona, ajuda",
                "capabilities": ["ajuda", "como funciona", "explicar", "o que é", "para que serve"]
            },
            "out_of_scope": {
                "description": "Perguntas fora do escopo do sistema de notas fiscais - deve ser rejeitado educadamente",
                "capabilities": []
            }
        }
        
        # Define escopo permitido
        self.project_scope = {
            "topics_in_scope": [
                "notas fiscais brasileiras (NFe, NFCe, SAT, CTe, NFSe)",
                "documentos fiscais eletrônicos",
                "extração de dados de documentos fiscais",
                "impostos e tributação brasileira (ICMS, PIS, COFINS, IPI, etc)",
                "SEFAZ (Secretaria da Fazenda)",
                "certificados digitais A1",
                "manifesto eletrônico",
                "validação de CNPJ e CPF",
                "chaves de acesso de NFe",
                "análise de dados fiscais",
                "funcionalidades do sistema de processamento",
                "como usar o sistema",
                "upload de documentos",
                "consultas ao banco de dados de notas processadas"
            ],
            "topics_out_of_scope": [
                "receitas culinárias",
                "esportes e jogos",
                "entretenimento, filmes, séries",
                "notícias gerais",
                "política",
                "matemática geral não relacionada a impostos",
                "programação geral não relacionada ao sistema",
                "assuntos pessoais",
                "qualquer tópico não relacionado a documentos fiscais brasileiros"
            ]
        }
    
    def analyze_intent(self, user_message: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Analisa a intenção do usuário e decide qual agente usar
        
        Args:
            user_message: Mensagem do usuário
            conversation_history: Histórico da conversa (opcional)
            
        Returns:
            Dict com agente selecionado, confiança e raciocínio
        """
        
        # Fallback se Groq não disponível
        if not self.is_available or not self.client:
            return {
                "agent": "general",
                "confidence": 0.5,
                "reasoning": "Modo degradado - GROQ_API_KEY não configurada",
                "requires_file": False,
                "parameters": {}
            }
        
        # Monta contexto da conversa
        context = ""
        if conversation_history and len(conversation_history) > 0:
            recent_messages = conversation_history[-6:]
            context = "\n".join([
                f"{msg['role']}: {msg['content'][:200]}" 
                for msg in recent_messages
            ])
        
        # Prompt para análise de intenção
        system_prompt = f"""Você é um assistente especializado em analisar intenções de usuários de um sistema de processamento de notas fiscais brasileiras.

**REGRA CRÍTICA DE VALIDAÇÃO DE ESCOPO:**
Você deve PRIMEIRO verificar se a pergunta está relacionada ao escopo do projeto. 
Se a pergunta for sobre tópicos NÃO relacionados a documentos fiscais brasileiros, retorne agent="out_of_scope".

TÓPICOS DENTRO DO ESCOPO (ACEITOS):
{json.dumps(self.project_scope['topics_in_scope'], indent=2, ensure_ascii=False)}

TÓPICOS FORA DO ESCOPO (REJEITADOS):
{json.dumps(self.project_scope['topics_out_of_scope'], indent=2, ensure_ascii=False)}

AGENTES DISPONÍVEIS:
{json.dumps(self.available_agents, indent=2, ensure_ascii=False)}

TAREFA:
1. **PRIMEIRO**: Verifique se a pergunta está no escopo do projeto
   - Se NÃO estiver relacionada a notas fiscais/documentos fiscais brasileiros → retorne "out_of_scope"
   - Se ESTIVER relacionada → prossiga para o passo 2

2. **SEGUNDO**: Analise qual agente específico deve ser acionado
3. Determine o nível de confiança (0-1)
4. Explique o raciocínio
5. Verifique se precisa de upload de arquivo

Responda APENAS com JSON no formato:
{{
    "agent": "nome_do_agente",
    "confidence": 0.95,
    "reasoning": "explicação clara",
    "requires_file": true/false,
    "parameters": {{"qualquer": "parametro relevante"}}
}}
"""

        user_prompt = f"""CONTEXTO DA CONVERSA:
{context if context else "Primeira mensagem da conversa"}

MENSAGEM DO USUÁRIO:
{user_message}

Analise e retorne o JSON de decisão:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extrai JSON da resposta
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(content)
            
            # Validação - aceita agentes disponíveis ou out_of_scope
            if decision.get("agent") not in self.available_agents:
                decision["agent"] = "general"
                decision["confidence"] = 0.5
                decision["reasoning"] = "Não foi possível determinar agente específico"
            
            return decision
            
        except Exception as e:
            print(f"Erro ao analisar intenção: {e}")
            return {
                "agent": "general",
                "confidence": 0.3,
                "reasoning": f"Erro na análise: {str(e)}",
                "requires_file": False,
                "parameters": {}
            }
    
    def generate_response(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """
        Gera resposta para perguntas gerais (quando agent='general')
        
        Args:
            user_message: Mensagem do usuário
            context: Contexto adicional (opcional)
            
        Returns:
            Resposta gerada
        """
        
        # Fallback se Groq não disponível
        if not self.is_available or not self.client:
            return """Olá! Sou o assistente do sistema de extração de dados de notas fiscais brasileiras.

**Funcionalidades disponíveis:**
- Processar documentos fiscais (NFe, NFCe, SAT, CTe, NFSe)
- Extrair dados estruturados automaticamente
- Validar CNPJ, CPF, chaves de acesso
- Dashboard com análises e gráficos
- Integração com SEFAZ
- Processamento em lote

Para processar um documento, faça upload na página correspondente."""
        
        system_prompt = """Você é um assistente prestativo de um sistema de extração de dados de notas fiscais brasileiras.

FUNCIONALIDADES DO SISTEMA:
- Processar documentos fiscais (NFe, NFCe, SAT, CTe, NFSe) em XML, PDF ou imagem
- Extrair dados estruturados automaticamente usando IA
- Validar CNPJ, CPF, chaves de acesso
- Armazenar histórico de documentos processados
- Dashboard com análises e gráficos
- Integração com SEFAZ para download automático
- Processamento em lote

Responda de forma clara, concisa e útil. Se o usuário quiser processar um documento, instrua a fazer upload."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
