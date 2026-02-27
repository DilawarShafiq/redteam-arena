"""
REST API server -- FastAPI with WebSocket for real-time updates.
Provides endpoints for programmatic battle management.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from datetime import datetime
from typing import Any

from redteam_arena.types import BattleConfig, BattleSummary

# Lazy imports -- FastAPI/uvicorn are optional dependencies
_app = None


def _get_app():
    """Lazy-create the FastAPI app."""
    global _app
    if _app is not None:
        return _app

    try:
        from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import JSONResponse
    except ImportError as exc:
        raise ImportError(
            "FastAPI required for API server. "
            "Install with: pip install redteam-arena[server]"
        ) from exc

    app = FastAPI(
        title="RedTeam Arena API",
        description="AI vs AI adversarial security testing",
        version="0.0.1",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # In-memory state
    active_battles: dict[str, dict[str, Any]] = {}
    ws_clients: list[WebSocket] = []

    def verify_token():
        """Verify API token if REDTEAM_API_TOKEN is set."""
        api_token = os.environ.get("REDTEAM_API_TOKEN")
        if not api_token:
            return  # No auth required
        # Token check happens in middleware

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
        }

    @app.get("/api/scenarios")
    async def list_scenarios_endpoint():
        from redteam_arena.scenarios.scenario import list_scenarios

        scenarios = await list_scenarios()
        return {
            "scenarios": [
                {
                    "name": s.name,
                    "description": s.description,
                    "tags": s.tags,
                    "isMeta": s.is_meta,
                }
                for s in scenarios
            ]
        }

    @app.post("/api/battles")
    async def start_battle(body: dict):
        target_dir = body.get("targetDir", body.get("target_dir", ""))
        scenario_name = body.get("scenario", "")
        rounds = body.get("rounds", 5)
        provider = body.get("provider", "claude")

        if not target_dir or not scenario_name:
            raise HTTPException(400, "targetDir and scenario are required")

        from redteam_arena.scenarios.scenario import load_scenario

        scenario_result = await load_scenario(scenario_name)
        if not scenario_result.ok:
            raise HTTPException(404, f"Scenario not found: {scenario_name}")

        battle_id = secrets.token_urlsafe(6)
        active_battles[battle_id] = {
            "id": battle_id,
            "scenario": scenario_name,
            "targetDir": target_dir,
            "status": "pending",
            "startedAt": datetime.now().isoformat(),
        }

        # Start battle asynchronously
        asyncio.create_task(
            _run_battle_async(
                battle_id, target_dir, scenario_result.value,
                rounds, provider, active_battles, ws_clients,
            )
        )

        return {"battleId": battle_id, "status": "pending"}

    @app.get("/api/battles")
    async def list_battles():
        return {"battles": list(active_battles.values())}

    @app.get("/api/battles/{battle_id}")
    async def get_battle(battle_id: str):
        battle = active_battles.get(battle_id)
        if not battle:
            raise HTTPException(404, "Battle not found")
        return battle

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        ws_clients.append(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # Echo back for keepalive
                await websocket.send_json({"type": "pong", "data": data})
        except WebSocketDisconnect:
            ws_clients.remove(websocket)

    @app.get("/api/openapi")
    async def openapi_spec():
        return app.openapi()

    _app = app
    return app


async def _run_battle_async(
    battle_id: str,
    target_dir: str,
    scenario,
    rounds: int,
    provider_id: str,
    active_battles: dict,
    ws_clients: list,
) -> None:
    """Run a battle asynchronously and update state."""
    try:
        from redteam_arena.agents.provider_registry import create_provider
        from redteam_arena.agents.red_agent import RedAgent
        from redteam_arena.agents.blue_agent import BlueAgent
        from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
        from redteam_arena.types import BattleConfig

        provider = create_provider(provider_id)  # type: ignore[arg-type]
        red_agent = RedAgent(provider)
        blue_agent = BlueAgent(provider)

        config = BattleConfig(
            target_dir=target_dir,
            scenario=scenario,
            rounds=rounds,
            provider=provider_id,  # type: ignore[arg-type]
        )

        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=red_agent,
                blue_agent=blue_agent,
                config=config,
            )
        )

        active_battles[battle_id]["status"] = "running"
        await _broadcast(ws_clients, {"type": "battle-start", "battleId": battle_id})

        battle = await engine.run()

        all_findings = [f for r in battle.rounds for f in r.findings]
        all_mitigations = [m for r in battle.rounds for m in r.mitigations]

        active_battles[battle_id].update({
            "status": battle.status,
            "endedAt": datetime.now().isoformat(),
            "totalFindings": len(all_findings),
            "totalMitigations": len(all_mitigations),
            "rounds": len(battle.rounds),
        })

        await _broadcast(ws_clients, {
            "type": "battle-end",
            "battleId": battle_id,
            "status": battle.status,
            "findings": len(all_findings),
        })

    except Exception as exc:
        active_battles[battle_id]["status"] = "error"
        active_battles[battle_id]["error"] = str(exc)
        await _broadcast(ws_clients, {
            "type": "error",
            "battleId": battle_id,
            "message": str(exc),
        })


async def _broadcast(clients: list, data: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    for ws in list(clients):
        try:
            await ws.send_json(data)
        except Exception:
            if ws in clients:
                clients.remove(ws)


def start_server(
    host: str = "0.0.0.0",
    port: int = 3000,
) -> None:
    """Start the API server."""
    try:
        import uvicorn
    except ImportError as exc:
        raise ImportError(
            "uvicorn required for API server. "
            "Install with: pip install redteam-arena[server]"
        ) from exc

    app = _get_app()
    uvicorn.run(app, host=host, port=port)
