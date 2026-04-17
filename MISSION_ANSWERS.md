# Day 12 Lab - Mission Answers

## Student Information
- Name: Ha Hung Phuoc
- Student ID: 2A202600367
- Date: 2026-04-17

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcoded secrets in source code (API key, DB URL).
2. Secrets leaked in logs.
3. Fixed port/host instead of environment-driven config.
4. Missing health and readiness endpoints.
5. Debug/reload behavior enabled in runtime path.
6. Non-structured logging (`print`) makes cloud observability harder.

### Exercise 1.2: Basic version run result
- App can run locally and answer requests.
- Not production-ready due to config, security, and operability gaps.

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcoded in code | Environment-based settings | Move across dev/staging/prod without code changes |
| Health checks | Missing | `/health` and `/ready` present | Required by orchestrators/load balancers |
| Logging | Plain print | Structured JSON | Easier tracing/searching in cloud logs |
| Shutdown | Abrupt | Graceful shutdown flow | Reduces dropped requests on restart/deploy |
| Host/Port | Fixed localhost:8000 | `0.0.0.0` + env port | Works in containers/cloud platforms |
| Secrets | In source and logs | Injected by env vars | Prevent secret exposure |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11` (develop) and slim variants in production.
2. Working directory: `/app`.
3. Why copy requirements first: better layer cache reuse.
4. `CMD` vs `ENTRYPOINT`: `CMD` is default command, `ENTRYPOINT` fixes main executable behavior.

### Exercise 2.2: Build/run result
- Built and ran the develop image successfully.
- API reachable through mapped port.

### Exercise 2.3: Image size comparison
- Develop: 1.66GB
- Production: 236MB
- Difference: ~85.8% smaller

### Exercise 2.4: Compose architecture and services
- Services: `agent`, `redis`, `qdrant`, `nginx`.
- Flow: Client -> Nginx -> Agent -> Redis/Qdrant.
- Verified compose boot and health endpoint behavior.

## Part 3: Cloud Deployment

### Exercise 3.1: Render deployment
- URL: https://ai-agent-5cj8.onrender.com
- Docs: https://ai-agent-5cj8.onrender.com/docs
- Health check verification: `status = ok`
- Platform: Render

### Exercise 3.2: Render vs Railway (summary)
- Render blueprint defines multi-service infra directly from `render.yaml`.
- Railway `railway.toml` is service-focused and often paired with CLI variable setup.

### Exercise 3.3: Cloud Run (optional)
- Reviewed role of `cloudbuild.yaml` and `service.yaml` for CI/CD + service config.

## Part 4: API Security

### Exercise 4.1: API key authentication
- API key enforced through dependency and `X-API-Key` header.
- Missing/invalid key returns proper auth errors.
- Key rotation is environment-driven (`AGENT_API_KEY`), no source edit required.

### Exercise 4.2: JWT flow
- Obtained token via auth endpoint.
- Called protected endpoint with `Authorization: Bearer <token>` successfully.

### Exercise 4.3: Rate limiting
- Algorithm used: Sliding window counter.
- Limits observed by role profile (user lower quota, admin higher quota).
- Repeated calls eventually trigger 429 as expected.

### Exercise 4.4: Cost guard implementation
- Budget tracked per-user per-month in Redis key: `budget:<user_id>:YYYY-MM`.
- Estimated request cost added with `INCRBYFLOAT`.
- Request denied when monthly threshold exceeded.
- TTL set so old period keys expire automatically.

## Part 5: Scaling & Reliability

### Exercise 5.1: Health and readiness
- Implemented and verified `/health` and `/ready` behaviors.
- Health returns runtime status; readiness guards traffic while app initializes/shuts down.

### Exercise 5.2: Graceful shutdown
- Signal handling integrated with server lifecycle.
- Shutdown waits for in-flight requests and exits cleanly.

### Exercise 5.3: Stateless refactor
- Removed per-instance in-memory conversation dependency.
- Session/history stored in Redis so replicas share state.

### Exercise 5.4: Load balancing
- Stack run with multiple agent replicas behind Nginx.
- Requests distributed across instances.

### Exercise 5.5: Stateless test results
- `test_stateless.py` passed.
- Multiple different instance IDs served requests.
- Conversation history remained intact via Redis-backed session state.

## Part 6: Final Project Completion Summary

- Local verification completed in `06-lab-complete`.
- Production readiness checker: 20/20 checks passed (100%).
- Public deployment verified on Render.

## Evidence Snapshot

- Local final stack checks:
  - `HEALTH=ok`
  - `READY=True`
  - `/ask` returned valid response
- Cloud checks:
  - `https://ai-agent-5cj8.onrender.com/docs` reachable
  - `https://ai-agent-5cj8.onrender.com/health` returned `status=ok`
