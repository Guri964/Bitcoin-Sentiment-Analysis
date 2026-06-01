Bitcoin Market Sentiment and Trader Performance Analysis

📌 Project Overview

This project explores the relationship between Bitcoin market sentiment (Fear vs. Greed) and trader performance on the Hyperliquid decentralized exchange. By merging historical trading data with daily sentiment classifications, this analysis uncovers hidden patterns in profitability, leverage usage, and risk management strategies.

The insights generated aim to drive smarter trading strategies and provide platform-level recommendations for risk mitigation.

📂 Project Structure

analysis.py: Main Python script containing data downloading, cleaning, EDA, statistical testing, and visualization logic.

Final_Report.md: Comprehensive business report detailing methodology, statistical findings, and actionable recommendations.

README.md: Project documentation and execution instructions.

data/: Directory automatically created by the script to store downloaded CSVs.

🚀 Setup & Installation

Clone the repository (or download the files).

Install dependencies:
We use gdown to automatically download the datasets from the provided Google Drive links.

pip install pandas numpy matplotlib seaborn scipy gdown


Run the analysis:
Execute the Python script. It will automatically download the datasets, process them, and generate visualizations and statistical outputs:

python analysis.py


Note: The script is configured to use your specific Google Drive links. If you ever need to test without an internet connection, you can set USE_DUMMY_DATA = True inside the script.

📊 Core Objectives Met

Data Engineering: Standardized Unix timestamps, handled missing values, and merged high-frequency trade data with daily sentiment indices.

EDA: Evaluated win rates, PnL distributions, and trading volume distributions.

Statistical Inference: Conducted Independent T-tests and Pearson correlations to validate the significance of sentiment on profitability and leverage.

Business Intelligence: Translated quantitative findings into actionable trading strategies and platform recommendations.