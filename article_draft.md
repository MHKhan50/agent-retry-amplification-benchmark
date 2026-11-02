# Agent Retry Amplification: when a failed tool response can repeat a successful side effect

**By Muzammal Hussain · 2 November 2026**

## Abstract
A tool request can commit an operation while its response is lost or reports a transient failure. An agent that retries without an idempotency contract may repeat the side effect. The Agent Retry Amplification Benchmark (ARAM) is a deterministic synthetic simulator comparing no-retry, naive-retry, bounded-backoff and idealised idempotency-key policies across 6,000 scenarios and 24,000 policy evaluations. It measures task completion, attempts, retry amplification, duplicate side effects and modeled latency. This is a reproducible engineering baseline, not a measurement of deployed agents or real APIs.

## Research question
How do retry policies trade off task completion, duplicate side effects, request amplification and latency when a failed response may follow a committed operation?

## Method
Each synthetic scenario specifies an operation label, number of transient failures, whether a failed attempt commits before returning an error, and base latency. Four policies are evaluated against the same scenarios. `no_retry` makes one attempt; `naive_retry` permits up to five attempts with fixed delay; `bounded_backoff` permits at most three attempts with exponential delay; `idempotency_key` permits up to five attempts while assuming an ideal server-side deduplication contract.

The default run uses five fixed seeds (13, 29, 47, 61 and 89), with 1,200 scenarios per seed. Every scenario is evaluated under all four policies.

## Results

| Policy | Task success rate | Mean attempts | Mean retry amplification | Duplicate-side-effect episode rate | Mean duplicate side effects | Mean latency steps |
|---|---:|---:|---:|---:|---:|---:|
| No retry | 29.13% | 1.0000 | 0.0000 | 0.00% | 0.0000 | 2.0063 |
| Naive retry | 94.32% | 2.6168 | 1.6168 | 30.27% | 0.6783 | 6.8792 |
| Bounded backoff | 71.40% | 2.1763 | 1.1763 | 30.27% | 0.4987 | 6.0162 |
| Idempotency key | 94.32% | 2.6168 | 1.6168 | 0.00% | 0.0000 | 9.2863 |

The idempotency-key policy matched naive retry's task success rate in this simulator while eliminating modeled duplicate side effects. It also had the highest modeled latency because the policy uses exponential backoff. Naive retry achieved high task completion but had duplicate side effects in 30.27% of episodes. Bounded backoff reduced the mean number of duplicate effects relative to naive retry, but did not reduce the proportion of episodes with at least one duplicate in this generated workload. No retry avoided repeated effects but completed only 29.13% of tasks.

## Interpretation
The key distinction is between a failed response and a failed operation. If an operation commits but the response is lost, retrying the request can repeat the operation unless the receiving service provides a reliable deduplication mechanism. Backoff controls request timing and load; by itself, it does not guarantee exactly-once side effects. The idealised idempotency policy demonstrates the potential value of server-side deduplication under the assumptions encoded here, not a universal exactly-once guarantee.

## Limitations
The simulator does not implement real network failures, distributed concurrency, API-specific idempotency semantics, rate limits, transaction isolation, compensation, or production agents. The idempotency policy assumes a perfect server-side key contract. Results depend on the synthetic failure distribution and policy rules. A next-stage study should use controlled fault injection against sandbox APIs and test key scope, retention, payload mismatch, concurrent requests and recovery after partial failure.

## Reproduction
Run `python3 run_benchmark.py` and `python3 -m unittest discover -s tests -v` with Python 3.9+. The repository includes the generated scenario CSV, episode-level policy outputs, summary JSON, dataset card and tests.
