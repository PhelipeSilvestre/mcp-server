import json
import os

# Caminho para o arquivo de progresso
PROGRESS_FILE = "progress.json"

# Função para salvar progresso do usuário
def salvar_progresso(usuario_id, progresso):
    if not os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({}, f)

    with open(PROGRESS_FILE, 'r') as f:
        dados = json.load(f)

    dados[usuario_id] = progresso

    with open(PROGRESS_FILE, 'w') as f:
        json.dump(dados, f, indent=4)

# Função para recuperar progresso do usuário
def recuperar_progresso(usuario_id):
    if not os.path.exists(PROGRESS_FILE):
        return {}

    with open(PROGRESS_FILE, 'r') as f:
        dados = json.load(f)

    return dados.get(usuario_id, {})

# Função para avaliar se o usuário pode avançar
def avaliar_progresso(pontuacao):
    if pontuacao >= 3:  # Exemplo: 3/5 corretas para avançar
        return "Avançar para o próximo tópico"
    return "Revisar novamente o tópico atual"