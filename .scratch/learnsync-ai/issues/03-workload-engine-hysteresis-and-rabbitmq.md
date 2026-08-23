# 03: Rolling Workload Engine W(t), Hysteresis State Machine & RabbitMQ Publisher

**What to build:**
Implement the continuous rolling Workload Score $W(t) \in [0.0, 1.0]$ computation engine over a 3-day lookahead window based on deadline density, event weights, and calendar proximity. Couple the calculation with a Schmitt-trigger Hysteresis controller (Free Mode $\le 0.55$, Dead-Band $0.55–0.70$, Busy Mode $> 0.70$) that persists transition logs in Supabase and publishes `workload.spike.detected` events to RabbitMQ.

**Blocked by:**
- 01: Supabase Backend Schema & Folder-Scoped Vector RPC Initialization

**Status:** ready-for-agent

- [ ] Workload engine implements rolling 3-day hyperbolic decay calculation: $W(t) = \min(1.0, \sum w_e / (\max(0.25, d_e(t)) \cdot \Gamma))$.
- [ ] Schmitt-trigger hysteresis state machine prevents mode oscillation in the $0.55 < W(t) \le 0.70$ dead-band.
- [ ] Recomputes and logs $W(t)$ and active mode transitions into `workload_logs` in Supabase.
- [ ] Connects to RabbitMQ and broadcasts `workload.spike.detected` when $W(t)$ crosses $> 0.70$.
- [ ] Unit & integration tests verify exact state retention across boundary score fluctuations.
