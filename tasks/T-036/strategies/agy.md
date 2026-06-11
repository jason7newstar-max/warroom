1. STRATEGY_NAME: QQQ-IPO-TAX-BWB (Bearish Asymmetric Put Broken-Wing Butterfly)

2. MARKET_ANALYSIS: Over the last 12 months, US equities have risen strongly (QQQ +30.29%, SPY +20.63%), but momentum has broken down sharply over the last 10 days, with QQQ falling 7.0% from its June 2 high, causing the VIX to spike from 15.74 to 22.22. This sell-off is driven by tech valuation concerns, resurgent headline CPI at 4.2%, and an impending "IPO tax" liquidity drain from the massive SpaceX IPO on June 12, coupled with hawkish positioning ahead of the June 16-17 FOMC meeting. Consequently, we call for a bearish-to-sideways, high-volatility regime for the coming week as capital de-risks and rebalances.

3. UNDERLYING(S): QQQ. QQQ has the highest exposure to the mega-cap tech stocks being sold off to fund the SpaceX IPO, higher implied volatility (23.55% vs SPY's 18.10%), and highly liquid option chains with $1 strike intervals, allowing precise wing spacing.

4. STRUCTURE: 4DTE Put Broken-Wing Butterfly entered dynamically relative to the spot price of QQQ at entry ($S_{entry}$), expiring on Monday, June 15, 2026:
   - Buy 1x Put at Strike K1 = round($S_{entry}$) (ATM, approx 0.50 delta)
   - Sell 2x Puts at Strike K2 = K1 - $6.00 (OTM, approx 0.35 delta)
   - Buy 1x Put at Strike K3 = K2 - $3.00 = K1 - $9.00 (OTM, approx 0.18 delta)
   This forms an asymmetric put butterfly where the upper wing is $6.00 wide and the lower wing is $3.00 wide, resulting in an expected net debit of approximately $1.60.

5. ENTRY_RULES: 
   - Time Window: Thursday, June 11, 2026, between 10:00 AM and 11:30 AM ET.
   - Trend Filter: Enter only if QQQ is trading below its 5-minute 20-period Exponential Moving Average (EMA) and the 14-period RSI is below 55 (confirming downward intraday momentum).
   - Premium Filter: The entry net debit must be between $1.40 and $1.85. If the debit is higher than $1.85, adjust the wings by moving the short strike K2 to K1 - $7.00 and long strike K3 to K2 - $3.00.

6. EXIT_RULES: 
   - Profit Target: Close the position if the net value of the structure reaches $4.00 (+150% of the entry debit).
   - Stop-Loss: No stop-loss on the downside (as downside profit is guaranteed below K3). Close the position if QQQ rallies to K1 + $2.50 to salvage remaining premium, or if the net loss exceeds 70% of the debit paid.
   - Time-Stop: Force close all open contracts on Monday, June 15, 2026, at 15:45 ET using market orders to eliminate assignment and pin risk.

7. SIZING: 5 contracts. Max collateral per trade is $800 (max loss is limited to the debit paid, which fits the $1000 budget). Max 1 trade per day.

8. EDGE: A plain iron butterfly loses heavily on any directional move and requires a precise pin at spot. Given our bearish/high-volatility call, QQQ is expected to move significantly. This Put Broken-Wing Butterfly has zero downside risk; if QQQ crashes (below K3), it guarantees a profit equal to (Upper Wing - Lower Wing - Debit) = ($6.00 - $3.00 - $1.60) = +$1.40 ($140 per contract or 87.5% return), while offering a peak profit of +$4.40 ($440 per contract or 275% return) if QQQ pins near K2. By expiring on Monday, June 15, it avoids the binary risk of the June 16-17 FOMC decision while fully harvesting the SpaceX IPO tech sector sell-off.
