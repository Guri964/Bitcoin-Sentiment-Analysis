Final Report: Bitcoin Market Sentiment & Trader Performance Analysis

1. Executive Summary

This project analyzes the historical trading data of 35,864 executions on the Hyperliquid decentralized exchange, juxtaposed against the daily Bitcoin Fear & Greed Index (ranging from 0-100). The objective was to uncover hidden patterns dictating trader profitability and generate actionable recommendations.

Key takeaway: Market sentiment heavily dictates trader behavior and profitability. Peak "Greed" levels (Index 80+) correlated with the highest profitability and win rates, while high-volume trading during extreme "Fear" (Index 15) resulted in suppressed win rates. Furthermore, "Whale" accounts demonstrated vastly superior overall profitability compared to the retail cohort.

2. Methodology & Data Preprocessing

Two datasets were utilized:

Bitcoin Sentiment Dataset: Daily numeric classifications of market sentiment (0 = Extreme Fear, 100 = Extreme Greed). Date range: 2018-02-01 to 2025-05-02.

Hyperliquid Trader Data: High-frequency execution data including account IDs, trade side, PnL, and size. Date range: 2023-01-05 to 2025-12-04.

Data Engineering Steps:

Cleaned and standardized column headers dynamically to account for raw data inconsistencies.

Converted Hyperliquid Unix timestamp arrays to standard UTC DateTime objects.

Synchronized both datasets to midnight UTC to ensure a perfect 1:1 join, resulting in 35,864 valid, overlapping records.

Handled missing values and engineered new features: is_win (boolean) and trade_volume_usd.

3. Exploratory Data Analysis (EDA) Findings

A. The Profitability Distribution

The overall win rate across all 35,864 trades sits at 42.86%. This sub-50% baseline is highly typical of retail trading environments, indicating that transaction costs (fees, spread, slippage) and poor risk management naturally push the median trader's expected value (EV) into negative territory over a high sample size.

B. Sentiment Impact (Numeric Fear vs. Greed)

When segmenting by the numeric Fear/Greed index, distinct behavioral clusters emerged:

Extreme Greed Euphoria (Index 80-83): These days generated massive trading volume (over 3,400 trades). Unlike traditional contrarian expectations, these high-greed days yielded the highest win rates in the dataset (65% to 69%) and massive positive mean PnL ($231 to $302 per trade). This suggests strong trend-following conditions where momentum traders thrive.

Extreme Fear Capitulation (Index 15): The single highest volume day for fear (1,748 trades) resulted in a dismal 29.7% win rate and a negative average PnL. Traders attempting to "catch falling knives" during market panics are statistically severely punished.

C. Account Profiling (Whales vs. Retail)

By aggregating data at the account level, we identified 32 unique traders in the dataset. We classified the top 10% of traders by total USD volume as "Whales" (4 accounts) and the rest as "Retail" (28 accounts).

Retail Cohort: Achieved a mean win rate of roughly 37.5%, yielding an average total PnL of $33,589 per account over the dataset timeframe.

Whale Cohort: Achieved a significantly better mean win rate of 40.8%. Their superior strike rate, combined with higher capital deployment, resulted in an average total PnL of $671,076 per account—outperforming retail by roughly 20x in raw dollar terms.

Note: Leverage data was not present in the provided dataset and was dynamically excluded from the risk analysis.

4. Actionable Business Insights & Recommendations

For Algorithmic Traders / Hedge Funds

Momentum Following in Extreme Greed: Statistical data shows that once the sentiment index breaks above 80, trend-following strategies exhibit a massive statistical edge (near 70% win rate). Algorithms should aggressively scale into momentum breakouts rather than attempting to mean-revert peak greed.

Avoid Knife-Catching: Trading systems should pause or significantly reduce position sizing when the index drops to 15 or below, as the expected value of trades heavily skews negative due to unpredictable volatility spikes.

For the Hyperliquid Platform (Product/Business Strategy)

Whale Retention Programs: Because just 4 accounts generate the vast majority of volume and successful market-making, Hyperliquid should implement VIP fee-tier programs specifically tailored to accounts exceeding the 90th percentile in volume to prevent capital flight to rival DEXs.

Retail Sentiment Warnings: The platform could introduce UI warnings when the Fear index drops below 20, cautioning retail users about historical unprofitability during capitulation events. This would build long-term user trust and prevent rapid retail account liquidations.