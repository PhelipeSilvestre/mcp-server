import json
import os
from datetime import datetime

# Diretório para armazenar os estados dos usuários
ESTADOS_DIR = "estados"

# Garantir que o diretório existe
if not os.path.exists(ESTADOS_DIR):
    os.makedirs(ESTADOS_DIR)

def salvar_estado(usuario_id, dados):
    """
    Salva o estado do usuário em um arquivo JSON.
    
    Args:
        usuario_id (str): ID único do usuário
        dados (dict): Dados a serem salvos
    """
    # Garantir que temos o ID em formato string
    usuario_id = str(usuario_id)
    
    # Caminho do arquivo para este usuário
    arquivo = os.path.join(ESTADOS_DIR, f"{usuario_id}.json")
    
    # Carregar dados existentes, se houver
    estado_atual = recuperar_estado(usuario_id)
    
    # Atualizar com novos dados
    estado_atual.update(dados)
    
    # Adicionar timestamp da última atualização
    estado_atual["ultima_atualizacao"] = datetime.now().isoformat()
    
    # Salvar no arquivo
    with open(arquivo, 'w') as f:
        json.dump(estado_atual, f, indent=2)

def recuperar_estado(usuario_id):
    """
    Recupera o estado do usuário.
    
    Args:
        usuario_id (str): ID único do usuário
        
    Returns:
        dict: Estado atual do usuário ou dicionário vazio se não existir
    """
    # Garantir que temos o ID em formato string
    usuario_id = str(usuario_id)
    
    # Caminho do arquivo para este usuário
    arquivo = os.path.join(ESTADOS_DIR, f"{usuario_id}.json")
    
    # Verificar se o arquivo existe
    if not os.path.exists(arquivo):
        return {}
    
    # Carregar e retornar os dados
    try:
        with open(arquivo, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao recuperar estado do usuário {usuario_id}: {e}")
        return {}