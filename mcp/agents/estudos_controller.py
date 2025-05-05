from fastapi import APIRouter, Body, Depends
from typing import Dict, List, Any, Optional

from mcp.models.gemini_provider import create_gemini_provider
from mcp.core.state_manager import StateManager

router = APIRouter()

@router.post("/revisar")
async def revisar():
    """Endpoint legado. Use /gerar-resumo em vez disso."""
    model_provider = create_gemini_provider()
    if not model_provider:
        return {"error": "Provedor de modelo não disponível"}
    return await model_provider.generate_resume("geral")

@router.post("/quiz")
async def aplicar_quiz():
    """Endpoint legado. Use /gerar-quiz em vez disso."""
    model_provider = create_gemini_provider()
    if not model_provider:
        return {"error": "Provedor de modelo não disponível"}
    return await model_provider.generate_quiz("geral")

@router.post("/salvar-progresso")
def salvar_progresso(usuario_id: str, progresso_data: dict):
    """
    Salva o progresso de estudos de um usuário.
    
    Args:
        usuario_id: ID do usuário
        progresso_data: Dados de progresso a serem salvos
    """
    StateManager.save_state(usuario_id, {"progresso": progresso_data})
    return {"message": "Progresso salvo com sucesso."}

@router.get("/recuperar-progresso")
def recuperar_progresso(usuario_id: str):
    """
    Recupera o progresso de estudos de um usuário.
    
    Args:
        usuario_id: ID do usuário
    """
    estado = StateManager.get_state(usuario_id)
    progresso_data = estado.get("progresso", {})
    return {"progresso": progresso_data}

@router.post("/gerar-resumo")
async def gerar_resumo(topico: str = Body(..., embed=True)):
    """
    Gera um resumo sobre o tópico especificado.
    
    Args:
        topico: O tópico para gerar o resumo
    
    Returns:
        dict: Dicionário contendo o resumo gerado
    """
    model_provider = create_gemini_provider()
    if not model_provider:
        return {"error": "Provedor de modelo não disponível"}
    return await model_provider.generate_resume(topico)

@router.post("/gerar-quiz")
async def gerar_quiz(topico: Optional[str] = Body(None, embed=True)):
    """
    Gera um quiz de múltipla escolha sobre o tópico especificado.
    
    Args:
        topico: O tópico para gerar o quiz. Se não for fornecido, será gerado um quiz geral.
    
    Returns:
        dict: Dicionário contendo as perguntas do quiz
    """
    model_provider = create_gemini_provider()
    if not model_provider:
        return {"error": "Provedor de modelo não disponível"}
    return await model_provider.generate_quiz(topico or "geral")

@router.post("/avaliar-quiz")
def avaliar_quiz(
    respostas_usuario: List[int] = Body(..., embed=True), 
    respostas_certas: List[int] = Body(..., embed=True)
):
    """
    Avalia as respostas do usuário e retorna o resultado.
    
    Args:
        respostas_usuario: Lista com os índices das respostas do usuário (0-3 para A-D)
        respostas_certas: Lista com os índices das respostas corretas
    
    Returns:
        dict: Dicionário contendo os resultados da avaliação
    """
    # Contar respostas corretas
    acertos = 0
    detalhes = []
    
    for i, (user, correta) in enumerate(zip(respostas_usuario, respostas_certas)):
        acertou = user == correta
        if acertou:
            acertos += 1
            
        detalhes.append({
            "pergunta": i + 1,
            "resposta_usuario": chr(65 + user) if 0 <= user <= 25 else "?",
            "resposta_correta": chr(65 + correta) if 0 <= correta <= 25 else "?",
            "acertou": acertou
        })
        
    # Calcular porcentagem de acerto
    total = len(respostas_certas)
    porcentagem = int((acertos / total) * 100) if total > 0 else 0
    
    return {
        "pontuacao": acertos,
        "total": total,
        "porcentagem": porcentagem,
        "detalhes": detalhes
    }