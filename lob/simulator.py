"""
Poisson order book simulator.

This module simulates a limit order book as a discrete-time approximation
to a continuous-time Markov process driven by six independent Poisson event
streams.

Model
-----
Let λ_i be the intensity of event type i, and let

    Λ = Σ λ_i

At each time step dt:

1. An event occurs with probability Λ * dt.
2. Conditional on occurrence, the event type is sampled with probability
   λ_i / Λ.
3. Exactly one state transition is applied.
4. The post-transition state is recorded.

Invariant
---------
At most one event may occur in a single time step.

Stability condition
-------------------
Λ * dt << 1

Violating this condition biases the simulation by suppressing the possibility
of multiple arrivals within a step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .book import OrderBook
from .market_maker import MarketMaker

EVENTS = (
    "buy_market_order",
    "sell_market_order",
    "buy_limit_order",
    "sell_limit_order",
    "cancel_bid",
    "cancel_ask",
)


@dataclass
class Snapshot:
    step: int
    time: float
    bid_price: int
    ask_price: int
    bid_size: int
    ask_size: int
    mid_price: float
    spread: int
    event: Optional[str]
    inventory: int
    cash: float
    wealth: float


@dataclass
class SimulationResult:
    snapshots: List[Snapshot]
    event_counts: Dict[str, int]
    ask_depletions: int
    bid_depletions: int
    bid_fills: int
    ask_fills: int

    @property
    def total_events(self) -> int:
        return sum(self.event_counts.values())

    def print_diagnostics(self, lambdas: Dict[str, float], dt: float) -> None:
        horizon = len(self.snapshots) * dt

        print(f"\nEvent diagnostics (T = {horizon:.1f}):")
        print(f"  {'event':<22}  {'fired':>6}  {'expected':>8}  {'ratio':>6}")
        print(f"  {'-' * 22}  {'-' * 6}  {'-' * 8}  {'-' * 6}")

        for event in EVENTS:
            fired = self.event_counts.get(event, 0)
            expected = lambdas.get(event, 0.0) * horizon
            ratio = fired / expected if expected > 0 else float("nan")
            print(f"  {event:<22}  {fired:>6}  {expected:>8.1f}  {ratio:>6.3f}")

        print("\nQueue depletions:")
        print(f"  ask depleted (price up):   {self.ask_depletions}")
        print(f"  bid depleted (price down): {self.bid_depletions}")

        print("\nMM fill counts:")
        print(f"  bid fills (MM bought): {self.bid_fills}")
        print(f"  ask fills (MM sold):   {self.ask_fills}")


def fill_probability(delta: float, k: float = 2.0) -> float:
    """
    Convert quote aggressiveness into a fill probability using a logistic map.

    Interpretation
    --------------
    delta > 0  : quote improves on the best price   -> p > 0.5
    delta = 0  : quote matches the best price       -> p = 0.5
    delta < 0  : quote is passive                   -> p < 0.5

    Parameters
    ----------
    delta:
        Signed quote aggressiveness.
    k:
        Logistic steepness. Larger values make the response more step-like.
    """
    return 1.0 / (1.0 + np.exp(-k * delta))


def _build_rate_vector(lambdas: Dict[str, float]) -> np.ndarray:
    return np.array([lambdas.get(event, 0.0) for event in EVENTS], dtype=float)


def _validate_time_step(total_rate: float, dt: float) -> float:
    fire_probability = total_rate * dt
    if fire_probability >= 1.0:
        raise ValueError(
            f"Invalid discretization: Λ * dt = {fire_probability:.6f} must be < 1. "
            "Reduce dt or the event intensities."
        )
    return fire_probability


def _market_maker_quotes(
    book: OrderBook, mm: MarketMaker, gamma: float
) -> tuple[int, int]:
    """
    Compute inventory-aware market maker quotes.

    Reservation price:
        r = mid - gamma * inventory
    """
    reservation_price = book.mid_price - gamma * mm.inventory
    half_spread = (book.ask_price - book.bid_price) / 2.0

    mm_bid = int(round(reservation_price - half_spread))
    mm_ask = int(round(reservation_price + half_spread))
    return mm_bid, mm_ask


def _fill_chance(
    *,
    event: str,
    book: OrderBook,
    mm_bid: int,
    mm_ask: int,
    fill_mode: str,
    p_fill: float,
    k: float,
) -> float:
    """
    Compute market maker fill probability for a market-order event.
    """
    if event == "sell_market_order":
        if fill_mode == "logistic":
            return fill_probability(mm_bid - book.bid_price, k)
        return p_fill if mm_bid >= book.bid_price else 0.0

    if event == "buy_market_order":
        if fill_mode == "logistic":
            return fill_probability(book.ask_price - mm_ask, k)
        return p_fill if mm_ask <= book.ask_price else 0.0

    return 0.0


def _attempt_market_maker_fill(
    *,
    rng: np.random.Generator,
    event: str,
    book: OrderBook,
    mm: MarketMaker,
    gamma: float,
    fill_mode: str,
    p_fill: float,
    k: float,
) -> tuple[int, int]:
    """
    Attempt a market maker execution on a market-order event.

    Returns
    -------
    bid_fill_increment, ask_fill_increment
    """
    if event not in {"buy_market_order", "sell_market_order"}:
        return 0, 0

    mm_bid, mm_ask = _market_maker_quotes(book, mm, gamma)
    probability = _fill_chance(
        event=event,
        book=book,
        mm_bid=mm_bid,
        mm_ask=mm_ask,
        fill_mode=fill_mode,
        p_fill=p_fill,
        k=k,
    )

    if rng.random() >= probability:
        return 0, 0

    if event == "sell_market_order":
        mm.inventory += 1
        mm.cash -= mm_bid
        return 1, 0

    mm.inventory -= 1
    mm.cash += mm_ask
    return 0, 1


def _apply_book_event(book: OrderBook, event: str) -> tuple[int, int]:
    """
    Apply an event to the order book and detect queue depletion via price moves.

    Returns
    -------
    ask_depletion_increment, bid_depletion_increment
    """
    old_ask_price = book.ask_price
    old_bid_price = book.bid_price

    getattr(book, event)()

    ask_depletion = int(book.ask_price > old_ask_price)
    bid_depletion = int(book.bid_price < old_bid_price)
    return ask_depletion, bid_depletion


def _snapshot(
    step: int, time: float, book: OrderBook, mm: MarketMaker, event: Optional[str]
) -> Snapshot:
    return Snapshot(
        step=step,
        time=time,
        bid_price=book.bid_price,
        ask_price=book.ask_price,
        bid_size=book.bid_size,
        ask_size=book.ask_size,
        mid_price=book.mid_price,
        spread=book.spread,
        event=event,
        inventory=mm.inventory,
        cash=mm.cash,
        wealth=mm.wealth(book.mid_price),
    )


def simulate(
    lambdas: Dict[str, float],
    dt: float = 0.01,
    n_steps: int = 5000,
    bid_price: int = 9999,
    ask_price: int = 10001,
    bid_size: int = 10,
    ask_size: int = 10,
    tick_size: int = 1,
    default_depth: int = 10,
    p_fill: float = 0.5,
    gamma: float = 0.0,
    fill_mode: str = "logistic",
    k: float = 2.0,
    seed: Optional[int] = None,
) -> SimulationResult:
    """
    Simulate a limit order book under Poisson-driven event flow.

    Parameters
    ----------
    lambdas:
        Event intensities keyed by event name.
    dt:
        Time step. Must satisfy Λ * dt < 1.
    n_steps:
        Number of simulation steps.
    bid_price, ask_price, bid_size, ask_size, tick_size, default_depth:
        Initial order book state.
    p_fill:
        Constant fill probability when fill_mode="constant".
    gamma:
        Inventory aversion. Quotes are centered at:
            r = mid - gamma * inventory
    fill_mode:
        Either:
        - "constant": use p_fill subject to quote competitiveness
        - "logistic": derive fill probability from quote aggressiveness
    k:
        Logistic steepness for fill_mode="logistic".
    seed:
        RNG seed.

    Returns
    -------
    SimulationResult
    """
    if fill_mode not in {"constant", "logistic"}:
        raise ValueError("fill_mode must be either 'constant' or 'logistic'.")

    rng = np.random.default_rng(seed)

    book = OrderBook(
        bid_price=bid_price,
        ask_price=ask_price,
        bid_size=bid_size,
        ask_size=ask_size,
        tick_size=tick_size,
        default_depth=default_depth,
    )
    mm = MarketMaker()

    rates = _build_rate_vector(lambdas)
    total_rate = float(rates.sum())
    fire_probability = _validate_time_step(total_rate, dt)

    if total_rate == 0.0:
        event_probabilities = None
    else:
        event_probabilities = rates / total_rate

    snapshots: List[Snapshot] = []
    event_counts: Dict[str, int] = {event: 0 for event in EVENTS}

    ask_depletions = 0
    bid_depletions = 0
    bid_fills = 0
    ask_fills = 0

    current_time = 0.0

    for step in range(n_steps):
        fired_event: Optional[str] = None

        if total_rate > 0.0 and rng.random() < fire_probability:
            event_index = int(rng.choice(len(EVENTS), p=event_probabilities))
            fired_event = EVENTS[event_index]
            event_counts[fired_event] += 1

            bid_fill_inc, ask_fill_inc = _attempt_market_maker_fill(
                rng=rng,
                event=fired_event,
                book=book,
                mm=mm,
                gamma=gamma,
                fill_mode=fill_mode,
                p_fill=p_fill,
                k=k,
            )
            bid_fills += bid_fill_inc
            ask_fills += ask_fill_inc

            ask_dep_inc, bid_dep_inc = _apply_book_event(book, fired_event)
            ask_depletions += ask_dep_inc
            bid_depletions += bid_dep_inc

        snapshots.append(_snapshot(step, current_time, book, mm, fired_event))
        current_time += dt

    return SimulationResult(
        snapshots=snapshots,
        event_counts=event_counts,
        ask_depletions=ask_depletions,
        bid_depletions=bid_depletions,
        bid_fills=bid_fills,
        ask_fills=ask_fills,
    )
