import logging
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable

from mcp.schemas.adapter import AdapterBase
from mcp.schemas.message import Message, ResponseMessage, MessageType, CommandMessage
from mcp.core.config import get_adapter_config

logger = logging.getLogger(__name__)

class WebhookAdapter(AdapterBase):
    """
    Adaptador para integração com sistemas externos via webhooks.
    Converte payloads de webhook para o formato MCP e vice-versa.
    """
    
    def __init__(self):
        config = get_adapter_config("webhook")
        super().__init__("webhook", config)
        self.paths = config.get("paths", {})
        
    async def initialize(self) -> None:
        """Inicializa o adaptador."""
        logger.info(f"Adaptador de webhook inicializado com caminhos: {self.paths}")
        
    async def shutdown(self) -> None:
        """Desliga o adaptador."""
        logger.info("Adaptador de webhook encerrado.")
    
    async def send_message(self, message: ResponseMessage) -> None:
        """
        Envia uma mensagem de resposta para o webhook.
        
        Args:
            message: Mensagem de resposta no formato MCP
        """
        # O comportamento padrão do webhook é não enviar nada de volta
        # as respostas já são tratadas pelo FastAPI no endpoint
        pass
    
    async def handle_external_input(self, input_data: Dict[str, Any]) -> Message:
        """
        Converte uma entrada de webhook em uma mensagem MCP.
        
        Args:
            input_data: Dados recebidos do webhook
            
        Returns:
            Message: Mensagem no formato MCP
        """
        source = input_data.get("source", "webhook")
        
        # Se for um webhook do n8n
        if source == "n8n":
            return await self._handle_n8n_input(input_data)
        
        # Webhook genérico
        return CommandMessage(
            id=str(uuid.uuid4()),
            source=self.adapter_id,
            content=input_data,
            user_id=input_data.get("user_id"),
            command=input_data.get("command", "process"),
            parameters=input_data,
            context={"webhook_source": source}
        )
    
    async def _handle_n8n_input(self, data: Dict[str, Any]) -> Message:
        """
        Processa uma entrada específica do n8n.
        
        Args:
            data: Dados recebidos do n8n
            
        Returns:
            Message: Mensagem MCP padronizada
        """
        acao = data.get("acao")
        
        if acao == "resumo":
            return CommandMessage(
                id=str(uuid.uuid4()),
                source=self.adapter_id,
                target="estudos",  # Agente de destino
                content=data,
                user_id=data.get("user_id"),
                command="resumo",
                parameters={"topico": data.get("topico", "")},
                context={"webhook_source": "n8n"}
            )
        elif acao == "quiz":
            return CommandMessage(
                id=str(uuid.uuid4()),
                source=self.adapter_id,
                target="estudos",  # Agente de destino
                content=data,
                user_id=data.get("user_id"),
                command="quiz",
                parameters={"topico": data.get("topico", "")},
                context={"webhook_source": "n8n"}
            )
        else:
            # Ação desconhecida
            return CommandMessage(
                id=str(uuid.uuid4()),
                source=self.adapter_id,
                content={"error": "Ação desconhecida"},
                user_id=data.get("user_id"),
                command="unknown",
                parameters=data,
                context={"webhook_source": "n8n", "error": "acao_desconhecida"}
            )