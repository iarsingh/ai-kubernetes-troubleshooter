# ai-kubernetes-troubleshooter — interview questions and answers

[README](README.md) · [Project architecture](PROJECT_ARCHITECTURE.md)

Answers below use this repository’s files and implementation. They distinguish existing behavior from suggested extensions; source links let you verify each walkthrough.

## 1. What problem does ai-kubernetes-troubleshooter address, and what can you demonstrate?

Hypothesis from posted events. kubectl delete is refused.

I would demonstrate the linked implementation or examples and distinguish that evidence from any planned production features. Start with [`README.md`](README.md).

## 2. How is this repository organized?

- [`src/k8strouble/main.py`](src/k8strouble/main.py): Implementation or supporting configuration.
- [`src/k8strouble/ops.py`](src/k8strouble/ops.py): Implementation or supporting configuration.
- [`src/k8strouble/agent.py`](src/k8strouble/agent.py): Implementation or supporting configuration.
- [`requirements.txt`](requirements.txt): Implementation or supporting configuration.
- [`src/k8strouble/__init__.py`](src/k8strouble/__init__.py): Implementation or supporting configuration.
- [`Dockerfile`](Dockerfile): Container build/service configuration.
- [`Makefile`](Makefile): Implementation or supporting configuration.
- [`docker-compose.yml`](docker-compose.yml): Container build/service configuration.

[PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) contains the component diagram and the implementation walkthrough.

## 3. Can you walk through `run` and explain the decision it makes?

The main walkthrough here is `run(goal, payload)` in [`src/k8strouble/agent.py`](src/k8strouble/agent.py#L9).

```python
def run(goal, payload):
    if not isinstance(goal, str) or not goal.strip():
        raise InputError("goal is empty")
    if any(word in goal.lower() for word in WRITES):
        return {"refused": True, "reason": "This agent only reads or plans. It does not write.", "tools": [], "wrote": False, "applied": False}
    events = " ".join(payload.get("events") or []).lower(); result = "crashloop" if "backoff" in events else "oom" if "oom" in events else "unknown"
    return {"refused": False, "tools": TOOLS, "hypothesis": result, "wrote": False, "applied": False}
```

The implementation calls `' '.join`, `' '.join(payload.get('events') or []).lower`, `InputError`, `any`, `goal.lower`, `goal.strip`, `isinstance`, `payload.get`. In an interview, trace those calls in execution order using a fixture input.

## 4. What input validation and failure behavior are implemented?

Explicit failure paths include:

- `InputError('goal is empty')` in [`src/k8strouble/agent.py`](src/k8strouble/agent.py#L11).
- `HTTPException(status_code=422, detail=str(exc))` in [`src/k8strouble/main.py`](src/k8strouble/main.py#L19).
- `HTTPException(status_code=404, detail='workspace not found')` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L77).
- `HTTPException(status_code=404, detail='job not found')` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L100).
- `HTTPException(status_code=404, detail='job not found')` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L109).
- `HTTPException(status_code=403, detail='production apply is disabled in this lab')` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L113).

I would test both the condition that reaches each exception and the caller that translates it. An explicit raise does not mean every malformed input or dependency failure is handled.

## 5. Which test would you use to demonstrate correctness?

[`tests/test_agent.py`](tests/test_agent.py#L7) contains `test_runs_and_refuses_a_write`:

```python
def test_runs_and_refuses_a_write():
    payload = client.post("/agent/run", json={"goal": 'why is the pod failing', **{'payload': {'events': ['BackOff restarting failed container']}}}).json()
    assert payload["refused"] is False
    assert payload["applied"] is False
    assert payload["hypothesis"] == "crashloop"
    refused = client.post("/agent/run", json={"goal": 'kubectl delete pod api-0'}).json()
    assert refused["refused"] is True
```

This is a concrete regression example from the repository. Its assertions establish that case; they do not establish behavior for every input or under production load.

## 6. What HTTP interface does the code expose?

- `GET /healthz` → `healthz` in [`src/k8strouble/main.py`](src/k8strouble/main.py#L10).
- `POST /agent/run` → `post_run` in [`src/k8strouble/main.py`](src/k8strouble/main.py#L15).
- `GET /readyz` → `readyz` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L74).
- `POST /workspaces` → `create_workspace` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L80).
- `GET /workspaces` → `list_workspaces` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L98).
- `POST /workspaces/{workspace_id}/jobs` → `create_job` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L106).
- `GET /jobs/{job_id}` → `get_job` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L130).
- `POST /jobs/{job_id}/approve` → `approve_job` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py#L140).

These are literal decorators. Application/router prefixes, authentication, and middleware must be checked in the corresponding setup code.

## 7. Where does state live, and what happens with multiple workers?

Module-level containers include `TOOLS` in [`src/k8strouble/agent.py`](src/k8strouble/agent.py); `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS` in [`src/k8strouble/ops.py`](src/k8strouble/ops.py).

These containers belong to a Python process. Inspect which are constant fixtures and which are mutated. Mutable process state needs an explicit shared-storage or synchronization strategy before multiple workers can provide consistent behavior.

## 8. How would another engineer reproduce your walkthrough?

Start from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

These commands follow repository manifests; environment setup and command results still need to be checked on the target machine.

## 9. What does automation verify, and what does it not prove?

Inspect [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for triggers, permissions, and job commands. I would name the checks that those definitions run and show the latest run separately. A workflow definition alone does not establish a successful deployment, security review, or production SLO.

## 10. How would you present this project in a Forward Deployed Engineer interview?

Start with the user and operational problem described in [`README.md`](README.md). Explain one constraint that changes the implementation, show the linked code or example, and walk through a success case and a failure case. Agree on a measurable acceptance criterion before expanding the solution, and leave a handoff with data boundaries and rollback ownership. Any proposed production or business metric should be identified as a target until measured.

## 11. What is the input-to-output contract of `run`?

In [`src/k8strouble/agent.py`](src/k8strouble/agent.py#L9), `run(goal, payload)` receives the inputs. The function computes these intermediate values:

- `events = ' '.join(payload.get('events') or []).lower()`
- `result = 'crashloop' if 'backoff' in events else 'oom' if 'oom' in events else 'unknown'`

Its result is defined by:

- `{'refused': False, 'tools': TOOLS, 'hypothesis': result, 'wrote': False, 'applied': False}`
- `{'refused': True, 'reason': 'This agent only reads or plans. It does not write.', 'tools': [], 'wrote': False, 'applied': False}`

## 12. Which decision rules or boundary conditions should an interviewer challenge?

The implementation in [`src/k8strouble/agent.py`](src/k8strouble/agent.py#L9) branches on:

- `not isinstance(goal, str) or not goal.strip()`
- `any((word in goal.lower() for word in WRITES))`

A useful extension is a table-driven test that covers each condition just below, at, and above its boundary where applicable. These expressions are the current rules; changing them changes behavior and should be justified by the project’s acceptance criteria.

## 13. What does the operations plane add, and where is its limit?

[`src/k8strouble/ops.py`](src/k8strouble/ops.py) declares `GET /readyz`, `POST /workspaces`, `GET /workspaces`, `POST /workspaces/{workspace_id}/jobs`, `GET /jobs/{job_id}`, `POST /jobs/{job_id}/approve`, `GET /audit`, `GET /metrics`. Inspect the application’s `include_router` call for its URL prefix.

Its state containers are `_WORKSPACES`, `_JOBS`, `_AUDIT`, `_METRICS`. The job-approval handler defines whether a target is accepted or refused; check that branch and the associated tests instead of treating a recorded job as a successful infrastructure apply.
