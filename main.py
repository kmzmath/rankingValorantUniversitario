from fastapi import FastAPI, Query, HTTPException
import pandas as pd
from pathlib import Path
from fastapi.responses import JSONResponse, Response

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