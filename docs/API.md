# API — v1

Base: `/api/v1`  
Tenant: cabeçalho `X-Tenant-ID: demo-store`

## POST `/jobs`

Cria uma execução de coleta.

```json
{
  "query": "notebook gamer",
  "category_url": null,
  "max_pages": 2,
  "sort": "relevance"
}
```

Ações internas:

1. valida consulta, URL e limites;
2. resolve o tenant e o plano;
3. persiste o job como `pending`;
4. agenda a execução;
5. retorna HTTP 202 com o ID.

## GET `/jobs/{job_id}`

Retorna status, progresso, quantidade de itens e eventual erro. A busca é sempre escopada ao tenant.

## GET `/jobs/{job_id}/products`

Retorna os snapshots ordenados pela posição da coleta.

## GET `/jobs/{job_id}/export.csv`

Gera ou atualiza um CSV UTF-8 com BOM, adequado para Excel em português.

## GET `/jobs/{job_id}/report.pdf`

Gera um relatório PDF com métricas estatísticas, melhor custo-benefício estimado e até 25 produtos.

## GET `/health`

Retorna saúde, nome, versão, ambiente e provedor ativo.

## Códigos de erro

- `404`: tenant ou job não encontrado.
- `409`: exportação solicitada antes de existirem produtos.
- `422`: payload inválido.
- `500`: falha não tratada.
