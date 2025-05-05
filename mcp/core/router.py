import asyncio
import uuid
from typing import Dict, Any, List, Optional, Set
import logging
from datetime import datetime

from mcp.schemas.message import Message, ResponseMessage, ErrorMessage, MessageType
from mcp.schemas.agent import AgentBase
from mcp.schemas.adapter import AdapterBase

logger = logging.getLogger(__name__)

class MCPRouter:
    """
    Componente central do MCP que gerencia o roteamento de mensagens 
    entre adaptadores e agentes.
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentBase] = {}
        self.adapters: Dict[str, AdapterBase] = {}
        self.running_tasks: Set[asyncio.Task] = set()
        
    def register_agent(self, agent: AgentBase) -> None:
        """
        Registra um agente no router.
        
        Args:
            agent: O agente a ser registrado
        """
        logger.info(f"Registrando agente: {agent.agent_id}")
        self.agents[agent.agent_id] = agent
        
    def register_adapter(self, adapter: AdapterBase) -> None:
        """
        Registra um adaptador no router.
        
        Args:
            adapter: O adaptador a ser registrado
        """
        logger.info(f"Registrando adaptador: {adapter.adapter_id}")
        adapter.register_message_handler(self.handle_message)
        self.adapters[adapter.adapter_id] = adapter
        
    def get_agent(self, agent_id: str) -> Optional[AgentBase]:
        """
        Obtém um agente pelo ID.
        
        Args:
            agent_id: ID do agente
            
        Returns:
            O agente ou None se não encontrado
        """
        return self.agents.get(agent_id)
    
    def get_adapter(self, adapter_id: str) -> Optional[AdapterBase]:
        """
        Obtém um adaptador pelo ID.
        
        Args:
            adapter_id: ID do adaptador
            
        Returns:
            O adaptador ou None se não encontrado
        """
        return self.adapters.get(adapter_id)
    
    async def initialize(self) -> None:
        """Inicializa todos os adaptadores registrados."""
        logger.info("Inicializando todos os adaptadores")
        init_tasks = [adapter.initialize() for adapter in self.adapters.values()]
        await asyncio.gather(*init_tasks)
        
    async def shutdown(self) -> None:
        """Desliga todos os adaptadores registrados."""
        logger.info("Desligando todos os adaptadores")
        shutdown_tasks = [adapter.shutdown() for adapter in self.adapters.values()]
        await asyncio.gather(*shutdown_tasks)
        
    async def handle_message(self, message: Message) -> None:
        """
        Processa uma mensagem recebida e a encaminha para o destino correto.
        
        Args:
            message: A mensagem a ser processada
        """
        try:
            logger.debug(f"Processando mensagem: {message.id} de {message.source} para {message.target}")
            
            # Se a mensagem já tem um destino específico
            if message.target and message.target in self.agents:
                agent = self.agents[message.target]
                task = asyncio.create_task(self._process_with_agent(agent, message))
                self.running_tasks.add(task)
                task.add_done_callback(self.running_tasks.discard)
                return
            
            # Se não tem destino, temos que determinar a qual agente enviar
            # com base no tipo e conteúdo da mensagem
            if message.type == MessageType.COMMAND or message.type == MessageType.QUERY:
                # Lógica para determinar o agente apropriado
                # Por enquanto, simplesmente usamos o primeiro registrado se não conseguirmos determinar
                agent_id = self._determine_agent_for_message(message)
                if agent_id and agent_id in self.agents:
                    agent = self.agents[agent_id]
                    task = asyncio.create_task(self._process_with_agent(agent, message))
                    self.running_tasks.add(task)
                    task.add_done_callback(self.running_tasks.discard)
                else:
                    error_msg = f"Não foi possível determinar um agente para a mensagem {message.id}"
                    logger.error(error_msg)
                    await self._handle_error(message, "AGENT_DETERMINATION_ERROR", error_msg)
            else:
                error_msg = f"Tipo de mensagem não suportado para roteamento automático: {message.type}"
                logger.error(error_msg)
                await self._handle_error(message, "UNSUPPORTED_MESSAGE_TYPE", error_msg)
                
        except Exception as e:
            error_msg = f"Erro ao processar mensagem: {str(e)}"
            logger.exception(error_msg)
            await self._handle_error(message, "PROCESSING_ERROR", error_msg)
    
    def _determine_agent_for_message(self, message: Message) -> Optional[str]:
        """
        Determina qual agente deve processar a mensagem com base no seu conteúdo.
        
        Args:
            message: A mensagem a ser processada
            
        Returns:
            O ID do agente mais apropriado ou None
        """
        # Implementação simples: atualmente só temos o agente de estudos
        # Futuramente esta lógica pode usar NLP ou regras mais sofisticadas
        return "estudos"
    
    async def _process_with_agent(self, agent: AgentBase, message: Message) -> None:
        """
        Processa uma mensagem com um agente específico.
        
        Args:
            agent: O agente a processar a mensagem
            message: A mensagem a ser processada
        """
        try:
            response = await agent.process_message(message)
            
            # Se a mensagem veio de um adaptador, enviar a resposta de volta
            if message.source in self.adapters:
                adapter = self.adapters[message.source]
                await adapter.send_message(response)
                
        except Exception as e:
            error_msg = f"Erro no agente {agent.agent_id}: {str(e)}"
            logger.exception(error_msg)
            await self._handle_error(message, "AGENT_PROCESSING_ERROR", error_msg)
    
    async def _handle_error(self, original_message: Message, error_code: str, error_message: str) -> None:
        """
        Cria e envia uma mensagem de erro.
        
        Args:
            original_message: A mensagem que causou o erro
            error_code: Código do erro
            error_message: Descrição do erro
        """
        error = ErrorMessage(
            id=str(uuid.uuid4()),
            source="mcp.router",
            target=original_message.source,
            content={"error": error_message},
            error_code=error_code,
            error_message=error_message,
            original_message_id=original_message.id,
            user_id=original_message.user_id
        )
        
        # Enviar mensagem de erro para o adaptador de origem
        if original_message.source in self.adapters:
            adapter = self.adapters[original_message.source]
            await adapter.send_message(error)