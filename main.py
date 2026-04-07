"""
Poisson Limit Order Book — demo.

Run:
    python main.py
"""

import random

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from lob import simulate

# ------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------

LAMBDAS = {
    "buy_market_order":  1.5,   # lifts the ask → price ↑ pressure
    "sell_market_order": 1.5,   # hits the bid  → price ↓ pressure
    "buy_limit_order":   2.0,   # adds to bid queue
    "sell_limit_order":  2.0,   # adds to ask queue
    "cancel_bid":        1.8,   # removes from bid queue
    "cancel_ask":        1.8,   # removes from ask queue
}

DT      = 0.005   # time step  (Λ * dt = 10.6 * 0.005 = 0.053 << 1)
N_STEPS = 10_000
P_FILL  = 0.5     # probability MM is filled on each market order (1.0 = always)
SEED    = random.randint(0, 2**31 - 1)

# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------

print(f"Running Poisson LOB simulation  (seed={SEED})...")
result = simulate(
    lambdas=LAMBDAS,
    dt=DT,
    n_steps=N_STEPS,
    bid_price=9999,
    ask_price=10001,
    bid_size=5,
    ask_size=5,
    tick_size=1,
    default_depth=5,
    p_fill=P_FILL,
    seed=SEED,
)

# Unpack into arrays
times       = np.array([s.time      for s in result.snapshots])
mids        = np.array([s.mid_price for s in result.snapshots])
inventories = np.array([s.inventory for s in result.snapshots])
cashes      = np.array([s.cash      for s in result.snapshots])
wealths     = np.array([s.wealth    for s in result.snapshots])
rel_mids    = mids - mids[0]   # price movement relative to start

# ------------------------------------------------------------------
# Summary + diagnostics
# ------------------------------------------------------------------

price_changes = int(np.sum(np.diff(mids) != 0))
print(f"  Steps simulated : {N_STEPS:,}")
print(f"  Total time      : {times[-1]:.1f}")
print(f"  Mid start / end : {mids[0]:.1f} / {mids[-1]:.1f}")
print(f"  Mid std         : {mids.std():.3f}")
print(f"  Price moves     : {price_changes}")
print(f"  Spread          : always {result.snapshots[0].spread} (constant)")
print(f"  p_fill          : {P_FILL}")
print(f"\nMM summary:")
print(f"  Final inventory : {inventories[-1]}")
print(f"  Min  inventory  : {inventories.min()}")
print(f"  Max  inventory  : {inventories.max()}")
print(f"  Final cash      : {cashes[-1]:.1f}")
print(f"  Final wealth    : {wealths[-1]:.1f}")
print(f"  Bid fills       : {result.bid_fills}")
print(f"  Ask fills       : {result.ask_fills}")
print(f"  Fill imbalance  : {result.bid_fills - result.ask_fills}")
print(f"  Inventory/fills : {inventories[-1]} / ({result.bid_fills + result.ask_fills})")

result.print_diagnostics(LAMBDAS, DT)

# ------------------------------------------------------------------
# Plot
# ------------------------------------------------------------------

fig = plt.figure(figsize=(11, 13))
gs = gridspec.GridSpec(4, 1, figure=fig, hspace=0.50)

# Panel 1: relative mid-price
ax1 = fig.add_subplot(gs[0])
ax1.plot(times, rel_mids, color="steelblue", lw=1, label="mid price − mid₀")
ax1.axhline(0, color="gray", lw=0.5, ls="--")
ax1.set_title("Mid-price change from start", fontsize=12)
ax1.set_xlabel("time")
ax1.set_ylabel("price change (ticks)")
ax1.legend(fontsize=9)
ax1.grid(True, ls="--", alpha=0.4)

# Panel 2: cash (realized P&L only, no inventory mark)
ax2 = fig.add_subplot(gs[1])
ax2.plot(times, cashes, color="#9C27B0", lw=1, label="cash (realized)")
ax2.axhline(0, color="gray", lw=0.5, ls="--")
ax2.set_title("Cumulative cash from executions", fontsize=12)
ax2.set_xlabel("time")
ax2.set_ylabel("cash")
ax2.legend(fontsize=9)
ax2.grid(True, ls="--", alpha=0.4)

# Panel 3: market maker wealth
ax3 = fig.add_subplot(gs[2])
ax3.plot(times, wealths, color="#4CAF50", lw=1, label="wealth (cash + inv × mid)")
ax3.axhline(0, color="gray", lw=0.5, ls="--")
ax3.set_title("Market maker wealth (cash + inventory × mid)", fontsize=12)
ax3.set_xlabel("time")
ax3.set_ylabel("wealth")
ax3.legend(fontsize=9)
ax3.grid(True, ls="--", alpha=0.4)

# Panel 4: inventory
ax4 = fig.add_subplot(gs[3])
ax4.plot(times, inventories, color="#FF9800", lw=0.8, alpha=0.85, label="inventory")
ax4.axhline(0, color="black", lw=0.5, ls="--")
ax4.set_title("Market maker inventory over time", fontsize=12)
ax4.set_xlabel("time")
ax4.set_ylabel("inventory (units)")
ax4.legend(fontsize=9)
ax4.grid(True, ls="--", alpha=0.4)

plt.suptitle(f"Poisson Limit Order Book  (p_fill={P_FILL})", fontsize=13)
plt.savefig("lob_simulation.png", dpi=150, bbox_inches="tight")
print("\nFigure saved → lob_simulation.png")
plt.show()
