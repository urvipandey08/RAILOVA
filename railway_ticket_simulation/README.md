# RAILOVA
### Railway Operations & Virtual Analytics

**An Interactive Railway Queue Simulation & Performance Analytics Platform**

RAILOVA is an independently developed, web-based railway ticket-counter simulation platform designed to model passenger flow, queue dynamics, and service efficiency. Built around the **M/M/c queuing theory model**, it explores how passenger arrivals, service rates, and queue conditions influence the performance of a multi-counter railway ticketing system.

The platform incorporates passenger balking and reneging, interactive simulation visualisations, performance analytics, and comparative analysis across different operating conditions.

---

## Overview

Railway ticket counters experience changing passenger arrival rates throughout the day. During peak hours, increasing demand can lead to longer queues, extended waiting times, and inefficient service utilisation.

RAILOVA provides a simulated environment to study these conditions and understand how different operational parameters affect overall system performance.

The system models multiple parallel ticket counters connected to a centralized First-Come, First-Served (FCFS) queue, allowing users to explore passenger behaviour and analyse queue performance under different scenarios.

## Key Features

- **Interactive Web Interface:** Explore railway ticket-counter operations through a browser-accessible simulation interface.
- **Multi-Counter Simulation:** Models multiple ticket counters operating simultaneously with a centralized queue.
- **FCFS Queue Management:** Implements First-Come, First-Served scheduling.
- **Passenger Balking:** Simulates passengers choosing not to join a queue when congestion exceeds acceptable limits.
- **Passenger Reneging:** Models passengers abandoning the queue after exceeding their individual waiting tolerance.
- **Live Queue Visualisation:** Displays passenger movement, queue formation, and counter activity.
- **Performance Analytics:** Evaluates waiting times, queue lengths, passenger outcomes, and counter utilisation.
- **Scenario Comparison:** Examines system behaviour under normal, peak-hour, and overloaded conditions.
- **Data Export:** Supports CSV-based extraction of simulation results for further analysis.

## Simulation Model

RAILOVA uses the **M/M/c queuing model**, where:

| Parameter | Description |
|---|---|
| M | Markovian (Poisson) passenger arrival process |
| M | Exponential service-time distribution |
| c | Number of parallel service counters |

The system operates with a centralized FIFO queue, where passengers are assigned to the next available counter.

### Mathematical Formulation

**1. Traffic Intensity**

Traffic intensity measures the proportion of available service capacity being utilised.

\[
\rho = \frac{\lambda}{c\mu}
\]

Where:
- \(\lambda\) = Average passenger arrival rate
- \(\mu\) = Average service rate per counter
- \(c\) = Number of service counters

**2. Passenger Balking**

Balking occurs when an arriving passenger decides not to enter the queue based on its current length.

The model uses two queue thresholds:

- Below the lower threshold: No balking.
- Between the thresholds: Balking probability increases linearly.
- At or above the maximum threshold: All arriving passengers balk.

**3. Passenger Reneging**

Reneging occurs when a passenger leaves the queue after waiting longer than their assigned patience limit.

The passenger's waiting duration is determined by the earlier of counter availability and their patience deadline.

**4. Erlang-C Analysis**

The theoretical Erlang-C model provides a baseline for evaluating waiting probability, expected queue length, and average waiting time in a stable M/M/c system without abandonment.

Simulation results can be compared against these theoretical values to understand differences between ideal queueing assumptions and behavioural extensions.

---

## Simulation Scenarios

The platform supports three operating conditions:

| Scenario | Arrival Rate | Traffic Intensity | Operating Condition |
|---|---:|---:|---|
| Normal | 0.60 passengers/min | 66.67% | Stable |
| Peak Hour | 0.80 passengers/min | 88.89% | High congestion |
| Overloaded | 1.00 passengers/min | 111.11% | Overloaded |

These scenarios help examine how increasing passenger demand affects queue formation, waiting times, counter utilisation, and passenger abandonment.

*The traffic intensity values assume three counters, each serving 0.30 passengers per minute.*

## Performance Metrics

RAILOVA evaluates system performance through several operational indicators:

- Total passenger arrivals
- Passengers successfully served
- Passengers who balk or renege
- Average passenger waiting time
- Queue length and system population
- Counter utilisation
- Service completion and throughput
- Passenger outcome distribution

These metrics provide a quantitative understanding of the relationship between passenger demand and available service capacity.

## Technology Stack

The project documentation covers the following technologies:

| Technology | Application |
|---|---|
| HTML & CSS | Web interface and presentation |
| JavaScript | Browser-based simulation interactions |
| Chart.js | Interactive analytical visualisations |
| Python | Simulation and analytical processing |
| SimPy | Discrete-event simulation |
| NumPy | Numerical computation |
| Pandas | Data processing and CSV exports |
| Matplotlib | Analytical plotting |
| Seaborn | Statistical visualisation |

## Project Structure

The repository contains the `railway_ticket_simulation` project directory, which holds the simulation implementation and associated documentation.

## Getting Started

RAILOVA is designed to make railway queue simulation accessible through a web interface.

Users can explore different passenger arrival conditions, observe queue behaviour, examine counter utilisation, and evaluate performance metrics without needing to understand the underlying simulation code.

For developers interested in the simulation implementation, the repository also documents its mathematical formulation, behavioural models, analytical methods, and supporting technologies.

## Project Objectives

1. Model passenger arrivals and service operations in a multi-counter railway ticketing environment.
2. Understand the impact of increasing passenger demand on queue performance.
3. Analyse passenger balking and reneging behaviour.
4. Evaluate counter utilisation and service efficiency.
5. Compare simulated performance with theoretical queueing models.
6. Present complex queueing concepts through an accessible interactive web platform.

---

## About RAILOVA

RAILOVA explores the intersection of **queueing theory, discrete-event simulation, behavioural modelling, and web-based data visualisation**.

It aims to provide an interactive way to understand how service systems behave under changing demand and how operational performance can be measured through simulation and analytical modelling.

**RAILOVA — Modelling Queues. Analysing Operations. Understanding Efficiency.**
