# Karen entry — Sell the Fear: SPY Bull Put Credit Spread (pre-FOMC, IV-crush harvest)

1. **STRATEGY_NAME:** FEAR-FADE-BPS (defined-risk SPY bull put credit spread)

2. **MARKET_ANALYSIS:** 12-month tape is a strong, intact uptrend (SPY ~+20%, QQQ ~+30%, IWM ~+33%); 3-month tape is still net-positive but decelerating, and the last week delivered a sharp, fast ~7% QQQ-led drop (QQQ ~693.69 on Jun 10, ~7% under its Jun 3 high of 748.65) that spiked VIX from ~16 to ~22. A 7% air-pocket in one week inside a structural bull market is a *volatility event*, not a trend break: it leaves put skew steep, premium rich, and the tape oversold heading into a Fed that is widely expected to HOLD on Jun 16-17. Fast oversold flushes in an uptrend base-rate to *stabilize or bounce* over the next 1-2 weeks far more often than they cascade, absent a fresh catalyst — and the cleanest catalyst (FOMC) lands Jun 17, outside my trade window. **My 1-2 week call: oversold BOUNCE-to-SIDEWAYS with elevated-but-falling IV** — I want to be a defined-risk SELLER of the now-expensive downside premium, not a buyer of it.

3. **UNDERLYING(S):** SPY only. Deepest, penny-wide option liquidity and daily expiries; lower realized vol than QQQ (~18% vs ~23% IV) so a short-premium structure has a calmer, higher-Sharpe path; and SPY is the broad-beta proxy least exposed to the single-sector AI/mega-cap unwind that hit QQQ hardest. I want index stabilization, not concentrated tech tail risk.

4. **STRUCTURE:** SPY **bull put credit spread (vertical)**, expiry **Tuesday Jun 16, 2026 (~3 trading DTE; before the Jun 17 FOMC announcement)**:
   - **SELL 1 put** at the strike nearest **0.30 delta** (≈ 1.5–2% below spot; rounds to ~1.5σ of the 3-DTE expected move).
   - **BUY 1 put** **$5 lower** (the defined-risk wing).
   - Strikes by formula: short strike K_s = round(prior-day SPY close × 0.982) to nearest $1, confirm 0.27–0.33 delta; long strike K_l = K_s − $5. *Illustrative only: if SPY closes ~$600, that's SELL 590 put / BUY 585 put.*
   - **Target net CREDIT ≥ $1.50** on the $5 wing (≥30% of width). Max loss = (5.00 − credit) × 100 ≈ $350/spread.

5. **ENTRY_RULES:** Enter **Thu Jun 11, 2026, 10:00–11:30 ET** only, and only if the stabilization thesis is confirmed:
   - SPY trading **at or above its Jun 10 close** OR holding **above the 5-min VWAP** after the 10:00 bar, AND
   - **VIX < 24 and NOT making a new intraday high** (don't sell into expanding panic).
   - **Limit order**; require net credit **≥ $1.40**. **Skip the day entirely** if: fill < $1.40, OR SPY gaps down >1% and stays below VWAP at 10:00 (waterfall continuation = stand aside), OR VIX prints a new high after 10:00.

6. **EXIT_RULES:**
   - **Profit target:** buy to close at **50% of credit received** (e.g., sold $1.50 → close at $0.75).
   - **Stop / defensive:** close if spread value reaches **2× credit received** (loss ≈ 1× credit), OR if SPY closes **below the short strike K_s on two consecutive 5-min candles**.
   - **Time-stop:** force-close ALL legs by **Tue Jun 16, 15:45 ET** — never hold to expiry, never hold through the Jun 17 FOMC.

7. **SIZING:** **2 spreads max**, entered as one order; **max collateral ≈ $700** total ($350/spread max loss). If only one fills at ≥$1.40, trade 1. **Max 1 entry/day**, no averaging down, no second trade.

8. **EDGE:** A plain iron butterfly is short the ATM straddle — it loses on a move in *either* direction, needs a dead-flat pin, and is symmetrically short vega right when downside puts are the single most overpriced part of the surface. My spread (a) sells *only* the steep, post-selloff **put skew** — the richest premium on the board; (b) carries a real margin of safety (short strike ~0.30 delta, ~2% OTM) so SPY can keep drifting lower and I still win; (c) gets paid three ways — theta, IV mean-reversion, and any bounce — instead of needing a pin; and (d) sidesteps the FOMC binary. And against the *actual* competition: all three rival entries **buy** broken-wing put debit flies into a VIX that already spiked to 22 — they are long premium after the vol event, exposed to IV crush, and need continued downside. I'm the **seller** of that expensive premium. If the market merely stabilizes — the base-rate outcome after a fast oversold flush in an uptrend — their long flies bleed via decay and IV mean-reversion while my short spread collects on the highest-probability, best-risk-adjusted path of the week.
