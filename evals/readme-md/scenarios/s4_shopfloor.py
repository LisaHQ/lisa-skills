"""Scenario s4: monorepo 'shopfloor' (create mode, monorepo root)."""
from fixture import w, git_init

ROOT = "s4-shopfloor"


def build(base):
    r = base / ROOT
    w(r / "package.json", '''\
{
  "name": "shopfloor",
  "private": true,
  "packageManager": "pnpm@9.12.0",
  "scripts": {
    "dev:web": "pnpm --filter @shopfloor/web dev",
    "build": "pnpm -r build",
    "lint": "pnpm -r lint",
    "gen:types": "pnpm --filter @shopfloor/shared-types gen"
  }
}
''')
    w(r / "pnpm-workspace.yaml", "packages:\n  - apps/web\n  - packages/*\n")
    w(r / "pnpm-lock.yaml", "lockfileVersion: '9.0'\n\nimporters:\n\n  .: {}\n\n  apps/web: {}\n\n  packages/shared-types: {}\n")
    w(r / ".nvmrc", "20\n")
    w(r / ".python-version", "3.12\n")
    w(r / ".env.example", '''\
# Copy to .env before running `make dev`.
POSTGRES_USER=shopfloor
POSTGRES_PASSWORD=change-me
POSTGRES_DB=shopfloor
DATABASE_URL=postgresql+psycopg://shopfloor:change-me@db:5432/shopfloor
API_CORS_ORIGINS=http://localhost:5173
VITE_API_URL=http://localhost:8000
''')
    w(r / "docker-compose.yml", '''\
services:
  db:
    image: postgres:16-alpine
    env_file: .env
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: ./apps/api
    env_file: .env
    command: sh -c "alembic upgrade head && uvicorn shopfloor_api.main:app --host 0.0.0.0 --port 8000 --reload"
    ports:
      - "8000:8000"
    volumes:
      - ./apps/api/src:/app/src
    depends_on:
      - db

  web:
    build: ./apps/web
    env_file: .env
    ports:
      - "5173:5173"
    volumes:
      - ./apps/web/src:/app/src
    depends_on:
      - api

volumes:
  pgdata:
''')
    w(r / "Makefile", '''\
.PHONY: dev seed migrate test down

dev: ## Start the database, API, and web app with live reload
\tdocker compose up --build

seed: ## Load demo machines and work orders (run while `make dev` is up)
\tdocker compose exec api python -m shopfloor_api.seed

migrate: ## Apply database migrations manually
\tdocker compose exec api alembic upgrade head

test: ## Run API and web tests
\tcd apps/api && uv run pytest
\tpnpm --filter @shopfloor/web test

down: ## Stop containers (keeps the database volume)
\tdocker compose down
''')
    # API
    w(r / "apps/api/pyproject.toml", '''\
[project]
name = "shopfloor-api"
version = "0.3.0"
description = "REST API for work orders and machine downtime."
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "sqlalchemy>=2.0",
  "alembic>=1.13",
  "psycopg[binary]>=3.2",
]

[dependency-groups]
dev = ["pytest>=8", "httpx>=0.27"]
''')
    w(r / "apps/api/uv.lock", "version = 1\nrequires-python = \">=3.12\"\n")
    w(r / "apps/api/Dockerfile", '''\
FROM python:3.12-slim
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src
''')
    w(r / "apps/api/src/shopfloor_api/__init__.py", "")
    w(r / "apps/api/src/shopfloor_api/main.py", '''\
"""Shopfloor API: work orders and machine downtime."""
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import Machine, WorkOrder, WorkOrderStatus, DowntimeEvent
from . import store

app = FastAPI(title="Shopfloor API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("API_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/work-orders")
def list_work_orders(status: WorkOrderStatus | None = None) -> list[WorkOrder]:
    return store.work_orders(status)


@app.post("/work-orders", status_code=201)
def create_work_order(order: WorkOrder) -> WorkOrder:
    return store.add_work_order(order)


@app.patch("/work-orders/{order_id}/status")
def move_work_order(order_id: int, status: WorkOrderStatus) -> WorkOrder:
    order = store.set_status(order_id, status)
    if order is None:
        raise HTTPException(404, "work order not found")
    return order


@app.get("/machines")
def list_machines() -> list[Machine]:
    return store.machines()


@app.get("/machines/{machine_id}/downtime")
def machine_downtime(machine_id: str, since: datetime | None = None) -> list[DowntimeEvent]:
    return store.downtime(machine_id, since)
''')
    w(r / "apps/api/src/shopfloor_api/models.py", '''\
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class WorkOrderStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"


class WorkOrder(BaseModel):
    id: int | None = None
    title: str
    machine_id: str
    status: WorkOrderStatus = WorkOrderStatus.open
    due: datetime | None = None


class MachineState(str, Enum):
    running = "running"
    idle = "idle"
    down = "down"


class Machine(BaseModel):
    id: str
    name: str
    state: MachineState


class DowntimeEvent(BaseModel):
    machine_id: str
    started: datetime
    ended: datetime | None
    reason: str
''')
    w(r / "apps/api/src/shopfloor_api/store.py", '''\
"""Database access (SQLAlchemy). Trimmed in this fixture."""


def work_orders(status=None): ...
def add_work_order(order): ...
def set_status(order_id, status): ...
def machines(): ...
def downtime(machine_id, since): ...
''')
    w(r / "apps/api/src/shopfloor_api/seed.py", '''\
"""Load demo data: 6 machines (CNC-01..CNC-04, PRESS-01, LATHE-01) and 20 work orders."""


def main() -> None:
    ...


if __name__ == "__main__":
    main()
''')
    w(r / "apps/api/alembic.ini", "[alembic]\nscript_location = migrations\n")
    w(r / "apps/api/migrations/versions/0001_initial.py", '"""Create machines, work_orders, downtime_events."""\n')
    w(r / "apps/api/tests/test_health.py", '''\
from fastapi.testclient import TestClient

from shopfloor_api.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}
''')
    w(r / "apps/api/README.md", '''\
# Shopfloor API

FastAPI service for work orders and machine downtime. Interactive docs run at
`http://localhost:8000/docs` while the API is up.

## Run without Docker

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/), plus a reachable
PostgreSQL database in `DATABASE_URL`.

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn shopfloor_api.main:app --reload --app-dir src
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| GET | `/work-orders?status=` | List work orders, optionally by status |
| POST | `/work-orders` | Create a work order |
| PATCH | `/work-orders/{id}/status` | Move a work order to another column |
| GET | `/machines` | List machines and their current state |
| GET | `/machines/{id}/downtime?since=` | Downtime events for one machine |

## Tests

```bash
uv run pytest
```
''')
    # Web
    w(r / "apps/web/package.json", '''\
{
  "name": "@shopfloor/web",
  "private": true,
  "version": "0.3.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 5173",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "lint": "eslint src"
  },
  "dependencies": {
    "@shopfloor/shared-types": "workspace:*",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.2",
    "typescript": "^5.6.0",
    "vite": "^5.4.8",
    "vitest": "^2.1.0"
  }
}
''')
    w(r / "apps/web/Dockerfile", '''\
FROM node:20-alpine
RUN corepack enable
WORKDIR /app
COPY . .
RUN pnpm install
CMD ["pnpm", "dev"]
''')
    w(r / "apps/web/src/App.tsx", '''\
import { WorkOrderBoard } from "./WorkOrderBoard";
import { MachineStatus } from "./MachineStatus";

/** Two screens: a Kanban board of work orders and a live machine status panel. */
export function App() {
  return (
    <main>
      <h1>Shopfloor</h1>
      <WorkOrderBoard columns={["open", "in_progress", "blocked", "done"]} />
      <MachineStatus refreshSeconds={15} />
    </main>
  );
}
''')
    w(r / "apps/web/src/WorkOrderBoard.tsx", '''\
import type { WorkOrder, WorkOrderStatus } from "@shopfloor/shared-types";

/** Drag a card to another column to PATCH /work-orders/{id}/status. */
export function WorkOrderBoard(props: { columns: WorkOrderStatus[] }) {
  return null as unknown as JSX.Element;
}
''')
    w(r / "apps/web/src/MachineStatus.tsx", '''\
/** Polls GET /machines every refreshSeconds and shows running / idle / down with the latest downtime reason. */
export function MachineStatus(props: { refreshSeconds: number }) {
  return null as unknown as JSX.Element;
}
''')
    w(r / "packages/shared-types/package.json", '''\
{
  "name": "@shopfloor/shared-types",
  "private": true,
  "version": "0.3.0",
  "main": "src/index.ts",
  "scripts": {
    "gen": "openapi-typescript http://localhost:8000/openapi.json -o src/api.d.ts"
  },
  "devDependencies": {
    "openapi-typescript": "^7.4.1"
  }
}
''')
    w(r / "packages/shared-types/src/index.ts", '''\
// Types shared by the web app. src/api.d.ts is generated from the API's OpenAPI
// schema with `pnpm gen:types` (the API must be running).
export type WorkOrderStatus = "open" | "in_progress" | "blocked" | "done";

export interface WorkOrder {
  id: number;
  title: string;
  machine_id: string;
  status: WorkOrderStatus;
  due: string | null;
}
''')
    w(r / ".gitignore", ".env\nnode_modules/\n.venv/\n__pycache__/\ndist/\n")
    git_init(r, remote="https://git.example.invalid/factory/shopfloor.git")
