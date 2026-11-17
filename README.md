# Dip-Buy BTC Bot — make.fun BTC 24h race

[![make.fun](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/aben00/btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/aben00/btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603)

A mean-reversion trading bot for the [make.fun BTC 24h race](https://make.fun/bounty/btc-race-24h-20261117-0603):
it trades Coinbase Wrapped BTC (cbBTC) against USDC, minute by minute, on
the `agent-fun/bars-replay/v1` protocol.

## Strategy

Long-only, one position at a time, full-size entries:

- Track EMA(60) of the 1-minute closes.
- **Buy** with all cash when the close is at least **50 bps below** the EMA
  — a dip that, on the dev window, tended to revert over the next 1–2 hours.
- **Sell half** when the close recovers to **+80 bps** above the entry close;
  **sell the rest** at **+200 bps**.
- **Stop-loss:** sell everything if the close falls **250 bps** below entry.
- No new entries in the final 60 minutes of the window.

See [STRATEGY.md](STRATEGY.md) for the evidence and the honest limits.

## Layout

- `main.py` — the bot (Python 3.13, standard library only, deterministic).
- `vendor/makefun_bars.py` — byte-for-byte copy of the kit's Python SDK shim.

## Local grade

From the unpacked kit directory:

```sh
node cli/makefun.mjs grade-local --kit . --bot <path-to-this-repo> --driver docker
```

## License

MIT — see [LICENSE](LICENSE).
