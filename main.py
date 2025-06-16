from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder

# ────────────────── CAMINHOS DE ARQUIVO ────────────────── #
BASE = Path(__file__).parent
CSV_PATH      = BASE / "ranking_completo.csv"
TEAMS_PATH    = BASE / "teams.xlsx"
MATCHES_PATH  = BASE / "matches.xlsx"

# ────────────────── CARREGA DADOS ───────────────────────── #
# Ranking
df_ranking = (
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

# Partidas
try:
    df_matches = pd.read_excel(MATCHES_PATH, engine="openpyxl")
    df_matches = df_matches.loc[:, ~df_matches.columns.str.contains(r"^Unnamed")].reset_index(drop=True)
except FileNotFoundError:
    df_matches = pd.DataFrame()

# ───────────────────── FASTAPI ──────────────────────────── #
app = FastAPI(
    title="Ranking Valorant Universitário",
    version="1.2.0",
    description="Ranking, lista de times e partidas expostos como API REST."
)

# ── HEALTH-CHECK ───────────────────────────────────────────
@app.head("/")
def healthcheck() -> Response:
    return Response(status_code=200)

# ── RAIZ: TABELA HTML DO RANKING ──────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_html(
    limit:  int = Query(100, ge=1),
    offset: int = Query(0,   ge=0),
) -> HTMLResponse:
    subset = df_ranking.iloc[offset : offset + limit]
    table = subset.to_html(index=False,
                           classes="table table-striped table-sm align-middle",
                           border=0, justify="center")
    html = f"""<!doctype html><html lang="pt-BR"><head>
    <meta charset="utf-8"><title>Ranking Valorant Universitário</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head><body class="container my-4">
    <h1 class="mb-4">Ranking Valorant Universitário</h1>
    {table}
    <p class="text-muted">Mostrando {len(subset)} de {len(df_ranking)} times ·
       <a href="/ranking?limit={limit}&offset={offset}">Ver JSON</a></p>
    </body></html>"""
    return HTMLResponse(html)

# ── ENDPOINT /ranking ─────────────────────────────────────
@app.get("/ranking")
def read_ranking(
    limit:  int | None = Query(None, ge=1),
    offset: int        = Query(0,    ge=0),
):
    data = df_ranking.iloc[offset : offset + limit if limit else None]
    return JSONResponse(content=jsonable_encoder(data.replace({np.nan: None}).to_dict("records")))

# ── ENDPOINT /times ───────────────────────────────────────
@app.get("/times")
def read_times(
    team:   str | None = Query(None, description="Filtro por nome ou slug"),
    org:    str | None = Query(None, description="Filtro por universidade/org"),
    limit:  int | None = Query(None, ge=1),
    offset: int        = Query(0,    ge=0),
):
    result = df_times
    if team:
        m1 = result["team_name"].str.contains(team, case=False, na=False)
        m2 = result["slug"].str.contains(team, case=False, na=False)
        result = result[m1 | m2]
    if org:
        result = result[result["org"].str.contains(org, case=False, na=False)]

    result = result.iloc[offset : offset + limit if limit else None]
    result = result.replace({np.nan: None})
    return JSONResponse(content=jsonable_encoder(result.to_dict("records")))

# ── ENDPOINT /partidas ────────────────────────────────────
@app.get("/partidas")
def read_partidas(
    team:        str | None = Query(None, description="time presente em team_i ou team_j"),
    campeonato:  str | None = Query(None, description="filtra pelo campo campeonato"),
    limit:  int | None = Query(None, ge=1),
    offset: int        = Query(0,    ge=0),
):
    if df_matches.empty:
        return JSONResponse(content=[])

    result = df_matches
    if team:
        m1 = result["team_i"].str.contains(team, case=False, na=False)
        m2 = result["team_j"].str.contains(team, case=False, na=False)
        result = result[m1 | m2]
    if campeonato:
        result = result[result["campeonato"].str.contains(campeonato, case=False, na=False)]

    result = result.iloc[offset : offset + limit if limit else None]
    result = result.replace({np.nan: None})
    return JSONResponse(content=jsonable_encoder(result.to_dict("records")))