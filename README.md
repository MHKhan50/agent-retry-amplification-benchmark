# Agent Retry Amplification Benchmark (ARAM)

**Version:** 0.1.0
**Author:** Muzammal Hussain
**Date:** 2 November 2026
**Status:** Reproducible synthetic baseline

## Research question
When a tool call commits a side effect but its response is lost or reports a transient failure, how do retry policies affect task completion, duplicate side effects, request amplification and latency?

## Policies
- `no_retry`: one attempt only.
- `naive_retry`: retries up to five attempts with a fixed one-step delay.
- `bounded_backoff`: at most three attempts with exponential backoff.
- `idempotency_key`: up to five attempts with an idealised server-side idempotency contract that deduplicates repeated effects.

## Run
Requires Python 3.9+; standard library only.

```bash
python3 run_benchmark.py
python3 -m unittest discover -s tests -v
```

Default run: 6,000 synthetic scenarios across five seeds and 24,000 policy evaluations.

## Metrics
Task success rate, mean attempts, mean retry amplification, duplicate-side-effect episode rate, mean duplicate side effects, and mean latency steps.

## Important interpretation boundary
This is a deterministic, stylised simulator. It is not a test of deployed LLM agents, real payment APIs, production retry middleware, distributed databases, or actual external side effects. The idempotency policy assumes an ideal server-side deduplication contract; real systems must define key scope, retention, payload matching, concurrency behaviour and failure recovery. Results are not safety or reliability guarantees.
