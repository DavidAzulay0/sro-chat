from flask import Flask, request, jsonify
import os
from openai import OpenAI

app = Flask(__name__)

_knowledge = None

SYSTEM_PROMPT = """Você é um assistente especializado no SRO (Sistema de Registro de Operações) da SUSEP, versão 3.0.0.

Seu objetivo é ajudar o time a entender como registrar e consultar informações conforme o modelo de registro definido pelo SRO.

## Como responder perguntas sobre campos

Quando alguém perguntar sobre um campo, sempre informe:
1. **Formato**: o formato e tipo do dado (ex: AAAA-MM-DD, String, Int, Decimal...)
2. **Condição**: a condição de preenchimento do campo (quando é obrigatório, regras de validação)
3. **Bloco**: a qual bloco o campo pertence dentro do laioute
4. **Condição do bloco**: se o próprio bloco tem alguma condição de preenchimento

## Regras importantes

- O mesmo nome de campo pode existir em **blocos diferentes** dentro do mesmo laioute.
- Se o usuário não especificar o bloco, liste **todos os blocos** onde o campo aparece naquele laioute.
- Se o usuário não especificar o laioute, pergunte em qual laioute ele está trabalhando.
- Cardinalidade: [1..1] = obrigatório, [0..1] = opcional, [0..N] = múltiplos opcionais, [1..N] = ao menos um obrigatório.
- "Condicional Sistêmica: Sim" significa que há uma condição programática que determina quando o campo é obrigatório.

## Laioutes disponíveis
1 - Documento | 2 - Documento alteração | 3 - Sinistro evento gerador | 4 - Sinistro alteração
10 - Cosseguro aceito | 11 - Alteração coss aceito | 12 - Sinistro cosseguro aceito
13 - Alteração sinistro coss ac | 97 - Bloqueio Gravame | 98 - Transferencia | 99 - Exclusao

## Base de dados do SRO

{knowledge}
"""


def get_knowledge():
    global _knowledge
    if _knowledge is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sro_knowledge.txt')
        with open(data_path, 'r', encoding='utf-8') as f:
            _knowledge = f.read()
    return _knowledge


@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    body = request.get_json(silent=True) or {}
    messages = body.get('messages', [])

    if not messages:
        return jsonify({"error": "Nenhuma mensagem recebida."}), 400

    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return jsonify({"error": "Chave de API não configurada."}), 500

    try:
        client = OpenAI(api_key=api_key)
        knowledge = get_knowledge()
        system_content = SYSTEM_PROMPT.format(knowledge=knowledge)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_content}] + messages,
            temperature=0.1,
            max_tokens=1500,
        )

        reply = response.choices[0].message.content
        resp = jsonify({"reply": reply})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    except Exception as e:
        resp = jsonify({"error": f"Erro interno: {str(e)}"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 500
