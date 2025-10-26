# Backend – To Do List (Django + DRF)

API REST usada pelo app To Do List. Foi construída em Django + DRF, com autenticação baseada em cookies HTTPOnly e suporte completo a registro, verificação por código, login, refresh, logout e recuperação de senha.

## Pré‑requisitos

| Dependência | Versão recomendada | Observações |
| ----------- | ------------------ | ----------- |
| Python | 3.12 ou superior | Uso `python -m venv .venv` |
| Pip | Atualizado | `python -m pip install --upgrade pip` |
| SQLite | Incluso no Python | Nenhuma configuração extra |

## Configuração

1. **Clonar e preparar o `.env`**
   ```bash
   cd backend
   cp .env.example .env
   ```
   Ajuste `SECRET_KEY`, `ALLOWED_HOSTS` (incluindo seu IP/localhost) e, se for expor a API, configure `CORS_ALLOWED_ORIGINS`.

2. **Criar o ambiente virtual e instalar dependências**
   ```bash
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # Linux/macOS
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Banco e dados demo**
   ```bash
   python manage.py migrate
   python manage.py seed   # opcional
   ```

4. **Rodar o servidor**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   A API fica disponível em `http://<seu_ip>:8000/api/`.

## Endpoints principais

| Método | Rota | Descrição |
| ------ | ---- | --------- |
| POST | `/api/auth/register/` | Cadastro + envio de código |
| POST | `/api/auth/verify/` | Verifica o código de e‑mail |
| POST | `/api/auth/token/` | Login – emite `access_token` e `refresh_token` | 
| POST | `/api/auth/token/refresh/` | Renova o access token usando o cookie de refresh |
| POST | `/api/auth/logout/` | Limpa cookies de acesso e refresh |
| GET  | `/api/auth/me/` | Retorna o perfil autenticado |
| CRUD | `/api/tasks/` | CRUD completo de tarefas (filtros, checklist etc.) |

Os cookies são `httponly`, `path=/`, `SameSite=Lax` e `Secure` quando `DEBUG=False`. O middleware `CookieToAuthorizationMiddleware` injeta `Authorization: Bearer` em toda requisição que chega com `access_token` válido.

## Comandos úteis

| Ação | Comando |
| ---- | ------- |
| Migrar banco | `python manage.py migrate` |
| Criar superusuário | `python manage.py createsuperuser` |
| Rodar testes | `python manage.py test` |
| Popular dados demo | `python manage.py seed` |

## Observabilidade

- Logging estruturado está configurado em `server/settings.py`.
- `todos.exceptions.custom_exception_handler` padroniza respostas do DRF.
- O arquivo `server.log` registra tudo durante desenvolvimento.

## Dicas de rede / dispositivos

- Rode sempre em `0.0.0.0:8000` e inclua o IP local em `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS` para permitir que o app mobile acesse a API.
- Para ambientes remotos/túnel (ngrok, Cloudflare), configure a URL final em `ALLOWED_HOSTS`.

