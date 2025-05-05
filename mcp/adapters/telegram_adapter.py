import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
import json

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters
)

from mcp.schemas.adapter import AdapterBase
from mcp.schemas.message import Message, ResponseMessage, MessageType, QueryMessage, CommandMessage
from mcp.core.config import get_adapter_config

logger = logging.getLogger(__name__)

class TelegramAdapter(AdapterBase):
    """
    Adaptador para integração com a API do Telegram.
    Converte mensagens do Telegram para o formato MCP e vice-versa.
    """
    
    def __init__(self):
        config = get_adapter_config("telegram")
        super().__init__("telegram", config)
        self.token = config.get("token")
        self.webhook_path = config.get("webhook_path", "/webhook/telegram")
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
    async def initialize(self) -> None:
        """Inicializa o bot do Telegram."""
        if not self.token:
            logger.error("Token do Telegram não configurado")
            return
            
        try:
            # Inicializar o bot
            self.bot = Bot(token=self.token)
            logger.info(f"Bot do Telegram inicializado: @{(await self.bot.get_me()).username}")
            
            # Configuração da aplicação (apenas se estivermos rodando em modo polling)
            self.application = Application.builder().token(self.token).build()
            
            # Adicionar handlers para comandos
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("resumo", self._handle_resumo))
            self.application.add_handler(CommandHandler("quiz", self._handle_quiz))
            self.application.add_handler(CommandHandler("responder", self._handle_responder))
            
            # Handler para mensagens não reconhecidas
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
        except Exception as e:
            logger.exception(f"Erro ao inicializar o bot do Telegram: {e}")
    
    async def shutdown(self) -> None:
        """Desliga o bot do Telegram."""
        if self.application:
            self.application.shutdown()
            logger.info("Bot do Telegram encerrado.")
    
    async def send_message(self, message: ResponseMessage) -> None:
        """
        Envia uma mensagem de resposta para o Telegram.
        
        Args:
            message: Mensagem de resposta no formato MCP
        """
        if not self.bot:
            logger.error("Bot do Telegram não inicializado")
            return
            
        try:
            # Extrair o chat_id do contexto da mensagem
            chat_id = message.context.get("chat_id")
            if not chat_id:
                logger.error(f"chat_id não encontrado na mensagem: {message.id}")
                return
                
            # Extrai o conteúdo da mensagem
            if isinstance(message.data, dict):
                if "quiz" in message.data:
                    await self._send_quiz(chat_id, message.data["quiz"])
                elif "resumo" in message.data:
                    await self.bot.send_message(chat_id=chat_id, text=message.data["resumo"])
                elif "error" in message.data:
                    await self.bot.send_message(chat_id=chat_id, text=f"Erro: {message.data['error']}")
                else:
                    # Mensagem genérica
                    text = message.data.get("text", json.dumps(message.data))
                    await self.bot.send_message(chat_id=chat_id, text=text)
            elif isinstance(message.data, str):
                await self.bot.send_message(chat_id=chat_id, text=message.data)
            else:
                await self.bot.send_message(
                    chat_id=chat_id, 
                    text=f"Resposta: {str(message.data)}"
                )
                
        except Exception as e:
            logger.exception(f"Erro ao enviar mensagem para o Telegram: {e}")
    
    async def handle_external_input(self, update_json: Dict[str, Any]) -> Message:
        """
        Converte uma atualização do Telegram em uma mensagem MCP.
        
        Args:
            update_json: Objeto JSON da atualização do Telegram
            
        Returns:
            Message: Mensagem no formato MCP
        """
        # Criar um objeto Update
        update = Update.de_json(update_json, self.bot)
        
        if not update.message:
            # Tratar outros tipos de atualizações futuramente
            return self._create_error_message("Tipo de atualização não suportado")
            
        text = update.message.text
        usuario_id = str(update.effective_user.id)
        chat_id = update.effective_chat.id
        
        # Adicionar contexto comum
        context = {
            "chat_id": chat_id,
            "user_id": usuario_id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name
        }
        
        # Determinar o tipo de mensagem com base no texto
        if text.startswith('/'):
            # É um comando
            parts = text.split(' ', 1)
            command = parts[0][1:]  # Remove a barra
            params = parts[1] if len(parts) > 1 else ""
            
            # Mapear comandos específicos
            if command == "start":
                return CommandMessage(
                    id=str(uuid.uuid4()),
                    source=self.adapter_id,
                    target="estudos",  # Fixo por enquanto
                    content={"command": "start", "params": {}},
                    user_id=usuario_id,
                    context=context,
                    command="start",
                    parameters={}
                )
            elif command == "resumo":
                return CommandMessage(
                    id=str(uuid.uuid4()),
                    source=self.adapter_id,
                    target="estudos",
                    content={"command": "resumo", "params": {"topico": params}},
                    user_id=usuario_id,
                    context=context,
                    command="resumo",
                    parameters={"topico": params}
                )
            elif command == "quiz":
                return CommandMessage(
                    id=str(uuid.uuid4()),
                    source=self.adapter_id,
                    target="estudos",
                    content={"command": "quiz", "params": {"topico": params}},
                    user_id=usuario_id,
                    context=context,
                    command="quiz",
                    parameters={"topico": params}
                )
            elif command == "responder":
                return CommandMessage(
                    id=str(uuid.uuid4()),
                    source=self.adapter_id,
                    target="estudos",
                    content={"command": "responder", "params": {"respostas": params}},
                    user_id=usuario_id,
                    context=context,
                    command="responder",
                    parameters={"respostas": params}
                )
            else:
                # Comando desconhecido
                return CommandMessage(
                    id=str(uuid.uuid4()),
                    source=self.adapter_id,
                    content={"command": command, "params": {"text": params}},
                    user_id=usuario_id,
                    context=context,
                    command=command,
                    parameters={"text": params}
                )
        else:
            # Mensagem de texto comum
            return QueryMessage(
                id=str(uuid.uuid4()),
                source=self.adapter_id,
                content={"text": text},
                user_id=usuario_id,
                context=context,
                query=text
            )
    
    def _create_error_message(self, error_text: str) -> Message:
        """Cria uma mensagem de erro MCP."""
        return Message(
            id=str(uuid.uuid4()),
            type=MessageType.ERROR,
            source=self.adapter_id,
            content={"error": error_text},
            user_id=None
        )
    
    async def _handle_start(self, update: Update, context: CallbackContext) -> None:
        """Manipulador para o comando /start."""
        if self.message_handler:
            message = await self.handle_external_input(update.to_dict())
            await self.message_handler(message)
        else:
            await update.message.reply_text("Serviço em inicialização. Tente novamente mais tarde.")
    
    async def _handle_resumo(self, update: Update, context: CallbackContext) -> None:
        """Manipulador para o comando /resumo."""
        if self.message_handler:
            message = await self.handle_external_input(update.to_dict())
            await self.message_handler(message)
        else:
            await update.message.reply_text("Serviço em inicialização. Tente novamente mais tarde.")
    
    async def _handle_quiz(self, update: Update, context: CallbackContext) -> None:
        """Manipulador para o comando /quiz."""
        if self.message_handler:
            message = await self.handle_external_input(update.to_dict())
            await self.message_handler(message)
        else:
            await update.message.reply_text("Serviço em inicialização. Tente novamente mais tarde.")
    
    async def _handle_responder(self, update: Update, context: CallbackContext) -> None:
        """Manipulador para o comando /responder."""
        if self.message_handler:
            message = await self.handle_external_input(update.to_dict())
            await self.message_handler(message)
        else:
            await update.message.reply_text("Serviço em inicialização. Tente novamente mais tarde.")
    
    async def _handle_message(self, update: Update, context: CallbackContext) -> None:
        """Manipulador para mensagens de texto comuns."""
        if self.message_handler:
            message = await self.handle_external_input(update.to_dict())
            await self.message_handler(message)
        else:
            await update.message.reply_text("Serviço em inicialização. Tente novamente mais tarde.")
    
    async def _send_quiz(self, chat_id: int, quiz_data: list) -> None:
        """
        Envia um quiz formatado para o chat do Telegram.
        
        Args:
            chat_id: ID do chat
            quiz_data: Dados do quiz
        """
        if not self.bot:
            return
            
        # Formatar o quiz para exibição
        mensagem = "📝 *QUIZ* 📝\n\n"
        for i, pergunta in enumerate(quiz_data):
            mensagem += f"*Pergunta {i+1}*: {pergunta['pergunta']}\n\n"
            for j, opcao in enumerate(pergunta['opcoes']):
                mensagem += f"{chr(65+j)}) {opcao}\n"
            mensagem += "\n"
        
        mensagem += "Para responder, use /responder seguido das letras correspondentes às suas respostas (ex: /responder ABCDE)"
        
        # Enviar como markdown
        await self.bot.send_message(chat_id=chat_id, text=mensagem, parse_mode="Markdown")