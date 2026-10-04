TOOLS = ["read_events", "hypothesize"]
WRITES = ("delete", "drain", "kubectl apply",)


class InputError(ValueError):
    pass


def run(goal, payload):
    if not isinstance(goal, str) or not goal.strip():
        raise InputError("goal is empty")
    if any(word in goal.lower() for word in WRITES):
        return {"refused": True, "reason": "This agent only reads or plans. It does not write.", "tools": [], "wrote": False, "applied": False}
    events = " ".join(payload.get("events") or []).lower(); result = "crashloop" if "backoff" in events else "oom" if "oom" in events else "unknown"
    return {"refused": False, "tools": TOOLS, "hypothesis": result, "wrote": False, "applied": False}
