import os, json, sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer

ROOT = Path(__file__).resolve().parent
DB = Path(os.getenv("AGENT_LAYER_DB", str(ROOT / "agent_layer.db")))

app = FastAPI(
    title="Agent Layer API",
    version="0.3.0",
    description="Machine-first UK commercial-property change intelligence.",
)

# x402 test payment configuration.
# Base Sepolia only for now; no private key is required by this API.
X402_PAY_TO = os.getenv(
    "X402_PAY_TO",
    "0x3ffc9a8b005d2ed2e64a32e330afb321eb3b89d3",
)
X402_PRICE = os.getenv("X402_PRICE", "$0.01")
X402_NETWORK = os.getenv("X402_NETWORK", "eip155:84532")
X402_FACILITATOR_URL = os.getenv(
    "X402_FACILITATOR_URL",
    "https://x402.org/facilitator",
)

facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url=X402_FACILITATOR_URL)
)
x402_server = x402ResourceServer(facilitator)
x402_server.register(X402_NETWORK, ExactEvmServerScheme())

paid_routes = {
    "GET /v1/commercial-property/changes": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price=X402_PRICE,
                network=X402_NETWORK,
                pay_to=X402_PAY_TO,
            )
        ],
        description="Derived UK commercial-property change events.",
        mime_type="application/json",
    )
}

app.add_middleware(
    PaymentMiddlewareASGI,
    routes=paid_routes,
    server=x402_server,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agent-layer.mbarr7.chatgpt.site",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

def rows(sql, args=()):
    if not DB.exists():
        raise HTTPException(503, "database_unavailable")
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, args).fetchall()]
    finally:
        con.close()

@app.get("/")
def root():
    return {
        "service": "Agent Layer",
        "dataset": "UK Commercial Property Change Feed",
        "version": "0.3.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/v1/health",
    }

@app.get("/v1/health")
def health():
    if not DB.exists():
        raise HTTPException(503, "database_unavailable")
    con = sqlite3.connect(DB)
    try:
        properties = con.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        snapshots = con.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        events = con.execute("SELECT COUNT(*) FROM change_events").fetchone()[0]
    finally:
        con.close()
    return {
        "status": "ok",
        "dataset": "uk-commercial-property-changes",
        "version": "0.3.0",
        "database": {
            "current_properties": properties,
            "snapshot_records": snapshots,
            "change_events": events,
        },
    }

@app.get("/v1/sources/status")
def source_status():
    return {"sources":[{
        "authority_code":"herefordshire",
        "authority_name":"Herefordshire Council",
        "licence":"OGL-3.0",
        "latest_snapshot":"2026-09-01",
        "previous_snapshot":"2026-08-01",
        "records":3686,
        "status":"healthy"
    }]}

@app.get("/v1/authorities")
def authorities():
    return {"authorities":[{
        "code":"herefordshire",
        "name":"Herefordshire Council",
        "licence":"OGL-3.0"
    }]}

@app.get("/v1/commercial-property/search")
def search(postcode: str = "", limit: int = Query(25, ge=1, le=100)):
    data = rows(
        "SELECT * FROM properties WHERE postcode LIKE ? ORDER BY postcode LIMIT ?",
        (postcode.upper() + "%", limit),
    )
    return {"count":len(data), "results":data}

@app.get("/v1/commercial-property/changes")
def changes(
    event_type: str | None = None,
    since: str | None = None,
    limit: int = Query(50, ge=1, le=250),
):
    clauses, args = [], []
    if event_type:
        clauses.append("event_type=?"); args.append(event_type.upper())
    if since:
        clauses.append("current_snapshot>=?"); args.append(since)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    args.append(limit)
    data = rows(
        f"SELECT * FROM change_events{where} ORDER BY id DESC LIMIT ?",
        tuple(args),
    )
    return {"count":len(data), "results":data}

@app.get("/v1/commercial-property/history/{record_id}")
def history(record_id: str):
    data = rows(
        "SELECT snapshot_date,payload_json FROM snapshots WHERE record_id=? ORDER BY snapshot_date",
        (record_id,),
    )
    if not data:
        raise HTTPException(404, "property_not_found")
    return {
        "record_id":record_id,
        "history":[
            {"snapshot_date":r["snapshot_date"], "record":json.loads(r["payload_json"])}
            for r in data
        ],
    }

@app.get("/v1/commercial-property/{record_id}")
def property_record(record_id: str):
    data = rows("SELECT * FROM properties WHERE record_id=?", (record_id,))
    if not data:
        raise HTTPException(404, "property_not_found")
    return data[0]
