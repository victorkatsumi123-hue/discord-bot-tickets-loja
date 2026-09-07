# Discord Bot - Tickets + Loja

Bot completo em **discord.py** com:

- 🎫 Sistema de Tickets (abrir, categorias, fechar)
- 🛒 Sistema de Loja / Venda de itens
- Painéis com botões
- Comandos de administração

## Como configurar

1. Crie um bot no [Discord Developer Portal](https://discord.com/developers/applications)
2. Ative as intents: `MESSAGE CONTENT`, `SERVER MEMBERS`
3. Coloque o **TOKEN** nas variáveis de ambiente (Railway, Render, etc.)
4. No arquivo `cogs/tickets.py`, configure:
   - `TICKET_CATEGORY_ID`
   - `STAFF_ROLE_ID`

## Comandos

- `/painel_ticket` → Envia o painel de tickets (Admin)
- `/painel_loja` → Envia o painel da loja (Admin)
- `/adicionar_produto` → Adiciona produto na loja (Admin)

## Hospedagem recomendada

- Railway
- Render
- Replit
