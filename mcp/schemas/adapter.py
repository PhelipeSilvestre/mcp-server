from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable
from mcp.schemas.message import Message, ResponseMessage

class AdapterBase(ABC):
    """Interface base para todos os adaptadores no sistema MCP."""
    
    def __init__(self, adapter_id: str, config: Dict[str, Any]):
        self.adapter_id = adapter_id
        self.config = config
        self.message_handler: Optional[Callable[[Message], Awaitable[None]]] = None
        
    def register_message_handler(self, handler: Callable[[Message], Awaitable[None]]) -> None:
        """
        Registra o manipulador de mensagens central para processar mensagens deste adaptador.
        
        Args:
            handler: Função de callback para processar mensagens
        """
        self.message_handler = handler
        
    @abstractmethod
    async def initialize(self) -> None:
        """Inicializa o adaptador."""
        pass
        
    @abstractmethod
    async def shutdown(self) -> None:
        """Desliga o adaptador."""
        pass
        
    @abstractmethod
    async def send_message(self, message: ResponseMessage) -> None:
        """
        Envia uma mensagem através deste adaptador.
        
        Args:
            message: Mensagem a ser enviada
        """
        pass
        
    @abstractmethod
    async def handle_external_input(self, input_data: Any) -> Message:
        """
        Converte uma entrada externa no formato da plataforma para uma mensagem MCP.
        
        Args:
            input_data: Dados recebidos da plataforma/sistema externo
            
        Returns:
            Message: Mensagem MCP padronizada
        """
        pass