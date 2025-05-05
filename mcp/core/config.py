import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações básicas do MCP
MCP_CONFIG = {
    "version": "1.0.0",
    "name": "MCP Server",
    "adapters": ["telegram", "webhook"],
    "active_agents": ["estudos"],
    "default_model": "gemini"
}

# Tokens e chaves de API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_KEY = os.getenv("NOTION_KEY")

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTADOS_DIR = os.path.join(BASE_DIR, "estados")

# Garantir que os diretórios necessários existam
if not os.path.exists(ESTADOS_DIR):
    os.makedirs(ESTADOS_DIR)

def get_adapter_config(adapter_name: str) -> Dict[str, Any]:
    """Retorna a configuração específica para um adaptador"""
    configs = {
        "telegram": {
            "token": TELEGRAM_TOKEN,
            "webhook_path": "/webhook/telegram"
        },
        "webhook": {
            "paths": {
                "n8n": "/webhook/n8n",
                "custom": "/webhook/custom"
            }
        }
    }
    return configs.get(adapter_name, {})