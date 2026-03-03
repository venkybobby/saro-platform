# SARO v8.0 DB Layer -- Deployment Guide

## Option A: Docker Compose (recommended)

```bash
cp .env.example .env          # edit creds if needed
docker compose up -d          # starts db + redis + backend
docker compose run --rm migrate  # runs alembic upgrade head
```

## Option B: Manual (existing Postgres + Redis)

```bash
export DATABASE_URL=postgresql://user:pass@host:5432/saro_db
export SESSION_REDIS_URL=redis://host:6379/0
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Verify migration ran

```bash
cd backend
alembic current    # should show: 0001 (head)
alembic history    # full revision chain
```

## Rollback

```bash
alembic downgrade -1   # roll back one revision
alembic downgrade base # full rollback (destructive)
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | yes | `sqlite:///./saro_dev.db` | PostgreSQL or SQLite |
| `SESSION_REDIS_URL` | no | in-memory | Redis for auth sessions |
| `SQL_ECHO` | no | `false` | Log SQL to stdout |
