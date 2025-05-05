import asyncio
import logging
import os
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from mcp.core.router import MCPRouter
from mcp.adapters.telegram_adapter import TelegramAdapter
from mcp.adapters.webhook_adapter import WebhookAdapter
from mcp.agents.estudos_agent import EstudosAgent
from mcp.agents.estudos_controller import router as estudos_router
from mcp.core.config import TELEGRAM_TOKEN

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server")

# Criar aplicação FastAPI
app = FastAPI(
    title="MCP Server",
    description="Servidor MCP (Model Context Protocol) para integração de agentes e adaptadores",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, limite isto aos domínios necessários
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criar o router MCP central
router = MCPRouter()

# Incluir rotas específicas de agentes
app.include_router(estudos_router, prefix="/estudos", tags=["estudos"])

# Endpoint para verificar status do servidor
@app.get("/")
async def read_root():
    """Endpoint raiz para verificar status do servidor."""
    return {
        "status": "online",
        "message": "MCP Server está ativo",
        "version": "1.0.0"
    }

# Endpoint para webhook do Telegram
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Endpoint para receber webhooks do Telegram."""
    try:
        # Obter o JSON do webhook
        update_json = await request.json()
        
        # Obter adaptador do Telegram
        adapter = router.get_adapter("telegram")
        if not adapter:
            logger.error("Adaptador do Telegram não está registrado")
            return {"status": "error", "message": "Telegram adapter not registered"}
        
        # Processar atualização
        message = await adapter.handle_external_input(update_json)
        if router.handle_message:
            # Criar uma tarefa assíncrona para processar a mensagem
            asyncio.create_task(router.handle_message(message))
        
        return {"status": "ok"}
    except Exception as e:
        logger.exception(f"Erro ao processar webhook do Telegram: {e}")
        return {"status": "error", "message": str(e)}

# Endpoint para webhook do n8n
@app.post("/webhook/n8n")
async def n8n_webhook(request: Request):
    """Endpoint para receber webhooks do n8n."""
    try:
        # Obter o JSON do webhook
        payload = await request.json()
        payload["source"] = "n8n"  # Adicionar origem para identificação
        
        # Obter adaptador de webhook
        adapter = router.get_adapter("webhook")
        if not adapter:
            logger.error("Adaptador de webhook não está registrado")
            return {"status": "error", "message": "Webhook adapter not registered"}
        
        # Processar payload
        message = await adapter.handle_external_input(payload)
        if router.handle_message:
            response_message = await router.handle_message(message)
            return response_message.data
        
        return {"status": "error", "message": "Message handler not available"}
    except Exception as e:
        logger.exception(f"Erro ao processar webhook do n8n: {e}")
        return {"status": "error", "message": str(e)}

# Função para inicializar o servidor MCP
async def initialize_mcp():
    """Inicializa o servidor MCP com seus adaptadores e agentes."""
    logger.info("Inicializando o servidor MCP...")
    
    # Registrar adaptadores
    telegram_adapter = TelegramAdapter()
    router.register_adapter(telegram_adapter)
    
    webhook_adapter = WebhookAdapter()
    router.register_adapter(webhook_adapter)
    
    # Registrar agentes
    estudos_agent = EstudosAgent()
    router.register_agent(estudos_agent)
    
    # Inicializar adaptadores
    await router.initialize()
    
    logger.info("Servidor MCP inicializado com sucesso!")
    
    return router

# Evento de inicialização do FastAPI
@app.on_event("startup")
async def startup_event():
    """Evento executado quando o servidor FastAPI inicia."""
    app.state.router = await initialize_mcp()
    logger.info("Servidor FastAPI iniciado com MCP configurado")

# Evento de encerramento do FastAPI
@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado quando o servidor FastAPI é encerrado."""
    if hasattr(app.state, "router"):
        await app.state.router.shutdown()
    logger.info("Servidor FastAPI encerrado")

# Configuração para rodar com uvicorn
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=port, reload=True)