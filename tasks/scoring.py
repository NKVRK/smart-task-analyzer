from datetime import date, datetime
from math import exp
from collections import defaultdict, deque

# default weight presets for strategies
STRATEGY_PRESETS = {
    "smart_balance": {"urgency": 0.35, "importance": 0.30, "dependencies": 0.20, "effort": 0.15},
    "deadline_driven": {"urgency": 0.6, "importance": 0.2, "dependencies": 0.1, "effort": 0.1},
    "high_impact": {"urgency": 0.2, "importance": 0.6, "dependencies": 0.15, "effort": 0.05},
    "fastest_wins": {"urgency": 0.15, "importance": 0.15, "dependencies": 0.1, "effort": 0.6},
}

MAX_PAST_DUE_DAYS_FOR_BOOST = 30  # cap the boost for very old tasks


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except Exception:
        # try common format
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None


def detect_cycles(tasks):
    """
    tasks: list of dicts with 'id' and 'dependencies' like ['t1','t2']
    Returns list of cycles (each cycle is list of task ids)
    """
    # build graph
    graph = defaultdict(list)
    ids = set()
    for t in tasks:
        tid = t.get("id")
        ids.add(tid)
    for t in tasks:
        tid = t.get("id")
        deps = t.get("dependencies") or []
        for d in deps:
            # only consider dependency edges among provided tasks
            if d in ids:
                graph[d].append(tid)  # edge d -> tid (d must be done before tid)
    # standard cycle detection (DFS)
    visited = {}
    stack = []
    cycles = []

    def dfs(node, path):
        if node in visited:
            return visited[node]  # 0 ongoing, 1 done
        visited[node] = 0
        path.append(node)
        for neigh in graph.get(node, []):
            if visited.get(neigh, None) == 0:
                # found cycle - collect cycle nodes
                try:
                    idx = path.index(neigh)
                    cycles.append(path[idx:] + [neigh])
                except ValueError:
                    pass
            elif visited.get(neigh, None) is None:
                dfs(neigh, path)
        visited[node] = 1
        path.pop()

    for node in ids:
        if visited.get(node, None) is None:
            dfs(node, [])
    # normalize cycles (unique)
    unique = []
    seen = set()
    for c in cycles:
        key = tuple(c)
        if key not in seen:
            unique.append(list(dict.fromkeys(c)))  # remove duplicates, preserve order
            seen.add(key)
    return unique


# Overwrite the existing calculate_scores function with this version
def calculate_scores(tasks, strategy="smart_balance", custom_weights=None):
    """
    Input: tasks: list of dicts. Each task should include:
      id, title, due_date (YYYY-MM-DD or None), importance (1-10), estimated_hours (float/int), dependencies (list)
    Returns: dict with 'analyzed_tasks' and 'meta'
    """
    today = date.today()
    # container for validation/warnings
    warnings_map = defaultdict(list)

    # validate and normalize tasks
    normalized = []
    for i, t in enumerate(tasks):
        nt = dict(t)  # shallow copy
        nt.setdefault("id", f"t{ i+1 }")
        nt.setdefault("title", nt["id"])

        # importance normalization with warning if corrected
        orig_imp = nt.get("importance", None)
        nt.setdefault("importance", 5)
        try:
            nt["importance"] = max(1, min(10, int(nt.get("importance", 5))))
            if orig_imp is not None:
                try:
                    # if original wasn't an integer or out of range, record
                    if int(orig_imp) != nt["importance"]:
                        warnings_map[nt["id"]].append(
                            f"importance value '{orig_imp}' normalized to {nt['importance']}"
                        )
                except Exception:
                    # orig_imp wasn't int-convertible
                    warnings_map[nt["id"]].append(
                        f"importance value '{orig_imp}' is invalid and defaulted to {nt['importance']}"
                    )
        except Exception:
            nt["importance"] = 5
            warnings_map[nt["id"]].append(
                f"importance value '{orig_imp}' is invalid and defaulted to 5"
            )

        # estimated_hours normalization with warning if corrected
        orig_hours = nt.get("estimated_hours", None)
        try:
            nt["estimated_hours"] = float(nt.get("estimated_hours", 2.0))
            if nt["estimated_hours"] < 0:
                nt["estimated_hours"] = 2.0
                warnings_map[nt["id"]].append(
                    f"estimated_hours '{orig_hours}' was negative and set to 2.0"
                )
            else:
                # if provided but had weird type (e.g. string "3h"), conversion may have thrown above
                if orig_hours is not None and float(orig_hours) != nt["estimated_hours"]:
                    # only warn if original differs after conversion (non-critical)
                    # (but avoid spamming when orig_hours is numeric matching)
                    pass
        except Exception:
            nt["estimated_hours"] = 2.0
            warnings_map[nt["id"]].append(
                f"estimated_hours value '{orig_hours}' is invalid and defaulted to 2.0"
            )

        # parse dates
        nt["due_date_parsed"] = _parse_date(nt.get("due_date"))

        # dependencies: coerce to list and warn if not list
        deps = nt.get("dependencies") or []
        if not isinstance(deps, list):
            # coerce strings like "t1,t2" -> list
            try:
                # if it's a comma-separated string
                if isinstance(deps, str):
                    deps = [s.strip() for s in deps.split(",") if s.strip()]
                    warnings_map[nt["id"]].append(
                        f"dependencies value was a string and coerced to list: {deps}"
                    )
                else:
                    deps = list(deps)
                    warnings_map[nt["id"]].append(
                        "dependencies value coerced to list"
                    )
            except Exception:
                deps = []
                warnings_map[nt["id"]].append(
                    "dependencies value invalid; treated as empty list"
                )
        nt["dependencies"] = deps

        normalized.append(nt)

    # build id set (for unknown dependency detection)
    id_set = {t["id"] for t in normalized}

    # now detect unknown dependency references and add warnings
    for t in normalized:
        for d in t.get("dependencies", []):
            if d not in id_set:
                warnings_map[t["id"]].append(f"dependency '{d}' not found in provided tasks")

    # ... the rest of your original scoring logic follows unchanged ...
    # compute raw sub-scores
    importance_scores = {}
    urgency_scores = {}
    effort_raw = {}
    dependencies_outdegree = defaultdict(int)

    # compute dependencies out-degree (how many depend on this task)
    for t in normalized:
        for d in t["dependencies"]:
            if d in id_set:
                dependencies_outdegree[d] += 1

    for t in normalized:
        tid = t["id"]
        # importance
        importance_scores[tid] = t["importance"] / 10.0

        # urgency
        dd = t["due_date_parsed"]
        if dd is None:
            urgency_scores[tid] = 0.0
        else:
            days = (dd - today).days
            if days < 0:
                urgency_scores[tid] = min(
                    1.0,
                    1.0 + min(-days, MAX_PAST_DUE_DAYS_FOR_BOOST) / MAX_PAST_DUE_DAYS_FOR_BOOST,
                )
            else:
                max_horizon = 60.0
                urgency_scores[tid] = max(0.0, 1.0 - (days / max_horizon))
                urgency_scores[tid] = min(1.0, urgency_scores[tid])

        # effort raw
        effort_raw[tid] = 1.0 / (1.0 + t["estimated_hours"])

    # normalize effort and dependencies to 0..1
    min_e = min(effort_raw.values()) if effort_raw else 0.0
    max_e = max(effort_raw.values()) if effort_raw else 1.0
    effort_scores = {}
    if max_e - min_e < 1e-9:
        for k, v in effort_raw.items():
            effort_scores[k] = 0.5
    else:
        for k, v in effort_raw.items():
            effort_scores[k] = (v - min_e) / (max_e - min_e)

    if dependencies_outdegree:
        min_d = min(dependencies_outdegree.values()) if dependencies_outdegree else 0
        max_d = max(dependencies_outdegree.values()) if dependencies_outdegree else 1
    else:
        min_d = 0
        max_d = 1
    dependencies_scores = {}
    for t in normalized:
        v = dependencies_outdegree.get(t["id"], 0)
        if max_d - min_d < 1e-9:
            dependencies_scores[t["id"]] = 0.0
        else:
            dependencies_scores[t["id"]] = (v - min_d) / (max_d - min_d)

    # pick weights
    weights = custom_weights or STRATEGY_PRESETS.get(strategy, STRATEGY_PRESETS["smart_balance"])
    wsum = sum(weights.values())
    if abs(wsum - 1.0) > 1e-6:
        weights = {k: v / wsum for k, v in weights.items()}

    # detect cycles (existing code)
    cycles = detect_cycles(normalized)

    # build cycle metadata + per-task membership
    cycle_memberships = defaultdict(list)
    cycle_list = []
    if cycles:
        for idx, c in enumerate(cycles, start=1):
            cycle_list.append(
                {
                    "cycle_id": idx,
                    "tasks": c,
                    "message": "circular dependency detected",
                }
            )
            for tid in set(c):
                cycle_memberships[tid].append(idx)

    if cycle_list:
        meta = {"cycles": cycle_list, "strategy_used": strategy}
    else:
        meta = {"cycles": [], "strategy_used": strategy}

    # also include warnings summary in meta
    flat_warnings = []
    for tid, msgs in warnings_map.items():
        if msgs:
            flat_warnings.append({"task_id": tid, "warnings": msgs})
    if flat_warnings:
        meta["warnings_summary"] = flat_warnings

    # assemble final output (preserve existing output shape)
    out = []
    for t in normalized:
        tid = t["id"]
        s_imp = importance_scores[tid]
        s_urg = min(1.0, urgency_scores[tid])
        s_eff = effort_scores[tid]
        s_dep = dependencies_scores[tid]

        score = (
            weights.get("urgency", 0) * s_urg
            + weights.get("importance", 0) * s_imp
            + weights.get("dependencies", 0) * s_dep
            + weights.get("effort", 0) * s_eff
        )

        # tiering
        tier = "Low"
        if score >= 0.75:
            tier = "High"
        elif score >= 0.45:
            tier = "Medium"

        # human readable explanation (same as before)
        reasons = []
        if t["due_date_parsed"]:
            days = (t["due_date_parsed"] - today).days
            if days < 0:
                reasons.append(f"Past due by {-days} day(s) → urgency boosted")
            elif days <= 3:
                reasons.append(f"Due in {days} day(s) → urgent")
            else:
                reasons.append(f"Due in {days} day(s)")
        else:
            reasons.append("No due date")

        if t["dependencies"]:
            reasons.append(f"Blocks {dependencies_outdegree.get(tid, 0)} task(s)")
        if t["estimated_hours"] <= 2:
            reasons.append("Quick win (low estimated hours)")
        if t["importance"] >= 8:
            reasons.append("High importance")

        explanation = "; ".join(reasons)

        # collect warnings: cycles + normalized-input warnings
        warnings = []
        if tid in cycle_memberships:
            cycle_ids = cycle_memberships[tid]
            if len(cycle_ids) == 1:
                warnings.append(
                    f"Task is part of a circular dependency (cycle #{cycle_ids[0]})."
                )
            else:
                warnings.append(
                    f"Task is part of multiple circular dependencies (cycles {', '.join(map(str, cycle_ids))})."
                )
        # append other warnings from normalization
        warnings.extend(warnings_map.get(tid, []))

        out.append(
            {
                "id": tid,
                "title": t.get("title"),
                "due_date": t.get("due_date"),
                "estimated_hours": t.get("estimated_hours"),
                "importance": t.get("importance"),
                "dependencies": t.get("dependencies"),
                "score": round(score, 4),
                "tier": tier,
                "score_breakdown": {
                    "urgency": round(s_urg, 4),
                    "importance": round(s_imp, 4),
                    "effort": round(s_eff, 4),
                    "dependencies": round(s_dep, 4),
                    "weights": {k: round(v, 4) for k, v in weights.items()},
                },
                "explanation": explanation,
                "warnings": warnings,
            }
        )

    out_sorted = sorted(
        out,
        key=lambda x: (-x["score"], -x["importance"], x["estimated_hours"]),
    )
    return {"analyzed_tasks": out_sorted, "meta": meta}
