from pathlib import Path
import pandas as pd
from fastapi import FastAPI, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
import numpy as np

# ────────────────── CARREGAMENTO DE DADOS ────────────────── #
CSV_PATH   = Path(__file__).with_name("ranking_completo.csv")
TEAMS_PATH = Path(__file__).with_name("teams.xlsx")

# Ranking
df = (
    pd.read_csv(CSV_PATH)
    .sort_values("NOTA_FINAL", ascending=False)
    .reset_index(drop=True)
)

# Times
try:
    df_times = pd.read_excel(TEAMS_PATH, engine="openpyxl")
    df_times = df_times.loc[:, ~df_times.columns.str.contains(r"^Unnamed")].reset_index(drop=True)
except FileNotFoundError:
    df_times = pd.DataFrame(columns=["team_name", "slug", "org", "icon"])

# ────────────────── FASTAPI ────────────────── #
app = FastAPI(
    title="Ranking Valorant Universitário",
    version="1.1.1",
    description="Ranking + lista de times expostos como API REST."
)

# Health-check
@app.head("/")
def healthcheck() -> Response:
    return Response(status_code=200)

# Página HTML do ranking
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_html(
    limit:  int = Query(100, ge=1),
    offset: int = Query(0,   ge=0)
) -> HTMLResponse:
    subset = df.iloc[offset : offset + limit]
    table_html = subset.to_html(
        index=False,
        classes="table table-striped table-sm align-middle",
        border=0,
        justify="center",
    )
    html = f"""<!doctype html><html lang="pt-BR"><head>
        <meta charset="utf-8"><title>Ranking Valorant Universitário</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"></head>
        <body class="container my-4">
        <h1 class="mb-4">Ranking Valorant Universitário</h1>
        {table_html}
        <p class="text-muted">Mostrando {len(subset)} de {len(df)} times ·
           <a href="/ranking?limit={limit}&offset={offset}">Ver JSON</a></p>
        </body></html>"""
    return HTMLResponse(html)

# JSON do ranking
@app.get("/ranking")
def read_ranking(
    limit:  int | None = Query(None, ge=1),
    offset: int        = Query(0,    ge=0),
):
    data = df.iloc[offset : offset + limit if limit else None].to_dict("records")
    return JSONResponse(content=data)

# JSON dos times
@app.get("/times")
def read_times(
    team:   str | None = Query(None, description="Filtro por nome ou slug"),
    org:    str | None = Query(None, description="Filtro por universidade/org"),
    limit:  int | None = Query(None, ge=1),
    offset: int        = Query(0,    ge=0),
):
    result = df_times
    if team:
        mask_name = result["team_name"].str.contains(team, case=False, na=False)
        mask_slug = result["slug"].str.contains(team, case=False, na=False)
        result = result[mask_name | mask_slug]
    if org:
        result = result[result["org"].str.contains(org, case=False, na=False)]

    # paginação
    result = result.iloc[offset : offset + limit if limit else None]

    # ─── Substitui NaN/Inf por None ───
    result_clean = result.replace({np.nan: None, np.inf: None, -np.inf: None})

    return JSONResponse(content=jsonable_encoder(result_clean.to_dict("records")))