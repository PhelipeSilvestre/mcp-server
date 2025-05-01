from typing import List, Dict, Any
from agents.estudos.servico_gemini import gerar_quiz as gerar_quiz_gemini

async def gerar_quiz(topico: str = None):
    """
    Gera um quiz de múltipla escolha sobre um tópico.
    
    Args:
        topico (str, optional): O tópico para gerar o quiz. Se não for fornecido,
                               será gerado um quiz geral.
    
    Returns:
        dict: Dicionário contendo as perguntas do quiz
    """
    try:
        if not topico:
            topico = "conhecimentos gerais"
        
        perguntas = await gerar_quiz_gemini(topico)
        return {"quiz": perguntas}
    except Exception as e:
        return {"error": str(e)}

def avaliar_quiz(respostas_usuario, respostas_certas):
    """
    Avalia as respostas do usuário e calcula a pontuação.
    
    Args:
        respostas_usuario (List): Lista com as respostas do usuário
        respostas_certas (List): Lista com o índice das respostas corretas
    
    Returns:
        dict: Dicionário com os resultados da avaliação
    """
    pontuacao = 0
    feedback = []
    
    for i, (resposta_usuario, resposta_certa) in enumerate(zip(respostas_usuario, respostas_certas)):
        acerto = resposta_usuario == resposta_certa
        if acerto:
            pontuacao += 1
        feedback.append({
            "pergunta": i + 1,
            "acerto": acerto,
            "sua_resposta": resposta_usuario,
            "resposta_correta": resposta_certa
        })

    return {
        "pontuacao": pontuacao,
        "total": len(respostas_certas),
        "feedback": feedback,
        "mensagem": f"Você acertou {pontuacao} de {len(respostas_certas)} perguntas."
    }