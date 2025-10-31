"""
Critic Agent - Valida e analisa criticamente outputs antes de enviar ao usuário
"""
import os
import json
from typing import Dict, Any
from groq import Groq


class CriticAgent:
    """
    Agente crítico que valida outputs de outros agentes antes de devolver ao usuário
    Garante qualidade, completude e acurácia das respostas
    """
    
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        self.is_available = bool(api_key)
        
        if not self.is_available:
            print("⚠️ GROQ_API_KEY não configurada. Crítico funcionará em modo degradado.")
            self.client = None
            self.model = None
        else:
            self.client = Groq(api_key=api_key)
            self.model = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    def review_output(self, 
                     user_question: str,
                     agent_response: str,
                     agent_name: str,
                     agent_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Revisa criticamente o output de um agente
        
        Args:
            user_question: Pergunta original do usuário
            agent_response: Resposta gerada pelo agente
            agent_name: Nome do agente que gerou a resposta
            agent_data: Dados adicionais do processamento
            
        Returns:
            Dict com análise crítica e recomendações
        """
        
        # Fallback se Groq não disponível - aprova tudo em modo degradado
        if not self.is_available or not self.client:
            return {
                "quality_score": 75,
                "approved": True,
                "strengths": ["Resposta gerada"],
                "weaknesses": ["Modo degradado - revisão automática não disponível"],
                "recommendations": ["Configure GROQ_API_KEY para análise crítica completa"],
                "confidence": 0.5,
                "analysis": "Aprovado automaticamente em modo degradado"
            }
        
        system_prompt = """Você é um revisor crítico especializado em validar outputs de sistemas de IA.

CRITÉRIOS DE AVALIAÇÃO:
1. COMPLETUDE: A resposta responde completamente a pergunta?
2. ACURÁCIA: Os dados estão corretos e consistentes?
3. CLAREZA: A resposta é clara e fácil de entender?
4. UTILIDADE: A resposta é útil para o usuário?
5. SEGURANÇA: Não expõe dados sensíveis indevidamente?

TAREFA:
Analise criticamente a resposta e forneça:
1. Score de qualidade (0-100)
2. Pontos fortes
3. Pontos fracos
4. Recomendações de melhoria
5. Se a resposta deve ser aprovada ou reprocessada

Responda APENAS com JSON no formato:
{
    "quality_score": 85,
    "approved": true,
    "strengths": ["ponto forte 1", "ponto forte 2"],
    "weaknesses": ["ponto fraco 1"],
    "recommendations": ["melhoria sugerida"],
    "confidence": 0.9,
    "analysis": "análise detalhada em 1-2 frases"
}
"""

        # Prepara contexto
        context = f"""AGENTE: {agent_name}

PERGUNTA DO USUÁRIO:
{user_question}

RESPOSTA DO AGENTE:
{agent_response}
"""

        if agent_data:
            context += f"\n\nDADOS ADICIONAIS:\n{json.dumps(agent_data, indent=2, ensure_ascii=False)[:500]}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extrai JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            review = json.loads(content)
            
            # Validação básica
            if "quality_score" not in review:
                review["quality_score"] = 70
            if "approved" not in review:
                review["approved"] = review.get("quality_score", 70) >= 60
            
            return review
            
        except Exception as e:
            print(f"Erro na análise crítica: {e}")
            return {
                "quality_score": 50,
                "approved": True,
                "strengths": [],
                "weaknesses": [f"Erro na validação: {str(e)}"],
                "recommendations": ["Revisar manualmente"],
                "confidence": 0.3,
                "analysis": "Não foi possível validar adequadamente a resposta"
            }
    
    def improve_response(self, 
                        original_response: str,
                        review: Dict[str, Any],
                        user_question: str) -> str:
        """
        Melhora uma resposta com base na análise crítica
        
        Args:
            original_response: Resposta original
            review: Análise crítica
            user_question: Pergunta do usuário
            
        Returns:
            Resposta melhorada
        """
        
        if review.get("approved", False) and review.get("quality_score", 0) >= 80:
            return original_response
        
        system_prompt = """Você é um editor especializado em melhorar respostas de sistemas de IA.

Sua tarefa é refinar a resposta com base nas recomendações do revisor,
mantendo a acurácia dos dados mas melhorando clareza e completude."""

        user_prompt = f"""PERGUNTA DO USUÁRIO:
{user_question}

RESPOSTA ORIGINAL:
{original_response}

ANÁLISE DO REVISOR:
- Pontos fracos: {', '.join(review.get('weaknesses', []))}
- Recomendações: {', '.join(review.get('recommendations', []))}

Melhore a resposta mantendo a acurácia mas aplicando as recomendações:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            improved = response.choices[0].message.content.strip()
            return improved if improved else original_response
            
        except Exception as e:
            print(f"Erro ao melhorar resposta: {e}")
            return original_response
