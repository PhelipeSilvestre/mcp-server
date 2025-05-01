import os
from agents.estudos.servico_openai import gerar_resumo_openai

async def gerar_resumo(topico: str):
    """
    Gera um resumo de um tópico usando o serviço OpenAI.
    
    Args:
        topico (str): O tópico para gerar o resumo
        
    Returns:
        dict: Dicionário contendo o resumo gerado ou mensagem de erro
    """
    try:
        resumo = await gerar_resumo_openai(topico)
        return {"resumo": resumo}
    except Exception as e:
        return {"error": str(e)}
