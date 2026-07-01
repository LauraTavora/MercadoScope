# MercadoScope — Inteligência de Preços para Portfólio

**Versão:** 1.0.0  
**Nível:** Intermediário  
**Objetivo:** pesquisar produtos públicos do Mercado Livre por termo ou categoria, coletar dados comerciais, armazenar histórico, exportar CSV e gerar relatório PDF de análise de preços.

> O modo padrão é `mock`, para que a demonstração funcione sem acessar sites externos. O modo `browser` existe para páginas públicas, sem login, sem contornar CAPTCHA, bloqueios ou limites. Antes de ativá-lo, valide os Termos de Uso, o `robots.txt` e a legislação aplicável. Para operação comercial, prefira o provedor `api` com credenciais oficiais.

## O que o projeto entrega

- Dashboard web responsivo com formulário de nova coleta.
- Provedores intercambiáveis: `mock`, `browser` e `api`.
- Coleta de título, preço, avaliação, quantidade de avaliações, vendas, URL e imagem.
- Jobs em segundo plano com status, progresso e tratamento de falhas.
- Histórico por tenant e por execução.
- Exportação CSV.
- Relatório PDF automático com resumo estatístico e produtos de destaque.
- Gráfico de distribuição de preços e tabela pesquisável.
- Planos nativos: Starter, Pro e Agency, com limites por execução.
- Multi-tenant básico por cabeçalho `X-Tenant-ID` ou tenant demo.
- Onboarding e tour do produto na primeira visita.
- Versionamento visível no rodapé e endpoint `/health`.
- Documentação técnica, estratégica, comercial, API, squads e concorrentes.

## Execução rápida

### Opção 1 — ambiente local

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

Abra `http://localhost:8000`.

Para instalar o Chromium do Playwright:

```bash
playwright install chromium
```

### Opção 2 — Docker

```bash
cp .env.example .env
docker compose up --build
```

## Modos de coleta

### Demonstração segura

```env
SCRAPER_PROVIDER=mock
SCRAPING_ENABLED=false
```

Gera produtos simulados de forma determinística e permite demonstrar toda a aplicação.

### Browser público

```env
SCRAPER_PROVIDER=browser
SCRAPING_ENABLED=true
```

O coletor:

1. aceita apenas URLs `mercadolivre.com.br`;
2. consulta `robots.txt` antes da navegação;
3. usa atraso configurável;
4. não autentica, não resolve CAPTCHA e não contorna bloqueios;
5. interrompe a execução quando a página não permite automação.

### API oficial

```env
SCRAPER_PROVIDER=api
MELI_ACCESS_TOKEN=seu_token
```

O token é enviado como Bearer. Dependendo do endpoint e das permissões vigentes, o campo de avaliação pode não estar disponível e será salvo como nulo.

## Endpoints principais

- `GET /` — dashboard.
- `POST /api/v1/jobs` — cria uma coleta.
- `GET /api/v1/jobs/{job_id}` — acompanha status e resultados.
- `GET /api/v1/jobs/{job_id}/products` — lista produtos em JSON.
- `GET /api/v1/jobs/{job_id}/export.csv` — baixa CSV.
- `GET /api/v1/jobs/{job_id}/report.pdf` — baixa relatório PDF.
- `GET /health` — saúde, versão e ambiente.

Consulte [`docs/API.md`](docs/API.md) para contratos completos.

## Exemplo de requisição

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: demo-store" \
  -d '{
    "query": "notebook gamer",
    "max_pages": 2,
    "sort": "relevance"
  }'
```

## Estrutura

```text
app/
  api/            Rotas HTTP
  services/       Coleta, análise, exportação e relatório
  static/         CSS e JavaScript
  templates/      Interface Jinja2
  config.py       Configurações
  database.py     Sessão e bootstrap
  models.py       Entidades persistidas
  schemas.py      Contratos Pydantic

docs/             Documentação do produto
tests/            Testes automatizados
data/              Banco, relatórios e CSVs locais
```

## Testes

```bash
pytest -q
```

## Limitações conhecidas

- Seletores de páginas públicas podem mudar sem aviso.
- SQLite é adequado para demonstração; em produção, use PostgreSQL.
- O executor interno de jobs é simples e reinícios do processo podem interromper uma coleta em andamento. Em escala, use Redis + Celery/RQ/Arq.
- O modo browser não deve ser usado para burlar mecanismos de proteção.

## Roadmap

- Autenticação por usuário e RBAC.
- Agendamento recorrente.
- Alertas de variação de preço.
- PostgreSQL + Redis + worker dedicado.
- Comparação de múltiplos marketplaces.
- Webhooks e integrações com Slack/WhatsApp.
- Dashboard de séries históricas.
