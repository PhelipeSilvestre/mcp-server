from fastapi import FastAPI, Request
from agents.estudos import controller as estudos_controller
from core.dispatcher import processar_update

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao MCP Server! Use as rotas /estudos para acessar as funcionalidades."}

# Endpoint para receber atualizações do bot do Telegram
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    update_json = await request.json()
    processar_update(update_json)
    return {"status": "ok"}

# Rotas dos agentes
app.include_router(estudos_controller.router, prefix="/estudos")