import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
import asyncio

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a chave da API Gemini do ambiente
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Configurar a API Gemini
genai.configure(api_key=gemini_api_key)

# Modelo padrão do Gemini
GEMINI_MODEL = "gemini-1.5-flash"

async def _fazer_requisicao_api_gemini(prompt: str, model_name: str = GEMINI_MODEL) -> str:
    """
    Função que faz requisição à API do Google Gemini.
    
    Args:
        prompt (str): O prompt a ser enviado para o modelo
        model_name (str): O nome do modelo Gemini a ser usado
        
    Returns:
        str: O texto gerado pelo modelo ou uma mensagem de erro
    """
    if not gemini_api_key:
        return "Erro: Chave de API do Gemini não configurada."
    
    try:
        # Criando o modelo generativo
        model = genai.GenerativeModel(model_name)
        
        print(f"Enviando requisição para modelo Gemini: {model_name}")
        print(f"Prompt: {prompt[:50]}...")
        
        # Utilizando uma função async para executar a chamada síncrona em uma thread separada
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        # Extrair o texto da resposta
        if response and hasattr(response, 'text'):
            return response.text.strip()
        else:
            return "Erro: Resposta vazia ou inválida do modelo."
            
    except Exception as e:
        error_msg = f"Erro ao fazer requisição para a API Gemini: {str(e)}"
        print(error_msg)
        return f"Erro: {str(e)}"

async def gerar_resumo(topico: str) -> str:
    """
    Gera um resumo sobre um tópico usando a API do Google Gemini.
    
    Args:
        topico (str): O tópico para gerar o resumo
        
    Returns:
        str: O resumo gerado
    """
    prompt = f"Escreva um resumo claro e didático em português sobre: {topico}"
    
    resultado = await _fazer_requisicao_api_gemini(prompt)
    
    # Verifica se o resultado é satisfatório
    if resultado.startswith("Erro") or len(resultado.split()) < 10:
        print(f"Não foi possível gerar um resumo satisfatório para: {topico}")
        return f"Não foi possível gerar um resumo sobre '{topico}'. Por favor, tente novamente mais tarde ou com outro tópico."
    
    return resultado

async def gerar_quiz(topico: str) -> List[Dict[str, Any]]:
    """
    Gera um quiz de múltipla escolha sobre um tópico usando a API do Google Gemini.
    
    Args:
        topico (str): O tópico para gerar o quiz
        
    Returns:
        List[Dict]: Lista de perguntas com opções e resposta correta
    """
    prompt = (
        f"Gere 3 perguntas de múltipla escolha em português sobre o tópico: {topico}. "
        f"Cada pergunta deve ter exatamente 4 alternativas (A, B, C, D) e indicar qual é a correta. "
        f"Retorne as perguntas no seguinte formato JSON:\n"
        f"[\n"
        f"  {{\n"
        f"    \"pergunta\": \"texto da pergunta 1\",\n"
        f"    \"opcoes\": [\"texto opção A\", \"texto opção B\", \"texto opção C\", \"texto opção D\"],\n"
        f"    \"resposta_correta\": 0  // índice da resposta correta (0 para A, 1 para B, etc)\n"
        f"  }},\n"
        f"  // outras perguntas no mesmo formato\n"
        f"]\n"
        f"Certifique-se de que o formato seja exatamente JSON válido, sem comentários."
    )
    
    resultado = await _fazer_requisicao_api_gemini(prompt)
    
    print(f"Resposta do Gemini para quiz: {resultado[:100]}...")
    
    # Processar o resultado JSON
    try:
        # Limpar o texto para encontrar apenas o JSON válido
        # Remover tudo antes do primeiro '['
        if '[' in resultado:
            resultado = resultado[resultado.find('['):]
        
        # Remover tudo depois do último ']'
        if ']' in resultado:
            resultado = resultado[:resultado.rfind(']')+1]
            
        import json
        perguntas = json.loads(resultado)
        
        # Validar formato das perguntas
        for pergunta in perguntas:
            # Garantir que temos todos os campos necessários
            if not all(k in pergunta for k in ("pergunta", "opcoes", "resposta_correta")):
                raise ValueError("Formato de pergunta inválido")
            
            # Garantir que temos exatamente 4 opções
            if len(pergunta["opcoes"]) != 4:
                # Ajustar para ter exatamente 4 opções
                if len(pergunta["opcoes"]) < 4:
                    pergunta["opcoes"].extend([f"Opção {i+1}" for i in range(len(pergunta["opcoes"]), 4)])
                else:
                    pergunta["opcoes"] = pergunta["opcoes"][:4]
            
            # Garantir que a resposta_correta é um índice válido
            if not isinstance(pergunta["resposta_correta"], int) or pergunta["resposta_correta"] < 0 or pergunta["resposta_correta"] > 3:
                pergunta["resposta_correta"] = 0
        
        return perguntas
        
    except Exception as e:
        print(f"Erro ao processar resposta do quiz: {e}")
        # Se houver erro no processamento, retornar um quiz genérico
        return [
            {
                "pergunta": f"Não foi possível gerar perguntas sobre {topico}. Por favor, tente novamente.",
                "opcoes": [
                    "Tentar novamente", 
                    "Escolher outro tópico",
                    "Contatar o administrador",
                    "Verificar a conexão com a API"
                ],
                "resposta_correta": 0
            }
        ]