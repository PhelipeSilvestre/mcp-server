import logging
import uuid
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime

from mcp.schemas.agent import AgentBase
from mcp.schemas.message import Message, ResponseMessage, MessageType, CommandMessage, QueryMessage
from mcp.core.state_manager import StateManager
from mcp.models.gemini_provider import GeminiProvider, create_gemini_provider

logger = logging.getLogger(__name__)

class EstudosAgent(AgentBase):
    """
    Agente de estudos que gerencia a geração de resumos e quizzes
    sobre tópicos educacionais.
    """
    
    def __init__(self):
        super().__init__("estudos")
        self.model_provider = create_gemini_provider()
        if not self.model_provider:
            logger.error("Não foi possível inicializar o provider Gemini")
        
    def _register_capabilities(self) -> Dict[str, Callable[[Message], Awaitable[ResponseMessage]]]:
        """Registra as capacidades do agente de estudos."""
        return {
            "start": self._handle_start,
            "resumo": self._handle_resumo,
            "quiz": self._handle_quiz,
            "responder": self._handle_responder,
            "query": self._handle_query  # Para perguntas gerais
        }
    
    async def process_message(self, message: Message) -> ResponseMessage:
        """
        Processa mensagens recebidas.
        
        Args:
            message: Mensagem a ser processada
            
        Returns:
            ResponseMessage: Resposta do agente
        """
        try:
            if message.type == MessageType.COMMAND:
                if isinstance(message, CommandMessage):
                    command = message.command
                    params = message.parameters
                    context = message.context
                    
                    if command in self.capabilities:
                        return await self.capabilities[command](message)
                    else:
                        return await self._create_error_response(
                            message, 
                            f"Comando não suportado: {command}"
                        )
                else:
                    return await self._create_error_response(
                        message, 
                        "Mensagem de comando inválida"
                    )
                    
            elif message.type == MessageType.QUERY:
                if isinstance(message, QueryMessage):
                    return await self._handle_query(message)
                else:
                    return await self._create_error_response(
                        message, 
                        "Mensagem de consulta inválida"
                    )
            else:
                return await self._create_error_response(
                    message, 
                    f"Tipo de mensagem não suportado: {message.type}"
                )
                
        except Exception as e:
            logger.exception(f"Erro ao processar mensagem: {e}")
            return await self._create_error_response(
                message, 
                f"Erro ao processar mensagem: {str(e)}"
            )
    
    async def handle_command(self, command: str, params: Dict[str, Any], context: Dict[str, Any]) -> ResponseMessage:
        """
        Processa um comando específico.
        
        Args:
            command: Nome do comando
            params: Parâmetros do comando
            context: Contexto da execução
            
        Returns:
            ResponseMessage: Resposta do comando
        """
        # Criar uma mensagem de comando fictícia para reuso do código
        msg = CommandMessage(
            id=str(uuid.uuid4()),
            source=context.get('source', 'unknown'),
            command=command,
            parameters=params,
            content={"command": command, "params": params},
            context=context,
            user_id=context.get('user_id')
        )
        
        if command in self.capabilities:
            return await self.capabilities[command](msg)
        else:
            return await self._create_error_response(
                msg, 
                f"Comando não suportado: {command}"
            )
    
    async def handle_query(self, query: str, context: Dict[str, Any]) -> ResponseMessage:
        """
        Processa uma consulta/pergunta.
        
        Args:
            query: Consulta/pergunta
            context: Contexto da execução
            
        Returns:
            ResponseMessage: Resposta à consulta
        """
        # Criar uma mensagem de query fictícia para reuso do código
        msg = QueryMessage(
            id=str(uuid.uuid4()),
            source=context.get('source', 'unknown'),
            query=query,
            content={"text": query},
            context=context,
            user_id=context.get('user_id')
        )
        
        return await self._handle_query(msg)
    
    async def _handle_start(self, message: CommandMessage) -> ResponseMessage:
        """Manipulador para o comando start."""
        user_id = message.user_id
        
        # Salvar estado do usuário
        if user_id:
            StateManager.save_state(user_id, {"ultimo_comando": "start"})
        
        return await self._create_success_response(
            message,
            "Olá! Eu sou seu assistente de estudos. "\
            "Use /resumo <tópico> para gerar um resumo ou /quiz <tópico> para iniciar um quiz."
        )
    
    async def _handle_resumo(self, message: CommandMessage) -> ResponseMessage:
        """Manipulador para o comando resumo."""
        user_id = message.user_id
        topico = message.parameters.get("topico", "")
        
        if not topico:
            return await self._create_error_response(
                message,
                "Por favor, forneça um tópico. Exemplo: /resumo HTTP"
            )
        
        # Salvar o tópico no estado do usuário
        if user_id:
            StateManager.save_state(user_id, {"ultimo_topico": topico})
        
        if not self.model_provider:
            return await self._create_error_response(
                message,
                "Provedor de modelo não está disponível no momento."
            )
        
        try:
            resultado = await self.model_provider.generate_resume(topico)
            
            if not resultado.get("success", False):
                return await self._create_error_response(
                    message,
                    resultado.get("error", "Erro desconhecido ao gerar resumo")
                )
            
            return ResponseMessage(
                id=str(uuid.uuid4()),
                source=self.agent_id,
                target=message.source,
                content=resultado,
                user_id=user_id,
                context=message.context,
                response_to=message.id,
                success=True,
                data=resultado
            )
        except Exception as e:
            logger.exception(f"Erro ao gerar resumo: {e}")
            return await self._create_error_response(
                message,
                f"Erro ao gerar resumo: {str(e)}"
            )
    
    async def _handle_quiz(self, message: CommandMessage) -> ResponseMessage:
        """Manipulador para o comando quiz."""
        user_id = message.user_id
        topico = message.parameters.get("topico", "")
        
        # Se não foi fornecido um tópico, usar o último tópico usado pelo usuário
        if not topico and user_id:
            estado = StateManager.get_state(user_id)
            topico = estado.get("ultimo_topico", "geral")
        
        # Salvar o tópico no estado do usuário
        if user_id:
            StateManager.save_state(user_id, {"ultimo_topico": topico})
        
        if not self.model_provider:
            return await self._create_error_response(
                message,
                "Provedor de modelo não está disponível no momento."
            )
        
        try:
            resultado = await self.model_provider.generate_quiz(topico)
            
            if not resultado.get("success", False):
                return await self._create_error_response(
                    message,
                    resultado.get("error", "Erro desconhecido ao gerar quiz")
                )
            
            perguntas = resultado.get("quiz", [])
            
            if not perguntas:
                return await self._create_error_response(
                    message,
                    "Não foi possível gerar perguntas para o quiz."
                )
            
            # Salvar as perguntas no estado do usuário para referência futura
            if user_id:
                StateManager.save_state(user_id, {"quiz_atual": perguntas})
            
            return ResponseMessage(
                id=str(uuid.uuid4()),
                source=self.agent_id,
                target=message.source,
                content=resultado,
                user_id=user_id,
                context=message.context,
                response_to=message.id,
                success=True,
                data=resultado
            )
        except Exception as e:
            logger.exception(f"Erro ao gerar quiz: {e}")
            return await self._create_error_response(
                message,
                f"Erro ao gerar quiz: {str(e)}"
            )
    
    async def _handle_responder(self, message: CommandMessage) -> ResponseMessage:
        """Manipulador para o comando responder."""
        user_id = message.user_id
        respostas_texto = message.parameters.get("respostas", "")
        
        if not respostas_texto:
            return await self._create_error_response(
                message,
                "Por favor, forneça suas respostas. Exemplo: /responder ABCDE"
            )
        
        # Obter o quiz atual do usuário
        if not user_id:
            return await self._create_error_response(
                message,
                "Não foi possível identificar o usuário."
            )
            
        estado = StateManager.get_state(user_id)
        quiz_atual = estado.get("quiz_atual", [])
        
        if not quiz_atual:
            return await self._create_error_response(
                message,
                "Não há um quiz ativo. Gere um quiz primeiro com /quiz <tópico>."
            )
        
        # Converter as respostas em letras para índices (A=0, B=1, etc)
        respostas_usuario = []
        
        for letra in respostas_texto.upper():
            if 'A' <= letra <= 'D':
                respostas_usuario.append(ord(letra) - ord('A'))
            else:
                respostas_usuario.append(-1)  # Resposta inválida
        
        # Garantir que temos o mesmo número de respostas que perguntas
        while len(respostas_usuario) < len(quiz_atual):
            respostas_usuario.append(-1)
        
        # Limitar ao número de perguntas
        respostas_usuario = respostas_usuario[:len(quiz_atual)]
        
        # Obter respostas corretas
        respostas_certas = [pergunta['resposta_correta'] for pergunta in quiz_atual]
        
        # Avaliar as respostas
        resultado = self._avaliar_quiz(respostas_usuario, respostas_certas)
        
        # Limpar o quiz atual após a resposta
        StateManager.save_state(user_id, {"quiz_atual": None})
        
        return ResponseMessage(
            id=str(uuid.uuid4()),
            source=self.agent_id,
            target=message.source,
            content=resultado,
            user_id=user_id,
            context=message.context,
            response_to=message.id,
            success=True,
            data={
                "avaliacao": resultado,
                "texto": f"Você acertou {resultado['pontuacao']} de {resultado['total']} perguntas!"
            }
        )
    
    def _avaliar_quiz(self, respostas_usuario: List[int], respostas_certas: List[int]) -> Dict[str, Any]:
        """
        Avalia as respostas do usuário em um quiz.
        
        Args:
            respostas_usuario: Lista com os índices das respostas selecionadas pelo usuário
            respostas_certas: Lista com os índices das respostas corretas
            
        Returns:
            Dict[str, Any]: Dados da avaliação
        """
        # Contar respostas corretas
        acertos = 0
        detalhes = []
        
        for i, (user, correta) in enumerate(zip(respostas_usuario, respostas_certas)):
            acertou = user == correta
            if acertou:
                acertos += 1
                
            detalhes.append({
                "pergunta": i + 1,
                "resposta_usuario": chr(65 + user) if 0 <= user <= 25 else "?",
                "resposta_correta": chr(65 + correta) if 0 <= correta <= 25 else "?",
                "acertou": acertou
            })
            
        # Calcular porcentagem de acerto
        total = len(respostas_certas)
        porcentagem = int((acertos / total) * 100) if total > 0 else 0
        
        return {
            "pontuacao": acertos,
            "total": total,
            "porcentagem": porcentagem,
            "detalhes": detalhes
        }
    
    async def _handle_query(self, message: QueryMessage) -> ResponseMessage:
        """Manipulador para mensagens de pergunta gerais."""
        query = message.query
        
        if not self.model_provider:
            return await self._create_error_response(
                message,
                "Provedor de modelo não está disponível no momento."
            )
        
        # Por padrão, tratamos todas as queries como pedidos de resumo
        try:
            resultado = await self.model_provider.generate_resume(query)
            
            if not resultado.get("success", False):
                return await self._create_error_response(
                    message,
                    resultado.get("error", "Erro desconhecido ao processar consulta")
                )
            
            return ResponseMessage(
                id=str(uuid.uuid4()),
                source=self.agent_id,
                target=message.source,
                content=resultado,
                user_id=message.user_id,
                context=message.context,
                response_to=message.id,
                success=True,
                data=resultado
            )
        except Exception as e:
            logger.exception(f"Erro ao processar consulta: {e}")
            return await self._create_error_response(
                message,
                f"Não consegui processar sua pergunta: {str(e)}"
            )
    
    async def _create_success_response(self, original_message: Message, text: str) -> ResponseMessage:
        """Helper para criar mensagens de sucesso."""
        return ResponseMessage(
            id=str(uuid.uuid4()),
            source=self.agent_id,
            target=original_message.source,
            content={"text": text},
            user_id=original_message.user_id,
            context=original_message.context,
            response_to=original_message.id,
            success=True,
            data=text
        )
    
    async def _create_error_response(self, original_message: Message, error_text: str) -> ResponseMessage:
        """Helper para criar mensagens de erro."""
        return ResponseMessage(
            id=str(uuid.uuid4()),
            source=self.agent_id,
            target=original_message.source,
            content={"error": error_text},
            user_id=original_message.user_id,
            context=original_message.context,
            response_to=original_message.id,
            success=False,
            data={"error": error_text}
        )