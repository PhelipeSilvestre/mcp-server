from fastapi import APIRouter, Body
from typing import Dict, List, Any, Optional
from agents.estudos import resumo, quiz, progresso

router = APIRouter()

@router.post("/revisar")
async def revisar():
    """Endpoint legado. Use /gerar-resumo em vez disso."""
    return await resumo.gerar_resumo("geral")

@router.post("/quiz")
async def aplicar_quiz():
    """Endpoint legado. Use /gerar-quiz em vez disso."""
    return await quiz.gerar_quiz()

@router.post("/salvar-progresso")
def salvar_progresso(usuario_id: str, progresso_data: dict):
    progresso.salvar_progresso(usuario_id, progresso_data)
    return {"message": "Progresso salvo com sucesso."}

@router.get("/recuperar-progresso")
def recuperar_progresso(usuario_id: str):
    progresso_data = progresso.recuperar_progresso(usuario_id)
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
    return await resumo.gerar_resumo(topico)

@router.post("/gerar-quiz")
async def gerar_quiz(topico: Optional[str] = Body(None, embed=True)):
    """
    Gera um quiz de múltipla escolha sobre o tópico especificado.
    
    Args:
        topico: O tópico para gerar o quiz. Se não for fornecido, será gerado um quiz geral.
    
    Returns:
        dict: Dicionário contendo as perguntas do quiz
    """
    return await quiz.gerar_quiz(topico)

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
    return quiz.avaliar_quiz(respostas_usuario, respostas_certas)

@router.post("/webhook/n8n")
async def n8n_webhook(payload: Dict[str, Any]):
    """
    Webhook para integração com n8n. Dispara rotinas de estudo.
    
    Args:
        payload: Dados recebidos do n8n
    
    Returns:
        dict: Resultado da operação solicitada
    """
    acao = payload.get("acao")
    if acao == "resumo":
        topico = payload.get("topico", "")
        if not topico:
            return {"error": "Tópico não fornecido."}
        return await resumo.gerar_resumo(topico)
    elif acao == "quiz":
        topico = payload.get("topico", None)
        return await quiz.gerar_quiz(topico)
    else:
        return {"error": "Ação desconhecida."}
