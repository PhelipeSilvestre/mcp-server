from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class MessageType(str, Enum):
    """Tipos de mensagens no protocolo MCP."""
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    EVENT = "event"
    ERROR = "error"

class Message(BaseModel):
    """Modelo base para mensagens no protocolo MCP."""
    id: str = Field(..., description="ID único da mensagem")
    type: MessageType = Field(..., description="Tipo da mensagem")
    source: str = Field(..., description="Origem da mensagem (adapter ou agent)")
    target: Optional[str] = Field(None, description="Destino da mensagem (adapter ou agent)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da mensagem")
    content: Dict[str, Any] = Field(..., description="Conteúdo da mensagem")
    user_id: Optional[str] = Field(None, description="ID do usuário relacionado à mensagem")
    context: Dict[str, Any] = Field(default_factory=dict, description="Contexto adicional")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CommandMessage(Message):
    """Mensagem de comando para um agente."""
    type: MessageType = MessageType.COMMAND
    command: str = Field(..., description="Nome do comando a ser executado")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros do comando")

class QueryMessage(Message):
    """Mensagem de consulta para um agente."""
    type: MessageType = MessageType.QUERY
    query: str = Field(..., description="Consulta/pergunta para o agente")
    
class ResponseMessage(Message):
    """Mensagem de resposta de um agente."""
    type: MessageType = MessageType.RESPONSE
    response_to: str = Field(..., description="ID da mensagem original")
    success: bool = Field(..., description="Indicador de sucesso")
    data: Any = Field(..., description="Dados da resposta")
    
class ErrorMessage(Message):
    """Mensagem de erro."""
    type: MessageType = MessageType.ERROR
    error_code: str = Field(..., description="Código do erro")
    error_message: str = Field(..., description="Descrição do erro")
    original_message_id: Optional[str] = Field(None, description="ID da mensagem que causou o erro")