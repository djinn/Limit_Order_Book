
# Limit Order Book Simulator with Inventory-Aware Market Making

Markets are not predictions.
They are systems under pressure.

This project builds a limit order book from first principles and then injects a market-making agent into it. The goal is not to forecast price. The goal is to understand how price *emerges* from order flow, and how profit *emerges* from managing risk inside that flow.

---

## What This Is

A multi-iteration simulation of a limit order book (LOB) where:

* Order arrivals follow stochastic processes
* Price evolves endogenously from liquidity imbalances
* A market-making agent interacts with the book
* Inventory, execution, and quoting are tightly coupled

This is not a backtest.
This is a controlled environment to study microstructure.

---

## System Overview

At its core, the system has three moving parts:

1. **Order Flow Engine**
   Generates limit and market orders using Poisson processes.

2. **Limit Order Book**
   Tracks bid/ask queues and updates price when liquidity is exhausted.

3. **Market Maker Agent**
   Quotes bid/ask, manages inventory, and accumulates PnL.

Each iteration increases the coupling between these parts.

---

## Iterations

### 1. Endogenous Price Formation

* Fixed initial bid/ask depths
* Orders arrive via Poisson processes (λ·Δt approximation)
* Price moves one tick when either side of the book is depleted
* Book resets after each move

**Insight:**
Price is a consequence of imbalance, not an input.

---

### 2. Introducing a Market Maker

* Agent quotes at best bid and ask
* Earns spread when filled
* Tracks:

  * Inventory
  * Cash
  * Mark-to-market wealth

**Trade-off introduced:**
Spread capture vs inventory risk

Profit is no longer guaranteed. Path matters.

---

### 3. Inventory-Aware Quoting

Quotes are no longer symmetric.

A reservation price is introduced:

[
r = S - \gamma q
]

Where:

* ( S ): Midpoint price
* ( q ): Current inventory
* ( \gamma ): Risk aversion parameter

**Behavior:**

* Low γ → aggressive quoting → higher fills → larger inventory swings
* High γ → conservative quoting → fewer fills → tighter inventory

**Insight:**
Inventory is not a constraint. It is a control signal.

---

### 4. Quote-Dependent Execution

Execution probability is no longer fixed.

It depends on quote quality using a logistic model:

* Δ = distance from best quote
* k = sensitivity parameter

Better quotes → higher fill probability

**Result:**

Inventory → affects quotes
Quotes → affect fills
Fills → affect inventory

A closed feedback loop.

**Insight:**
Execution is not guaranteed. It is negotiated.

---

## What This Teaches

This system makes a few things visible:

* Spread is not free money
* Inventory risk is unavoidable
* Execution quality shapes strategy viability
* Microstructure is a feedback system, not a pipeline

If your model ignores one of these, it will break in production.

---

## Running Experiments

Typical experiments involve:

* Sweeping γ (risk aversion) across multiple seeds
* Comparing wealth trajectories
* Measuring:

  * Inventory variance
  * Fill rates
  * PnL stability

No single parameter dominates.
Each choice trades one risk for another.

---

## Where This Breaks

This is a model. It is meant to fail.

Known gaps:

* No queue position modeling (execution priority ignored)
* No clustered order flow (Poisson ≠ reality)
* No informed flow / adverse selection
* No latency or market impact
* No calibration to real-world data

If you trust this blindly, you will lose money.

---

## Next Steps

The roadmap focuses on making the system harder to game:

### 1. Queue Position Modeling

Simulate time priority within price levels.

### 2. Hawkes Processes

Replace independent arrivals with self-exciting flows.

### 3. Adverse Selection

Introduce informed traders whose flow predicts price moves.

### 4. Calibration

Fit parameters to real LOB data.

---

## Philosophy

Most models optimize parameters.
This one exposes constraints.

* Inventory is not optional
* Execution is not guaranteed
* Risk is not removable

The goal is not to eliminate these forces.
The goal is to survive them.

---

## Why This Matters

If you want to trade:

Don’t start with signals.
Start with the machine that turns signals into PnL.

Because the edge is rarely in predicting price.
It’s in understanding what happens *after* you’re right.

---

## Open to Contributions

This is an evolving system.

If you’ve built:

* Better execution models
* Real data calibration pipelines
* Queue-aware simulators

Fork it. Break it. Improve it.

---
