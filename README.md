# SRO SUSEP — Assistente de Registro

Chat com LLM para tirar dúvidas sobre campos, blocos e laioutes do SRO SUSEP v3.0.0.

## Deploy na Vercel

### 1. Suba o projeto para o GitHub

```bash
cd sro-chat
git init
git add .
git commit -m "feat: assistente SRO SUSEP"
git remote add origin https://github.com/SEU_USUARIO/sro-chat.git
git push -u origin main
```

### 2. Importe na Vercel

1. Acesse [vercel.com/new](https://vercel.com/new)
2. Clique em **"Import Git Repository"**
3. Selecione o repositório `sro-chat`
4. Em **Environment Variables**, adicione:
   - **Name:** `OPENAI_API_KEY`
   - **Value:** `sk-proj-...` (sua chave OpenAI)
5. Clique em **Deploy**

### Estrutura do projeto

```
sro-chat/
├── api/
│   └── chat.py          # Serverless function (Python)
├── data/
│   └── sro_knowledge.txt  # Base de conhecimento extraída do Excel
├── index.html           # Frontend do chat
├── vercel.json          # Configuração da Vercel
├── requirements.txt     # Dependências Python
└── README.md
```

### Como funciona

1. O Excel SRO foi parseado em um arquivo texto estruturado (`data/sro_knowledge.txt`)
2. A cada mensagem, o backend injeta toda a base de dados no system prompt do GPT-4o-mini
3. O modelo responde com base nos dados reais do SRO, sem inventar informações

### Para atualizar a base de dados

Quando o leiaute SRO for atualizado, execute o script de parsing e substitua o arquivo `data/sro_knowledge.txt`:

```bash
python3 parse_excel.py "novo_leiaute.xlsx"
```
