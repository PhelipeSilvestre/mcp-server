from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable
from mcp.schemas.message import Message, ResponseMessage

class AgentBase(ABC):
    """Interface base para todos os agentes no sistema MCP."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.capabilities = self._register_capabilities()
        
    @abstractmethod
    def _register_capabilities(self) -> Dict[str, Callable[[Message], Awaitable[ResponseMessage]]]:
        """
        Registra as capacidades do agente.
        
        Returns:
            Dict[str, Callable]: Mapeamento de comandos para funções que os implementam
        """
        pass
        
    @abstractmethod
    async def process_message(self, message: Message) -> ResponseMessage:
        """
        Processa uma mensagem recebida.
        
        Args:
            message: Mensagem a ser processada
            
        Returns:
            ResponseMessage: Resposta do agente
        """
        pass
    
    @abstractmethod
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
        pass
        
    @abstractmethod
    async def handle_query(self, query: str, context: Dict[str, Any]) -> ResponseMessage:
        """
        Processa uma consulta/pergunta.
        
        Args:
            query: Consulta/pergunta
            context: Contexto da execução
            
        Returns:
            ResponseMessage: Resposta à consulta
        """
        pass