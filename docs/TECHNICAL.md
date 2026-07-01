# Documentação Técnica

## Arquitetura

O MercadoScope usa uma arquitetura modular em camadas:

1. **Interface web:** Jinja2 + JavaScript, responsável por criar e acompanhar jobs.
2. **API:** FastAPI, com contratos Pydantic e rotas versionadas em `/api/v1`.
3. **Domínio:** tenants, planos, jobs e snapshots de produto.
4. **Serviços:** provedores de coleta, análise, CSV e PDF.
5. **Persistência:** SQLAlchemy com SQLite no demo e suporte a PostgreSQL via `DATABASE_URL`.

## Multi-tenant

- O tenant é resolvido pelo cabeçalho `X-Tenant-ID`, cookie `tenant_slug` ou tenant padrão.
- Toda consulta de job é filtrada por `tenant_id`.
- Os limites são herdados do plano do tenant.
- Em produção, acrescente autenticação, RBAC e políticas de banco por tenant.

## Planos nativos

| Plano | Itens/job | Páginas/job |
|---|---:|---:|
| Starter | 50 | 1 |
| Pro | 250 | 5 |
| Agency | 1000 | 10 |

## Ciclo de um job

`pending → running → completed` ou `failed`.

O executor em memória é suficiente para demonstração. Para produção, substitua por fila externa e worker dedicado.

## Provedores

- `mock`: dados determinísticos para demonstração.
- `browser`: Playwright, somente páginas públicas e autorizadas por `robots.txt`.
- `api`: endpoint oficial de busca, com token opcional/necessário conforme regras vigentes.

## Segurança

- Validação de domínio para URL informada.
- Sem login automatizado.
- Sem contorno de CAPTCHA, fingerprint, bloqueios ou limites.
- Limites de páginas e itens no servidor.
- Consultas SQL via ORM.
- Escape de texto no frontend.
- Erros operacionais limitados antes de persistência.

## Evolução recomendada

- PostgreSQL, Redis e Celery/Arq.
- Autenticação OIDC.
- Rate limiting por tenant.
- Observabilidade OpenTelemetry.
- Testes E2E Playwright.
- Alertas e agendamentos.
