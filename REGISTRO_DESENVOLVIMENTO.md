# Registro de Desenvolvimento – Backend

Relato cronológico resumido de como o backend evoluiu.

1. **Planejamento e setup**
   - Defini a stack (Django + DRF + SQLite) e preparei o projeto `server`.
   - Configurei `.env.example`, `.gitignore`, requirements e o app `todos`.

2. **Modelagem e autenticação**
   - Modelei usuários, verificações de e‑mail, códigos de senha e tarefas.
   - Implementei toda a jornada `/api/auth/*` (registro, verificação, login, refresh, logout, reset).
   - Implementei login utilizando JWT Token, salvando-o no Local Storage.
3. **REST + extras**
   - Terminei o CRUD de tarefas com filtros, checklist e ordering.
   - Adicionei o handler de exceções (`todos.exceptions`) e logging estruturado.
   - Escrevi `manage.py seed` para gerar uma conta demo e tarefas iniciais.

4. **Ajustes recentes**
   - Documentei a exigência de `withCredentials` / suporte a cookies nos clientes.
   - Tornei obrigatório o `_skipAuthRefresh` para chamadas críticas a fim de evitar loops de refresh.


5. **Uso transparente de IA**
   - Registrei o apoio pontual de IA (utilizado o CODEX) em cada fase (planejamento, modelagem, REST e ajustes), sempre como sparring para validar ideias, revisar textos e levantar riscos.
   - Mantive as criações das decisõees técnicas e do código, tratando as sugestões da IA como referências e ajustando tudo ao contexto do projeto.
