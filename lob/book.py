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
        if ask_price - bid_price != 2 * tick_size:
            raise ValueError("Initial spread must equal 2 * tick_size")

        self.bid_price = bid_price
        self.ask_price = ask_price
        self.bid_size = bid_size
        self.ask_size = ask_size
        self.tick_size = tick_size
        self.default_depth = default_depth

        self._recompute_derived()

    def _recompute_derived(self) -> None:
        self.mid_price = (self.bid_price + self.ask_price) * 0.5
        self.spread = self.ask_price - self.bid_price

    def _shift_up(self) -> None:
        self.bid_price += self.tick_size
        self.ask_price += self.tick_size
        self._recompute_derived()

    def _shift_down(self) -> None:
        self.bid_price -= self.tick_size
        self.ask_price -= self.tick_size
        self._recompute_derived()

    def _consume_ask(self) -> None:
        if self.ask_size <= 0:
            return
        self.ask_size -= 1
        if self.ask_size == 0:
            self._shift_up()
            self.ask_size = self.default_depth

    def _consume_bid(self) -> None:
        if self.bid_size <= 0:
            return
        self.bid_size -= 1
        if self.bid_size == 0:
            self._shift_down()
            self.bid_size = self.default_depth

    def buy_market_order(self) -> None:
        self._consume_ask()

    def sell_market_order(self) -> None:
        self._consume_bid()

    def cancel_ask(self) -> None:
        self._consume_ask()

    def cancel_bid(self) -> None:
        self._consume_bid()

    def buy_limit_order(self) -> None:
        self.bid_size += 1

    def sell_limit_order(self) -> None:
        self.ask_size += 1

    def __repr__(self) -> str:
        return (
            f"OrderBook("
            f"bid={self.bid_price} x{self.bid_size}  |  "
            f"ask={self.ask_price} x{self.ask_size}  "
            f"mid={self.mid_price:.1f}  spread={self.spread})"
        )
