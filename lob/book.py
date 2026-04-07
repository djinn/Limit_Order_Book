"""
OrderBook: minimal single-level limit order book.

State
-----
  bid_price : int   best bid (integer ticks)
  ask_price : int   best ask (integer ticks)
  bid_size  : int   number of units queued at the bid
  ask_size  : int   number of units queued at the ask
  tick_size : int   price grid spacing (constant spread = ask - bid)

Price update rule (spread is always preserved)
-----------------------------------------------
  ask_size hits 0  →  both prices rise by tick_size, ask_size resets
  bid_size hits 0  →  both prices fall by tick_size, bid_size resets

Six events (each removes or adds exactly one unit)
---------------------------------------------------
  buy_market_order   consume 1 from ask queue
  sell_market_order  consume 1 from bid queue
  buy_limit_order    add 1 to bid queue
  sell_limit_order   add 1 to ask queue
  cancel_bid         remove 1 from bid queue
  cancel_ask         remove 1 from ask queue
"""


class OrderBook:
    def __init__(
        self,
        bid_price: int = 9999,
        ask_price: int = 10001,
        bid_size: int = 10,
        ask_size: int = 10,
        tick_size: int = 1,
        default_depth: int = 10,
    ) -> None:
        assert ask_price - bid_price == 2 * tick_size, (
            "Initial spread must equal 2 * tick_size"
        )
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.tick_size = tick_size
        self.default_depth = default_depth

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def mid_price(self) -> float:
        return (self.bid_price + self.ask_price) / 2.0

    @property
    def spread(self) -> int:
        return self.ask_price - self.bid_price

    # ------------------------------------------------------------------
    # Six events
    # ------------------------------------------------------------------

    def buy_market_order(self) -> None:
        """Consume one unit from the ask queue (buyer lifts the offer)."""
        if self.ask_size <= 0:
            return
        self.ask_size -= 1
        if self.ask_size == 0:
            self.ask_price += self.tick_size
            self.bid_price += self.tick_size
            self.ask_size = self.default_depth

    def sell_market_order(self) -> None:
        """Consume one unit from the bid queue (seller hits the bid)."""
        if self.bid_size <= 0:
            return
        self.bid_size -= 1
        if self.bid_size == 0:
            self.ask_price -= self.tick_size
            self.bid_price -= self.tick_size
            self.bid_size = self.default_depth

    def buy_limit_order(self) -> None:
        """Add one unit to the bid queue."""
        self.bid_size += 1

    def sell_limit_order(self) -> None:
        """Add one unit to the ask queue."""
        self.ask_size += 1

    def cancel_bid(self) -> None:
        """Remove one unit from the bid queue."""
        if self.bid_size <= 0:
            return
        self.bid_size -= 1
        if self.bid_size == 0:
            self.ask_price -= self.tick_size
            self.bid_price -= self.tick_size
            self.bid_size = self.default_depth

    def cancel_ask(self) -> None:
        """Remove one unit from the ask queue."""
        if self.ask_size <= 0:
            return
        self.ask_size -= 1
        if self.ask_size == 0:
            self.ask_price += self.tick_size
            self.bid_price += self.tick_size
            self.ask_size = self.default_depth

    def __repr__(self) -> str:
        return (
            f"OrderBook("
            f"bid={self.bid_price} x{self.bid_size}  |  "
            f"ask={self.ask_price} x{self.ask_size}  "
            f"mid={self.mid_price:.1f}  spread={self.spread})"
        )
