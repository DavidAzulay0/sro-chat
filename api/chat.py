from http.server import BaseHTTPRequestHandler
import json
import os
from openai import OpenAI

# Load knowledge base once at module level (cached between warm invocations)
_knowledge = None

def get_knowledge():
    global _knowledge
    if _knowledge is None:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'sro_knowledge.txt')
        with open(data_path, 'r', encoding='utf-8') as f:
            _knowledge = f.read()
    return _knowledge

SYSTEM_PROMPT = """Você é um assistente especializado no SRO (Sistema de Registro de Operações) da SUSEP, versão 3.0.0.

Seu objetivo é ajudar o time a entender como registrar e consultar informações conforme o modelo de registro definido pelo SRO.

## Como responder perguntas sobre campos

Quando alguém perguntar sobre um campo, sempre informe:
1. **Formato**: o formato e tipo do dado (ex: AAAA-MM-DD, String, Int, Decimal...)
2. **Condição**: a condição de preenchimento do campo (quando é obrigatório, regras de validação)
3. **Bloco**: a qual bloco o campo pertence dentro do laioute
4. **Condição do bloco**: se o próprio bloco tem alguma condição de preenchimento (quando o bloco inteiro é obrigatório ou condicional)

## Regras importantes

- O mesmo nome de campo pode existir em **blocos diferentes** dentro do mesmo laioute (ex: "Data de Início" pode estar em "Dados Gerais" e em "Cobertura de Seguro").
- Se o usuário não especificar o bloco, liste **todos os blocos** onde o campo aparece naquele laioute.
- Se o usuário não especificar o laioute, pergunte em qual laioute ele está trabalhando.
- A cardinalidade indica obrigatoriedade: [1..1] = obrigatório, [0..1] = opcional, [0..N] = múltiplos registros opcionais, [1..N] = ao menos um obrigatório.
- "Condicional Sistêmica: Sim" significa que há uma condição programática que determina quando o campo é obrigatório.

## Laioutes disponíveis
- 1 - Documento
- 2 - Documento alteração
- 3 - Sinistro evento gerador
- 4 - Sinistro alteração
- 10 - Cosseguro aceito
- 11 - Alteração coss aceito
- 12 - Sinistro cosseguro aceito
- 13 - Alteração sinistro coss ac
- 97 - Bloqueio Gravame
- 98 - Transferencia
- 99 - Exclusao

## Formato de resposta

Responda de forma clara e objetiva em português. Use markdown quando útil (negrito, listas).
Seja direto: primeiro dê a resposta, depois os detalhes.

## Base de dados do SRO

{knowledge}
"""


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default logging

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            messages = body.get('messages', [])

            if not messages:
                self._send_error(400, "Nenhuma mensagem recebida.")
                return

            api_key = os.environ.get('OPENAI_API_KEY', '')
            if not api_key:
                self._send_error(500, "Chave de API não configurada.")
                return

            client = OpenAI(api_key=api_key)
            knowledge = get_knowledge()
            system_content = SYSTEM_PROMPT.replace('{knowledge}', knowledge)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_content}] + messages,
                temperature=0.1,
                max_tokens=1500,
            )

            reply = response.choices[0].message.content
            self._send_json(200, {"reply": reply})

        except json.JSONDecodeError:
            self._send_error(400, "JSON inválido.")
        except Exception as e:
            self._send_error(500, f"Erro interno: {str(e)}")

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status, message):
        self._send_json(status, {"error": message})
