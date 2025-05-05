import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from mcp.core.config import ESTADOS_DIR

class StateManager:
    """
    Gerencia o armazenamento e recuperação do estado dos usuários.
    Versão refatorada para a arquitetura MCP.
    """
    
    @staticmethod
    def save_state(user_id: str, data: Dict[str, Any]) -> None:
        """
        Salva o estado do usuário em arquivo JSON.
        
        Args:
            user_id (str): ID único do usuário
            data (Dict[str, Any]): Dados a serem salvos
        """
        # Garantir que temos o ID em formato string
        user_id = str(user_id)
        
        # Caminho do arquivo para este usuário
        file_path = os.path.join(ESTADOS_DIR, f"{user_id}.json")
        
        # Carregar dados existentes, se houver
        current_state = StateManager.get_state(user_id)
        
        # Atualizar com novos dados
        current_state.update(data)
        
        # Adicionar timestamp da última atualização
        current_state["last_update"] = datetime.now().isoformat()
        
        # Salvar no arquivo
        with open(file_path, 'w') as f:
            json.dump(current_state, f, indent=2)
    
    @staticmethod
    def get_state(user_id: str) -> Dict[str, Any]:
        """
        Recupera o estado do usuário.
        
        Args:
            user_id (str): ID único do usuário
            
        Returns:
            Dict[str, Any]: Estado atual do usuário ou dicionário vazio se não existir
        """
        # Garantir que temos o ID em formato string
        user_id = str(user_id)
        
        # Caminho do arquivo para este usuário
        file_path = os.path.join(ESTADOS_DIR, f"{user_id}.json")
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            return {}
        
        # Carregar e retornar os dados
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao recuperar estado do usuário {user_id}: {e}")
            return {}
    
    @staticmethod
    def delete_state(user_id: str) -> bool:
        """
        Exclui o estado de um usuário.
        
        Args:
            user_id (str): ID único do usuário
            
        Returns:
            bool: True se excluído com sucesso, False caso contrário
        """
        user_id = str(user_id)
        file_path = os.path.join(ESTADOS_DIR, f"{user_id}.json")
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                print(f"Erro ao excluir estado do usuário {user_id}: {e}")
                return False
        return False
    
    @staticmethod
    def get_property(user_id: str, property_name: str, default: Any = None) -> Any:
        """
        Recupera uma propriedade específica do estado do usuário.
        
        Args:
            user_id (str): ID único do usuário
            property_name (str): Nome da propriedade a recuperar
            default (Any, optional): Valor padrão caso a propriedade não exista
            
        Returns:
            Any: Valor da propriedade ou o default se não existir
        """
        state = StateManager.get_state(user_id)
        return state.get(property_name, default)

# Funções de compatibilidade com o código legado
def salvar_estado(usuario_id: str, dados: Dict[str, Any]) -> None:
    """Função de compatibilidade com a antiga API"""
    StateManager.save_state(usuario_id, dados)

def recuperar_estado(usuario_id: str) -> Dict[str, Any]:
    """Função de compatibilidade com a antiga API"""
    return StateManager.get_state(usuario_id)