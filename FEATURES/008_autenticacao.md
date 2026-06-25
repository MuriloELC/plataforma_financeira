# Feature 008 — Autenticação

## Objetivo
Proteger acesso local ao sistema.

## Requisitos
- Login.
- Hash de senha.
- JWT ou sessão.
- Rotas protegidas.
- Arquivos protegidos.

## Regras
- Sem senha em texto puro.
- Sem expor arquivo bruto sem autenticação.
- Logs sem dados sensíveis.

## Modelagem
- `app.users`
- `audit.audit_log`

## Endpoints
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

## Telas
- Login.

## Testes
- Login válido/inválido.
- Rota protegida.

## Critérios de aceite
- Acesso protegido.

## Prompt para Codex
```text
Implemente autenticação simples para MVP local com usuário único.
```
