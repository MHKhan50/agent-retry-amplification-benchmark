# Dataset Card: ARAM v0.1.0

- **Dataset:** synthetic tool-operation retry scenarios.
- **Rows:** 6,000 by default.
- **Seeds:** 13, 29, 47, 61, 89; 1,200 scenarios per seed.
- **Fields:** seed, scenario_id, operation, transient_failures, commit_before_error, base_latency_steps.
- **Operations:** send_notification, create_ticket, submit_payment, update_record (all fictional labels).
- **Generation:** Python standard-library pseudorandom generator with fixed seeds.
- **Labels:** number of transient failures and whether a failed attempt commits before its error response are generated scenario attributes.
- **Privacy:** no personal data; all records are synthetic.
- **Known limitations:** stylised independent scenarios; no network, concurrency, real API semantics, transaction isolation, rate limiting or actual money movement.
