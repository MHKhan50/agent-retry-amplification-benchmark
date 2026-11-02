"""Deterministic synthetic benchmark for retry amplification and duplicate effects."""
from __future__ import annotations
import csv, json, random
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
SEEDS = (13, 29, 47, 61, 89)
SCENARIOS_PER_SEED = 1200
POLICIES = ("no_retry", "naive_retry", "bounded_backoff", "idempotency_key")


def generate_scenarios(n_per_seed: int = SCENARIOS_PER_SEED, seeds=SEEDS) -> List[Dict]:
    rows = []
    operations = ("send_notification", "create_ticket", "submit_payment", "update_record")
    for seed in seeds:
        rng = random.Random(seed)
        for i in range(n_per_seed):
            # Failure count is the number of attempts that commit a side effect but
            # return a transient error before a later successful response.
            failures = rng.choices((0, 1, 2, 3, 4, 5), weights=(28, 24, 18, 14, 10, 6))[0]
            commit_before_error = rng.random() < 0.42
            rows.append({
                "seed": seed,
                "scenario_id": f"s{seed}_{i:05d}",
                "operation": operations[rng.randrange(len(operations))],
                "transient_failures": failures,
                "commit_before_error": int(commit_before_error),
                "base_latency_steps": rng.randint(1, 3),
            })
    return rows


def evaluate(s: Dict, policy: str) -> Dict:
    if policy not in POLICIES:
        raise ValueError(f"Unknown policy: {policy}")
    limits = {"no_retry": 1, "naive_retry": 5, "bounded_backoff": 3, "idempotency_key": 5}
    max_attempts = limits[policy]
    attempts = min(s["transient_failures"] + 1, max_attempts)
    success = int(s["transient_failures"] < max_attempts)
    failed_attempts = min(s["transient_failures"], max_attempts)
    # Each failed request may have committed despite its error response.
    raw_effects = failed_attempts * int(s["commit_before_error"]) + success
    # Idempotency is an idealised server-side deduplication contract, not a client trick.
    effects = min(raw_effects, 1) if policy == "idempotency_key" else raw_effects
    duplicate_effects = max(0, effects - 1)
    if policy == "no_retry":
        backoff = 0
    elif policy == "naive_retry":
        backoff = max(0, attempts - 1)
    else:
        backoff = sum(2 ** k for k in range(max(0, attempts - 1)))
    latency = attempts * int(s["base_latency_steps"]) + backoff
    return {
        "seed": s["seed"], "scenario_id": s["scenario_id"], "policy": policy,
        "operation": s["operation"], "transient_failures": s["transient_failures"],
        "commit_before_error": s["commit_before_error"], "attempts": attempts,
        "task_success": success, "side_effect_count": effects,
        "duplicate_side_effects": duplicate_effects,
        "duplicate_side_effect_episode": int(duplicate_effects > 0),
        "latency_steps": latency,
        "retry_amplification": attempts - 1,
    }


def aggregate(rows: List[Dict]) -> List[Dict]:
    summaries = []
    for policy in POLICIES:
        group = [r for r in rows if r["policy"] == policy]
        n = len(group)
        summaries.append({
            "policy": policy,
            "episodes": n,
            "task_success_rate": round(sum(r["task_success"] for r in group) / n, 6),
            "mean_attempts": round(sum(r["attempts"] for r in group) / n, 6),
            "mean_retry_amplification": round(sum(r["retry_amplification"] for r in group) / n, 6),
            "duplicate_side_effect_episode_rate": round(sum(r["duplicate_side_effect_episode"] for r in group) / n, 6),
            "mean_duplicate_side_effects": round(sum(r["duplicate_side_effects"] for r in group) / n, 6),
            "mean_latency_steps": round(sum(r["latency_steps"] for r in group) / n, 6),
        })
    return summaries


def write_csv(path: Path, rows: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def run(n_per_seed: int = SCENARIOS_PER_SEED, seeds=SEEDS) -> Dict:
    scenarios = generate_scenarios(n_per_seed, seeds)
    episodes = [evaluate(s, p) for s in scenarios for p in POLICIES]
    summaries = aggregate(episodes)
    write_csv(DATA / "scenarios.csv", scenarios)
    write_csv(OUT / "episode_results.csv", episodes)
    write_csv(OUT / "policy_summary.csv", summaries)
    result = {
        "benchmark": "Agent Retry Amplification Benchmark (ARAM)",
        "version": "0.1.0", "synthetic_scenarios": len(scenarios),
        "seeds": list(seeds), "policies": list(POLICIES),
        "policy_evaluations": len(episodes), "metrics": summaries,
        "interpretation_warning": "Deterministic synthetic simulator results only; not real-world agent or payment-system measurements.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
