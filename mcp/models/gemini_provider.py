import os
from typing import List, Dict, Any
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

class GeminiProvider:
    """
    Provider para o modelo Gemini da Google.
    Gerencia a comunicação com a API do Gemini.
    """
    
    # Modelo padrão do Gemini
    DEFAULT_MODEL = "gemini-1.5-flash"
    
    def __init__(self, api_key: str = None):
        """
        Inicializa o provider do Gemini.
        
        Args:
            api_key (str, optional): Chave de API do Gemini. Se não fornecida, usa a variável de ambiente.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Chave de API do Gemini não configurada.")
            
        # Configurar a API Gemini
        genai.configure(api_key=self.api_key)
        
    async def generate_content(self, prompt: str, model_name: str = None) -> str:
        """
        Gera conteúdo utilizando o modelo Gemini.
        
        Args:
            prompt (str): Prompt para o modelo
            model_name (str, optional): Nome do modelo a ser usado. Se não fornecido, usa o modelo padrão.
            
        Returns:
            str: Conteúdo gerado
        """
        model_name = model_name or self.DEFAULT_MODEL
        
        try:
            # Criando o modelo generativo
            model = genai.GenerativeModel(model_name)
            
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
    
    async def generate_resume(self, topic: str) -> Dict[str, Any]:
        """
        Gera um resumo sobre um tópico.
        
        Args:
            topic (str): O tópico para gerar o resumo
            
        Returns:
            Dict[str, Any]: Dicionário com o resumo gerado
        """
        prompt = f"Escreva um resumo claro e didático em português sobre: {topic}"
        
        resultado = await self.generate_content(prompt)
        
        # Verifica se o resultado é satisfatório
        if resultado.startswith("Erro") or len(resultado.split()) < 10:
            error_msg = f"Não foi possível gerar um resumo satisfatório para: {topic}"
            return {
                "error": error_msg,
                "success": False
            }
        
        return {
            "resumo": resultado,
            "topic": topic,
            "success": True
        }
    
    async def generate_quiz(self, topic: str, num_questions: int = 3) -> Dict[str, Any]:
        """
        Gera um quiz de múltipla escolha sobre um tópico.
        
        Args:
            topic (str): O tópico para gerar o quiz
            num_questions (int): Número de perguntas a gerar
            
        Returns:
            Dict[str, Any]: Dicionário com o quiz gerado
        """
        prompt = (
            f"Gere {num_questions} perguntas de múltipla escolha em português sobre o tópico: {topic}. "
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
        
        resultado = await self.generate_content(prompt)
        
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
            
            return {
                "quiz": perguntas,
                "topic": topic,
                "success": True
            }
            
        except Exception as e:
            print(f"Erro ao processar resposta do quiz: {e}")
            return {
                "error": f"Erro ao gerar quiz sobre {topic}: {str(e)}",
                "success": False,
                "quiz": []
            }

# Função auxiliar para criar uma instância do provider
def create_gemini_provider() -> GeminiProvider:
    """
    Cria e retorna uma instância do provider do Gemini.
    
    Returns:
        GeminiProvider: Provider para o modelo Gemini
    """
    try:
        return GeminiProvider()
    except ValueError as e:
        print(f"Erro ao criar provider Gemini: {e}")
        return None