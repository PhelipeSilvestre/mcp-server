import openai
from openai import AsyncOpenAI
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a chave da API OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError(
        "API key da OpenAI não encontrada! Certifique-se de adicionar OPENAI_API_KEY=sua_chave_aqui no arquivo .env"
    )

# Configurar cliente assíncrono da OpenAI
client = AsyncOpenAI(api_key=api_key)

async def gerar_resumo_openai(topico: str) -> str:
    """
    Gera um resumo sobre um tópico usando a API ChatCompletion da OpenAI.
    
    Args:
        topico (str): O tópico para gerar o resumo
        
    Returns:
        str: O resumo gerado
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um tutor especialista e objetivo."},
                {"role": "user", "content": f"Escreva um resumo claro e didático sobre o seguinte tópico: {topico}"}
            ],
            temperature=0.7,
            max_tokens=700
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao gerar resumo: {str(e)}"
        print(error_msg)
        return error_msg


async def gerar_quiz_openai(topico: str) -> List[Dict[str, Any]]:
    """
    Gera um quiz de múltipla escolha sobre um tópico usando a API ChatCompletion da OpenAI.
    
    Args:
        topico (str): O tópico para gerar o quiz
        
    Returns:
        List[Dict]: Lista de perguntas com opções e resposta correta
    """
    try:
        prompt = (
            f"Gere 5 perguntas de múltipla escolha sobre o tópico: {topico}. "
            "Para cada pergunta, forneça 4 opções (A, B, C, D) e indique qual é a correta. "
            "Retorne em formato JSON com o seguinte formato para cada pergunta:\n"
            "{\n"
            "  \"pergunta\": \"texto da pergunta\",\n"
            "  \"opcoes\": [\"opção A\", \"opção B\", \"opção C\", \"opção D\"],\n"
            "  \"resposta_correta\": 0 // índice da resposta correta (0 a 3)\n"
            "}"
        )

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um professor criando um quiz educativo. Responda apenas com o JSON solicitado."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        # Extrair o JSON da resposta
        import json
        import re
        
        # Tenta encontrar estruturas JSON na resposta
        json_pattern = r"\[\s*{.*}\s*\]"
        json_match = re.search(json_pattern, content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            # Fallback: tentar interpretar a resposta completa como JSON
            try:
                return json.loads(content)
            except:
                # Último recurso: criar um formato simples com a resposta de texto
                return [{"pergunta": "Não foi possível gerar o quiz no formato correto. Aqui está a resposta textual:", 
                         "opcoes": [content], 
                         "resposta_correta": 0}]
    except Exception as e:
        return [{"pergunta": f"Erro ao gerar quiz: {str(e)}", 
                 "opcoes": ["Tente novamente mais tarde"], 
                 "resposta_correta": 0}]