from fastapi import FastAPI, Query, HTTPException
import pandas as pd
from pathlib import Path
from fastapi.responses import JSONResponse, Response, HTMLResponse, RedirectResponse
from fastapi import Query


CSV_PATH = Path(__file__).with_name("ranking_completo.csv")

# Carrega o CSV uma única vez na memória
try:
    df = pd.read_csv(CSV_PATH)
except FileNotFoundError as e:
    raise RuntimeError(f"Arquivo {CSV_PATH} não encontrado.") from e

# (Opcional) já ordena pela sua métrica principal
df = df.sort_values("NOTA_FINAL", ascending=False).reset_index(drop=True)

app = FastAPI(title="Ranking API", version="0.1.0")

@app.head("/")          # Render envia HEAD; devolvemos 200
@app.get("/", tags=["health"])
def healthcheck():
    return JSONResponse({"status": "ok"})

@app.get("/ranking")
def read_ranking(
    limit: int | None = Query(None, ge=1, description="Máximo de linhas a retornar"),
    offset: int = Query(0, ge=0, description="Deslocamento inicial (paginacão)")
):
    """
    Retorna o ranking como JSON.
    
    • `limit`  – quantidade máxima de registros  
    • `offset` – posição inicial (útil para paginação)
    """
    data = df.iloc[offset: offset + limit if limit else None]\
             .to_dict(orient="records")
    return JSONResponse(content=data)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_html(
    limit: int = Query(100, ge=1, description="Linhas a exibir"),
    offset: int = Query(0, ge=0, description="Começar a partir de")
):
    """
    Mostra o ranking num <table> HTML.
    Aceita os mesmos parâmetros de paginação (limit, offset).
    """
    # Seleciona o trecho desejado
    subset = df.iloc[offset : offset + limit]

    # Converte para HTML; classes Bootstrap = zebra
    table_html = subset.to_html(index=False, classes="table table-striped table-sm")

    html = f"""
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <title>Ranking Universitário</title>
        <link
            href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
            rel="stylesheet">
    </head>
    <body class="container my-4">
        <h1 class="mb-4">Ranking Universitário</h1>
        {table_html}
        <p class="text-muted">Mostrando {len(subset)} de {len(df)} times.</p>
    </body>
    </html>
    """
    return HTMLResponse(html)