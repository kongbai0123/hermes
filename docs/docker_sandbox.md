# Hermes Docker Sandbox With External Ollama Provider

## 1. Goals and Non-Goals

This document defines the planned Docker sandbox boundary for Hermes while keeping Ollama as an external model provider on the host machine.

Goals:

- Define the recommended Hermes Docker sandbox architecture.
- Explain how a Hermes container connects to Ollama running on the Windows host.
- Preserve Hermes governance, approval, and command safety rules as the primary safety layer.
- Provide a docker-compose example for future implementation planning.
- Document host-side and container-side connectivity checks.

Non-goals:

- Do not implement a Dockerfile in this phase.
- Do not add a real docker-compose.yml file in this phase.
- Do not put Ollama inside the Hermes container.
- Do not modify Runtime, Governance, MCP, Dashboard, or provider code in this phase.
- Do not test Docker execution in this phase.

## 2. Recommended Architecture

Recommended layout:

```text
Windows Host
├── Ollama
│   └── http://localhost:11434
│
└── Docker Desktop
    └── Hermes Container
        └── HERMES_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Responsibilities:

- Hermes container: Agent Runtime sandbox.
- Host Ollama: Model Provider.
- Docker: execution and filesystem boundary.
- Hermes Governance: primary safety control.

Hermes should treat Ollama as an external provider, not as a process bundled into the Hermes runtime container.

## 3. Why localhost:11434 Does Not Work Inside the Container

Inside a Docker container, `localhost` means the container itself. It does not mean the Windows host.

Incorrect inside container:

```text
http://localhost:11434
```

Correct for Docker Desktop on Windows:

```text
http://host.docker.internal:11434
```

This routes the Hermes container to the Ollama service running on the host machine.

## 4. docker-compose.yml Draft

This is a documentation-only draft. Do not create this file until the Docker implementation phase.

```yaml
services:
  hermes:
    build: .
    container_name: hermes
    ports:
      - "8000:8000"
    volumes:
      - ./user_projects:/workspace/user_projects
      - ./docs:/workspace/docs
    environment:
      HERMES_WORKSPACE: /workspace
      HERMES_DEFAULT_PROVIDER: ollama
      HERMES_DEFAULT_MODEL: qwen3:14b
      HERMES_OLLAMA_BASE_URL: http://host.docker.internal:11434
      HERMES_MCP_PROVIDER: ollama
      HERMES_MCP_MODEL: qwen3:14b
      HERMES_MCP_BASE_URL: http://host.docker.internal:11434
```

The model name is an example. It must match a model available in the host Ollama installation.

## 5. Windows Docker Desktop Notes

On Windows Docker Desktop:

- Do not use `localhost:11434` from inside the container.
- Use `host.docker.internal:11434`.
- Make sure Ollama is already running on the Windows host.
- Confirm the target model is installed before starting Hermes.

Host-side quick check:

```powershell
ollama list
curl http://localhost:11434/api/tags
```

## 6. Linux Notes

On Linux, `host.docker.internal` may not exist by default. A future docker-compose.yml may need:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

After that, the container can use the same base URL:

```text
http://host.docker.internal:11434
```

## 7. Ollama Host-Side Checks

Run these commands on the host machine before starting a Hermes container:

```powershell
ollama list
curl http://localhost:11434/api/tags
```

Expected result:

- `ollama list` shows the intended model.
- `/api/tags` returns a JSON response listing available models.

If the host cannot reach Ollama, the container will not be able to reach it either.

## 8. Container Connectivity Check

After a Hermes container exists, test connectivity from inside the container:

```bash
curl http://host.docker.internal:11434/api/tags
```

Expected result:

- The command returns the same kind of model tags JSON as the host-side check.
- If it fails, debug networking before debugging Hermes provider logic.

## 9. Troubleshooting OLLAMA_HOST

If the container cannot reach host Ollama, Ollama may be bound only to `127.0.0.1`.

On Windows, set:

```powershell
setx OLLAMA_HOST "0.0.0.0:11434"
```

Then restart Ollama and test again:

```powershell
curl http://localhost:11434/api/tags
```

From inside the container:

```bash
curl http://host.docker.internal:11434/api/tags
```

Only proceed when both checks work.

## 10. Security Principles

Docker is a second-layer sandbox boundary. It must not replace Hermes governance.

Required rules:

- Do not disable GovernanceManager.
- Do not change GovernanceManager to always return `True`.
- Do not disable approval.
- Do not automatically allow shell access.
- Do not bypass command allowlists because Docker exists.
- Do not treat mounted volumes as disposable unless they are explicitly test fixtures.

Docker limits the blast radius. Hermes governance still decides whether an action is allowed.

Recommended safety model:

```text
GovernanceManager / approvals / command policy
        ↓
SafeExecutor / ConstraintValidator
        ↓
Docker filesystem and process boundary
        ↓
Mounted workspace volumes
```

## 11. Future Phases

Phase 1: Add this design document.

Phase 2: Add a Dockerfile draft for Hermes-only runtime.

Phase 3: Add a real docker-compose.yml with external Ollama provider settings.

Phase 4: Add CI or local sandbox smoke tests.

Phase 5: Define sandbox autonomy levels and L5 policy boundaries.

Each phase should preserve the same principle: Docker is additional isolation, not permission to weaken Hermes governance.
