class MarketMaker:
    def __init__(self) -> None:
        self.inventory: int = 0
        self.cash: float = 0.0

    def wealth(self, mid_price: float) -> float:
        return self.cash + self.inventory * mid_price
