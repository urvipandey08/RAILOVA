## Project Overview

RAILOVA (Railway Operations & Virtual Analytics) is an independently developed railway ticket-counter simulation platform designed to model and analyse passenger flow, queue dynamics, and service efficiency.

Built around the M/M/c queuing theory framework, the system simulates multiple parallel ticket counters operating with a centralized First-Come, First-Served (FCFS) queue. It incorporates two behavioural mechanisms:

1. **Passenger Balking:** Models passengers who decide not to join a queue when its length exceeds an acceptable threshold.
2. **Passenger Reneging:** Models passengers who abandon the queue after waiting longer than their individual patience limit.

The platform supports normal, peak-hour, and overloaded operating scenarios, allowing users to examine how changing arrival rates, service rates, and queue conditions affect overall system performance.

It also provides interactive simulation visualisation, performance analytics, structured event logs, CSV exports, and comparisons between empirical simulation results and theoretical Erlang-C calculations.
