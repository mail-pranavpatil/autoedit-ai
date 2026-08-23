# Implementation Decisions for Render Deployment (AutoEdit AI)

---

## Decision 1: Dockerfile.web — Production
Switched Dockerfile.web from:
- `npm run dev`
to:
- `RUN npm run build`
- `CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]`

**Reasoning:** Render and production must not use a development server. Build/static output and correct host/port binding enable safe, scalable, secure prod deployment. This maintains local Docker Compose dev behavior by only adjusting Dockerfile.web used in production services.

---

## Decision 2: Dockerfile.api — Flexible Port
Switched Dockerfile.api from:
- `alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port 8000`
to:
- `alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`

**Reasoning:** This allows Render to inject its own port via the `PORT` env variable while retaining backward compatibility for local (dev/compose) as 8000 default. It is a minimal, safe change for both environments.

---

## Decision 3: Dockerfile.worker — No Immediate Change
Inspected Dockerfile.worker and found it uses only environment variables for config, builds as production, includes ffmpeg, and copies all necessary files. No change required.

---

(*Further decisions to be logged as implementation proceeds*)
# Implementation Decisions for Render Deployment (AutoEdit AI)

This file logs every decision taken during the Render deployment modernization.

---
