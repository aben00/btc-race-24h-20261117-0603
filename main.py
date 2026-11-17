"""Dip-buying mean-reversion bot for the make.fun BTC 24h race.

Strategy (see STRATEGY.md): long-only, one position at a time.
  - Track EMA(60) of the 1-minute closes of CBBTC.
  - Buy with all cash when the close trades at least 50 bps below the EMA
    (a dip the window's own statistics say tends to revert).
  - Sell half the position when the close recovers to 80 bps above the
    entry close; sell the rest at 200 bps above it.
  - Stop-loss: sell everything if the close falls 250 bps below entry.
  - No new entries in the final 60 minutes of the window.

Deterministic: pure float64 arithmetic over the bars received, no wall
clock, no network, no files, no unseeded randomness. The same bars give
the same orders on every run.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# EMA span in bars (1-minute bars).
EMA_SPAN = 60
# Entry: close at least this many bps below the EMA.
DIP_BPS = 50
# Exits, in bps versus the entry close.
TAKE_HALF_BPS = 80
TAKE_REST_BPS = 200
STOP_BPS = 250
# No new entries once the window is this many minutes from its start
# (the window is 1440 one-minute bars; the last hour leaves no time for
# a dip to recover, so opening there only pays entry costs).
ENTRY_CUTOFF_MINUTES = 1380
# Slippage cap on every order, in bps from the latest close. The largest
# open-vs-previous-close move on the dev window is ~16 bps, so 100 bps
# never binds in practice; it only guards against a wild gap.
MAX_SLIPPAGE_BPS = 100

_EMA_K = 2.0 / (EMA_SPAN + 1)


class Bot:
    def __init__(self):
        self.ema = None          # EMA(60) of closes, float (price-scale units)
        self.first_t = None      # t of the first bar seen (ms)
        self.entry_close = None  # close (int) the current position was entered on
        self.entry_qty = None    # qty (int) the position held right after entry
        self.pending_buy = None  # client_id of a buy not yet confirmed filled

    def on_batch(self, state, batch):
        bar = None
        for b in batch["bars"]:
            if b["symbol"] == SYMBOL:
                bar = b
                break
        if bar is None:
            return []
        close = int(bar["c"])
        if self.first_t is None:
            self.first_t = int(batch["t"])
        # EMA over closes; a bar that is absent adds nothing.
        if self.ema is None:
            self.ema = float(close)
        else:
            self.ema += _EMA_K * (close - self.ema)

        held = state.positions.get(SYMBOL)
        # A buy sent on the previous batch is confirmed by the position
        # appearing (or its rejection in this batch's fills).
        if self.pending_buy is not None:
            if held is not None:
                self.entry_qty = held.qty
                self.pending_buy = None
            else:
                rejected = any(
                    f.get("client_id") == self.pending_buy
                    and f.get("status") == "rejected"
                    for f in batch.get("fills", [])
                )
                if rejected:
                    self.entry_close = None
                    self.pending_buy = None
                else:
                    # Fill not reported yet; wait one more batch.
                    return []

        if held is None:
            if self.entry_close is not None:
                # Position gone without a fill confirmation: the entry
                # never happened (or was flattened); allow a fresh entry.
                self.entry_close = None
                self.entry_qty = None
            if state.warming_up:
                return []
            elapsed_min = (int(batch["t"]) - self.first_t) // 60000
            if elapsed_min > ENTRY_CUTOFF_MINUTES:
                return []
            if close * 10000 < self.ema * (10000 - DIP_BPS):
                cid = state.client_id()
                self.entry_close = close
                self.pending_buy = cid
                return [{
                    "side": "buy",
                    "client_id": cid,
                    "symbol": SYMBOL,
                    "notional_quote_units": state.cash,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
            return []

        # Holding a position: exits versus the entry close.
        entry = self.entry_close
        if entry is None:
            # Defensive: a position we did not open (should not happen);
            # hold it to the window's flatten rather than guessing.
            return []
        half_sold = self.entry_qty is not None and held.qty < self.entry_qty
        # Stop-loss first: sell everything.
        if close * 10000 <= entry * (10000 - STOP_BPS):
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        # Second target: sell the rest.
        if close * 10000 >= entry * (10000 + TAKE_REST_BPS):
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        # First target: sell half, once.
        if not half_sold and close * 10000 >= entry * (10000 + TAKE_HALF_BPS):
            half = held.qty // 2
            if half > 0:
                return [{
                    "side": "sell",
                    "symbol": SYMBOL,
                    "qty": half,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
        return []


def main():
    bot = Bot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
