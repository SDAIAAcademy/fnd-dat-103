"""A mock of the charge-point platform API, with faults injected on a fixed schedule.

It is a FastAPI application. The labs call it in-process through a test client, which behaves
like an httpx.Client, so no server, port or network is needed:

    import mockapi
    client = mockapi.client(token="fdt103-mock-token-not-a-secret")
    client.get("/v1/sessions", params={"limit": 100}).json()

To serve it on this computer and call it with any HTTP client (optional), from labs/:

    uv run python mockapi.py            # prints the address it listens on; Ctrl+C stops it

Endpoints (newest session first, as many platforms list them):

    GET /v1/sessions?limit=&cursor=     cursor pagination: {"data": [...], "next_cursor": "..." | null}
    GET /v1/sessions-by-offset?limit=&offset=
                                        offset pagination: {"data": [...], "total": n}
    GET /v1/terms                       the API's terms: rate limit and use

Every request needs the header "Authorization: Bearer <token>". The fault schedule counts the
requests the app has received: by default request 3 gets 429 with Retry-After, request 6 gets
503, request 9 gets 500 with an HTML body, request 13 gets 429 again. On the offset endpoint,
new sessions arrive (are inserted at the top) after the second page is served.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import warnings

warnings.filterwarnings("ignore", message=".*httpx2.*")

from fastapi import FastAPI, Header, Request
from fastapi.responses import HTMLResponse, JSONResponse

DATA = Path(__file__).resolve().parent / "data" / "api"
TOKEN = "fdt103-mock-token-not-a-secret"
DEFAULT_FAULTS = {3: ("429", 2), 6: ("503", None), 9: ("500", None), 13: ("429", 1)}
TERMS = {
    "service": "charge-point platform API (course mock)",
    "rate_limit": "60 requests per minute per token; answer 429 with Retry-After when exceeded",
    "use": "the network's own staff and contractors; keep raw responses for 30 days; no resale",
    "auth": "bearer token, issued per person; never commit it",
}


def _load(name: str) -> list[dict]:
    with open(DATA / name, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _cursor(sid: str) -> str:
    return base64.urlsafe_b64encode(f"before:{sid}".encode()).decode().rstrip("=")


def _uncursor(c: str) -> str:
    pad = "=" * (-len(c) % 4)
    return base64.urlsafe_b64decode(c + pad).decode().split(":", 1)[1]


def make_app(records: list[dict] | None = None, arrivals: list[dict] | None = None, faults: dict | None = None, token: str = TOKEN) -> FastAPI:
    app = FastAPI(title="Charge-point platform API (course mock)")
    rows = sorted(records if records is not None else _load("sessions.jsonl"), key=lambda r: r["session_id"], reverse=True)
    waiting = list(arrivals if arrivals is not None else _load("arrivals.jsonl"))
    plan = dict(DEFAULT_FAULTS if faults is None else faults)
    state = {"n": 0, "offset_pages": 0, "rows": rows}
    app.state.mock = state

    def gate(authorization: str | None):
        state["n"] += 1
        if authorization != f"Bearer {token}":
            return JSONResponse({"error": "unauthorised"}, status_code=401)
        f = plan.get(state["n"])
        if f is None:
            return None
        kind, wait = f
        if kind == "429":
            return JSONResponse({"error": "rate limit exceeded"}, status_code=429, headers={"Retry-After": str(wait)})
        if kind == "503":
            return JSONResponse({"error": "service unavailable"}, status_code=503)
        return HTMLResponse("<html><body><h1>Internal error</h1></body></html>", status_code=500)

    @app.get("/v1/terms")
    def terms(authorization: str | None = Header(default=None)):
        return gate(authorization) or TERMS

    @app.get("/v1/sessions")
    def sessions(limit: int = 100, cursor: str | None = None, authorization: str | None = Header(default=None)):
        bad = gate(authorization)
        if bad:
            return bad
        limit = max(1, min(limit, 200))
        data = state["rows"]
        if cursor:
            before = _uncursor(cursor)
            data = [r for r in data if r["session_id"] < before]
        page = data[:limit]
        nxt = _cursor(page[-1]["session_id"]) if len(data) > limit else None
        return {"data": page, "next_cursor": nxt}

    @app.get("/v1/sessions-by-offset")
    def by_offset(limit: int = 100, offset: int = 0, authorization: str | None = Header(default=None)):
        bad = gate(authorization)
        if bad:
            return bad
        limit = max(1, min(limit, 200))
        state["offset_pages"] += 1
        if state["offset_pages"] == 3 and waiting:  # new sessions arrive while the client pages
            state["rows"] = sorted(waiting + state["rows"], key=lambda r: r["session_id"], reverse=True)
            waiting.clear()
        data = state["rows"]
        return {"data": data[offset : offset + limit], "total": len(data)}

    @app.exception_handler(ValueError)
    async def bad_cursor(request: Request, exc: ValueError):
        return JSONResponse({"error": "bad cursor"}, status_code=400)

    return app


def client(token: str = TOKEN, **kw):
    """An in-process client for a fresh mock (its own fault counter)."""
    from fastapi.testclient import TestClient

    return TestClient(make_app(token=TOKEN, **kw), base_url="http://mock.local", headers={"Authorization": f"Bearer {token}"} if token else {})


if __name__ == "__main__":
    import socket

    import uvicorn

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    print(f"mock API on http://127.0.0.1:{port}/v1/sessions (token in .env.example); Ctrl+C stops it")
    uvicorn.run(make_app(), host="127.0.0.1", port=port, log_level="warning")
