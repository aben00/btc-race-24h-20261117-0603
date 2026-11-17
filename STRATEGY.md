# Strategy

## What the bot does

Long-only mean reversion on 1-minute cbBTC/USDC bars, one full-size
position at a time:

1. Maintain EMA(60) of closes.
2. Buy with all cash when the close is ≥ 50 bps below the EMA.
3. Sell half at +80 bps vs the entry close, the rest at +200 bps.
4. Stop-loss: sell all at −250 bps vs entry.
5. No new entries in the last 60 minutes (a position opened there has no
   time to recover and would only pay entry costs at the flatten).

## Why this shape

Analysis of the 1,440-bar dev window (2026-11-16 06:03Z → 2026-11-17 06:03Z,
BTC $64,461 → $64,776, +0.49%):

- **Momentum loses here.** After a +30–80 bps move over the past 15–60
  minutes, the next 15–60 minutes are negative on average (e.g. after a
  +80 bps 15-min move, the following 30 min average −89 bps). Chasing
  breakouts pays the ~34 bps full-size round-trip cost and then gives it
  back. EMA-crossover trend following lost $37–$62 on the dev window.
- **Dips revert.** Buying the next open after the close sits ≥ 60 bps below
  EMA(60) earned +44 bps on average over the next 60 minutes and +97 bps
  over 120 minutes (n = 20 overlapping signals). At ≥ 40 bps the figures
  are +22 / +55 bps. That is the whole edge: buy a dip, wait for the
  recovery, bank it in two stages.
- **Costs dominate small moves.** A full-size round trip costs ~34 bps
  (4 bps fee + 2 bps slippage + ~11 bps impact each way at ~$880k pool
  depth). Targets of +80 / +200 bps clear that with margin; a 20–30 bps
  target would not.

## Dev-window result (exact integer replay of the harness fill model)

- Net PnL **+$16.28** on $1,000 starting capital (buy-and-hold: +$1.07).
- 5 filled orders (2 round trips; the second position sold half at +80 bps
  and the rest was flattened at the close), max drawdown 0.87%.
- Deterministic: two full runs produce byte-identical action logs.
  Zero rejected fills; the bot exits 0.
- The parameter family is flat, not spiky: across EMA spans 30–120, dip
  thresholds 40–70 bps and single-exit gain targets 50–200 bps, 98 of 100
  tested combinations were profitable (median +$7.95, worst −$0.43). The
  chosen parameters sit in the middle of that plateau, not at a sharp peak.

## Honest limits

- The edge rests on **2–3 round trips** in one 24-hour window. That is a
  small sample; a different day can easily give fewer dips, dips that keep
  falling (the −250 bps stop caps that case), or recoveries that stall
  between the two targets.
- The race window is a different 24 hours. Nothing here predicts it; the
  bot only applies the same rule to whatever prices arrive.
- If no dip of ≥ 50 bps vs EMA(60) occurs, the bot trades nothing and
  scores $0.
- The two-stage exit banks the first +80 bps and keeps the rest for a
  larger recovery; it is a compromise, not an optimum, and on some days
  selling everything at +80 would have done better, on others holding
  everything to +200.
