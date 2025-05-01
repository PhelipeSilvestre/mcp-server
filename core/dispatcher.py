import logging
import os
import requests
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters
)
from config.settings import TELEGRAM_TOKEN
from core.state_manager import salvar_estado, recuperar_estado
from agents.estudos.resumo import gerar_resumo
from agents.estudos.quiz import gerar_quiz, avaliar_quiz

# Configurar logging para depuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar o bot
bot = Bot(token=TELEGRAM_TOKEN)

async def start(update: Update, context: CallbackContext):
    """Comando inicial do bot."""
    usuario_id = str(update.effective_user.id)
    logger.info(f"Comando /start recebido de {update.effective_user.username} (ID: {usuario_id})")
    
    # Salvar estado inicial do usuário
    salvar_estado(usuario_id, {"ultimo_comando": "start"})
    
    await update.message.reply_text(
        "Olá! Eu sou seu assistente de estudos. "
        "Use /resumo <tópico> para gerar um resumo ou /quiz <tópico> para iniciar um quiz."
    )

async def enviar_resumo(update: Update, context: CallbackContext):
    """Gera um resumo sobre o tópico especificado."""
    usuario_id = str(update.effective_user.id)
    logger.info(f"Comando /resumo recebido de {update.effective_user.username} (ID: {usuario_id})")
    
    # Obter o tópico dos argumentos do comando
    topico = ' '.join(context.args) if context.args else ""
    if not topico:
        await update.message.reply_text("Por favor, forneça um tópico. Exemplo: /resumo HTTP")
        return

    # Salvar o tópico no estado do usuário
    salvar_estado(usuario_id, {"ultimo_topico": topico})
    
    await update.message.reply_text(f"Gerando resumo sobre '{topico}'. Aguarde um momento...")
    
    try:
        # Gerar o resumo de forma assíncrona
        resultado = await gerar_resumo(topico)
        await update.message.reply_text(resultado.get("resumo", "Erro ao gerar resumo."))
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {e}")
        await update.message.reply_text(f"Ocorreu um erro ao gerar o resumo: {str(e)}")

async def enviar_quiz(update: Update, context: CallbackContext):
    """Envia um quiz para o usuário."""
    usuario_id = str(update.effective_user.id)
    logger.info(f"Comando /quiz recebido de {update.effective_user.username} (ID: {usuario_id})")
    
    # Obter o tópico dos argumentos do comando ou usar o último tópico usado
    topico = ' '.join(context.args) if context.args else None
    
    # Se não foi fornecido um tópico, usar o último tópico usado pelo usuário
    if not topico:
        estado = recuperar_estado(usuario_id)
        topico = estado.get("ultimo_topico", "geral")
        await update.message.reply_text(f"Gerando quiz sobre o último tópico: '{topico}'...")
    else:
        # Salvar o tópico no estado do usuário
        salvar_estado(usuario_id, {"ultimo_topico": topico})
        await update.message.reply_text(f"Gerando quiz sobre '{topico}'...")
    
    try:
        # Gerar o quiz de forma assíncrona
        resultado = await gerar_quiz(topico)
        
        if "error" in resultado:
            await update.message.reply_text(f"Erro ao gerar quiz: {resultado['error']}")
            return
        
        perguntas = resultado.get("quiz", [])
        
        if not perguntas:
            await update.message.reply_text("Não foi possível gerar perguntas para o quiz.")
            return
        
        # Salvar as perguntas no estado do usuário para referência futura
        salvar_estado(usuario_id, {"quiz_atual": perguntas})
        
        # Enviar cada pergunta
        mensagem = "📝 *QUIZ* 📝\n\n"
        for i, pergunta in enumerate(perguntas):
            mensagem += f"*Pergunta {i+1}*: {pergunta['pergunta']}\n\n"
            for j, opcao in enumerate(pergunta['opcoes']):
                mensagem += f"{chr(65+j)}) {opcao}\n"
            mensagem += "\n"
        
        mensagem += "Para responder, use /responder seguido das letras correspondentes às suas respostas (ex: /responder ABCDE)"
        await update.message.reply_text(mensagem)
    except Exception as e:
        logger.error(f"Erro ao gerar quiz: {e}")
        await update.message.reply_text(f"Ocorreu um erro ao gerar o quiz: {str(e)}")

async def responder_quiz(update: Update, context: CallbackContext):
    """Processa as respostas do usuário a um quiz."""
    usuario_id = str(update.effective_user.id)
    logger.info(f"Comando /responder recebido de {update.effective_user.username} (ID: {usuario_id})")
    
    if not context.args or len(context.args[0]) == 0:
        await update.message.reply_text("Por favor, forneça suas respostas. Exemplo: /responder ABCDE")
        return
    
    # Obter o quiz atual do usuário
    estado = recuperar_estado(usuario_id)
    quiz_atual = estado.get("quiz_atual", [])
    
    if not quiz_atual:
        await update.message.reply_text("Não há um quiz ativo. Gere um quiz primeiro com /quiz <tópico>.")
        return
    
    # Converter as respostas em letras para índices (A=0, B=1, etc)
    respostas_texto = context.args[0].upper()
    respostas_usuario = []
    
    for letra in respostas_texto:
        if 'A' <= letra <= 'D':
            respostas_usuario.append(ord(letra) - ord('A'))
        else:
            respostas_usuario.append(-1)  # Resposta inválida
    
    # Garantir que temos o mesmo número de respostas que perguntas
    while len(respostas_usuario) < len(quiz_atual):
        respostas_usuario.append(-1)
    
    # Limitar ao número de perguntas
    respostas_usuario = respostas_usuario[:len(quiz_atual)]
    
    # Obter respostas corretas
    respostas_certas = [pergunta['resposta_correta'] for pergunta in quiz_atual]
    
    # Avaliar as respostas
    resultado = avaliar_quiz(respostas_usuario, respostas_certas)
    
    # Preparar a mensagem de resultado
    mensagem = f"📊 *Resultado do Quiz* 📊\n\n"
    mensagem += f"Você acertou {resultado['pontuacao']} de {resultado['total']} perguntas!\n\n"
    
    for i, feedback in enumerate(resultado['feedback']):
        pergunta = quiz_atual[i]
        mensagem += f"*Pergunta {i+1}*: "
        if feedback['acerto']:
            mensagem += "✅ Correto!\n"
        else:
            opcao_usuario = chr(ord('A') + feedback['sua_resposta']) if 0 <= feedback['sua_resposta'] <= 25 else "?"
            opcao_correta = chr(ord('A') + feedback['resposta_correta'])
            mensagem += f"❌ Errado. Sua resposta: {opcao_usuario}, Correta: {opcao_correta}\n"
    
    await update.message.reply_text(mensagem)
    
    # Limpar o quiz atual após a resposta
    salvar_estado(usuario_id, {"quiz_atual": None})

async def handle_message(update: Update, context: CallbackContext):
    """Trata mensagens que não são comandos."""
    await update.message.reply_text("Mensagem não reconhecida. Use /start para ver os comandos disponíveis.")

def configurar_webhook(url_base):
    """Configura o webhook do Telegram."""
    webhook_url = f"{url_base}/webhook/telegram"
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    
    try:
        response = requests.post(api_url, json={"url": webhook_url})
        resultado = response.json()
        if resultado.get("ok"):
            logger.info(f"Webhook configurado com sucesso: {webhook_url}")
            return True
        else:
            logger.error(f"Falha ao configurar webhook: {resultado}")
            return False
    except Exception as e:
        logger.error(f"Erro ao configurar webhook: {e}")
        return False

async def processar_update_async(update_json):
    """Processa uma atualização recebida do webhook do Telegram de forma assíncrona."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    update = Update.de_json(update_json, application.bot)
    
    # Processar a atualização baseada no tipo de mensagem
    if update.message and update.message.text:
        try:
            if update.message.text.startswith('/start'):
                await start(update, None)
            elif update.message.text.startswith('/resumo'):
                # Extrair o tópico do texto da mensagem
                partes = update.message.text.split(' ', 1)
                topico = partes[1] if len(partes) > 1 else ""
                context = type('obj', (object,), {'args': topico.split()})
                await enviar_resumo(update, context)
            elif update.message.text.startswith('/quiz'):
                # Extrair o tópico do texto da mensagem
                partes = update.message.text.split(' ', 1)
                topico = partes[1] if len(partes) > 1 else ""
                context = type('obj', (object,), {'args': topico.split()})
                await enviar_quiz(update, context)
            elif update.message.text.startswith('/responder'):
                # Extrair as respostas do texto da mensagem
                partes = update.message.text.split(' ', 1)
                respostas = partes[1] if len(partes) > 1 else ""
                context = type('obj', (object,), {'args': [respostas]})
                await responder_quiz(update, context)
            else:
                await handle_message(update, None)
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            await update.message.reply_text(f"Ocorreu um erro ao processar sua mensagem: {str(e)}")

def processar_update(update_json):
    """Wrapper para processo assíncrono que processa atualizações."""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(processar_update_async(update_json))
    loop.close()

def main():
    """Função principal para iniciar o bot."""
    # Configuração do aplicativo
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Adicionar handlers para comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("resumo", enviar_resumo))
    application.add_handler(CommandHandler("quiz", enviar_quiz))
    application.add_handler(CommandHandler("responder", responder_quiz))
    
    # Handler para mensagens não reconhecidas
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Iniciando o bot do Telegram usando polling...")
    
    # Iniciar o bot - não será executado em um loop em execução
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Bot encerrado.")

if __name__ == "__main__":
    main()