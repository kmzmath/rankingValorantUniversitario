
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse

# ──────────────────── CONFIGURAÇÃO ──────────────────── #
CSV_PATH = Path(__file__).with_name("ranking_completo.csv")

df = (
    pd.read_csv(CSV_PATH)
    .sort_values("NOTA_FINAL", ascending=False)
    .reset_index(drop=True)
)

app = FastAPI(
    title="Ranking Valorant Universitário",
    version="1.0.0",
    description="API + página simples para exibir o ranking de forma pública."
)

# ──────────────────── HEALTH-CHECK ──────────────────── #
@app.head("/")
def healthcheck() -> Response:
    """A Render faz HEAD / para conferir se o serviço está vivo."""
    return Response(status_code=200)

# ──────────────────── PÁGINA PRINCIPAL ───────────────── #
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_html(
    limit: int = Query(100, ge=1, description="Linhas a exibir"),
    offset: int = Query(0,  ge=0, description="Começar a partir de"),
) -> HTMLResponse:

    subset = df.iloc[offset : offset + limit]
    
    table_html = subset.to_html(
        index=False,
        classes="table table-striped table-sm align-middle",
        border=0,
        justify="center",
    )

    html = f"""
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <title>Ranking Valorant Universitário</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container my-4">
        <h1 class="mb-4">Ranking Valorant Universitário</h1>
        {table_html}
        <p class="text-muted">
            Mostrando {len(subset)} de {len(df)} times &middot;
            <a href="/ranking?limit={limit}&offset={offset}">Ver JSON</a>
        </p>
    </body>
    </html>
    """
    return HTMLResponse(html)

# ──────────────────── ENDPOINT JSON ──────────────────── #
@app.get("/ranking")
def read_ranking(
    limit: int | None = Query(None, ge=1, description="Máximo de linhas"),
    offset: int = Query(0, ge=0,   description="Deslocamento inicial"),
) -> JSONResponse:
    """
    Retorna o ranking em JSON.
    Parâmetros:
    • limit  – corta a quantidade máxima de registros
    • offset – posição inicial (paginação)
    """
    data = df.iloc[offset : offset + limit if limit else None].to_dict(orient="records")
    return JSONResponse(content=data)