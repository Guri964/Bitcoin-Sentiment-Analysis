# %% [markdown]
# # Bitcoin Sentiment vs. Trader Performance
# **Objective:** Analyze the impact of Bitcoin Market Sentiment (Fear/Greed) on trader profitability and behavior on Hyperliquid.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import os

warnings.filterwarnings('ignore')
sns.set_theme(style="whitegrid", palette="muted")

# ==========================================
# CONFIGURATION
# ==========================================
# Set to False to download and use the real data from Google Drive
USE_DUMMY_DATA = False 

DATA_DIR = 'data'
SENTIMENT_CSV_PATH = os.path.join(DATA_DIR, 'sentiment.csv')
TRADES_CSV_PATH = os.path.join(DATA_DIR, 'hyperliquid_trades.csv')

# Google Drive File IDs
GDRIVE_TRADES_ID = '1IAfLZwu6rJzyWKgBToqwSmmVYU6VbjVs'
GDRIVE_SENTIMENT_ID = '1PgQC0tO8XN-wqkNyghWc_-mnrYv_nhSf'

# %% [markdown]
# ## 1. Data Loading (Google Drive Download) & Dummy Generation

# %%
def download_from_gdrive():
    """Downloads files from Google Drive using gdown."""
    import gdown
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    print("Checking for existing datasets...")
    
    # Download Trades Data
    if not os.path.exists(TRADES_CSV_PATH):
        print("Downloading Historical Trader Data from Google Drive...")
        trades_url = f'https://drive.google.com/uc?id={GDRIVE_TRADES_ID}'
        gdown.download(trades_url, TRADES_CSV_PATH, quiet=False)
    
    # Download Sentiment Data
    if not os.path.exists(SENTIMENT_CSV_PATH):
        print("Downloading Sentiment Data from Google Drive...")
        sentiment_url = f'https://drive.google.com/uc?id={GDRIVE_SENTIMENT_ID}'
        gdown.download(sentiment_url, SENTIMENT_CSV_PATH, quiet=False)
        
    print("Datasets are ready.")

def generate_dummy_data():
    """Generates synthetic datasets for demonstration purposes if internet is down."""
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    sentiments = np.random.choice(['Fear', 'Greed', 'Neutral'], size=100, p=[0.4, 0.4, 0.2])
    df_sentiment = pd.DataFrame({'Date': dates, 'Classification': sentiments})
    
    num_trades = 10000
    accounts = [f"0x{str(i).zfill(4)}" for i in range(1, 101)]
    
    start_ts = int(pd.Timestamp('2023-01-01').timestamp() * 1000)
    end_ts = int(pd.Timestamp('2023-04-10').timestamp() * 1000)
    times = np.random.randint(start_ts, end_ts, size=num_trades)
    
    df_trades = pd.DataFrame({
        'account': np.random.choice(accounts, size=num_trades),
        'symbol': ['BTC-USD'] * num_trades,
        'execution price': np.random.normal(30000, 2000, size=num_trades),
        'size': np.random.exponential(1.5, size=num_trades),
        'side': np.random.choice(['Buy', 'Sell'], size=num_trades),
        'time': times,
        'start position': np.random.normal(0, 1, size=num_trades),
        'event': ['Trade'] * num_trades,
        'closedPnL': np.random.normal(-5, 100, size=num_trades), 
        'leverage': np.random.choice([1, 2, 5, 10, 20, 50, 100], size=num_trades, p=[0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.05])
    })
    
    df_trades['closedPnL'] = df_trades['closedPnL'] - (df_trades['leverage'] * 2 * np.random.rand(num_trades))
    return df_sentiment, df_trades

if USE_DUMMY_DATA:
    print("Using generated synthetic data for demonstration.")
    df_sentiment, df_trades = generate_dummy_data()
else:
    try:
        download_from_gdrive()
        print("Loading data from downloaded CSVs...")
        df_sentiment = pd.read_csv(SENTIMENT_CSV_PATH)
        df_trades = pd.read_csv(TRADES_CSV_PATH)
    except ImportError:
        print("CRITICAL ERROR: 'gdown' library is missing.")
        print("Please run: pip install gdown")
        exit(1)

# %% [markdown]
# ## 2. Data Cleaning & Preprocessing

# %%
def clean_and_merge(df_sent, df_trd):
    """Cleans raw data and merges trades with market sentiment."""
    
    # Strip hidden whitespace from all column headers in both datasets
    df_sent.columns = df_sent.columns.str.strip()
    df_trd.columns = df_trd.columns.str.strip()
    
    # ---------------------------------------------
    # 1. Clean Sentiment Data
    # ---------------------------------------------
    sent_date_col = next((col for col in df_sent.columns if 'date' in col.lower() or 'time' in col.lower()), 'Date')
    sent_class_col = next((col for col in df_sent.columns if 'class' in col.lower() or 'sentiment' in col.lower() or 'value' in col.lower()), 'Classification')
    
    df_sent.rename(columns={sent_date_col: 'Date', sent_class_col: 'Classification'}, inplace=True)
    
    # Robust Date Parsing for Sentiment Data (Handles string-based Unix timestamps)
    sent_numeric = pd.to_numeric(df_sent['Date'], errors='coerce')
    if sent_numeric.notna().sum() > 0.5 * len(df_sent):
        # Data is mostly unix timestamps
        if sent_numeric.max() < 1e11:
            df_sent['Date'] = pd.to_datetime(sent_numeric, unit='s', errors='coerce')
        else:
            df_sent['Date'] = pd.to_datetime(sent_numeric, unit='ms', errors='coerce')
    else:
        # Data is standard date strings
        df_sent['Date'] = pd.to_datetime(df_sent['Date'], errors='coerce')
        
    # Standardize sentiment dates securely to datetime64 at midnight
    df_sent['Date'] = df_sent['Date'].dt.tz_localize(None).dt.normalize()
    df_sent['Classification'] = df_sent['Classification'].astype(str).str.strip().str.title()
    
    # ---------------------------------------------
    # 2. Clean Trades Data
    # ---------------------------------------------
    # Drop any natively duplicated columns first to prevent ambiguity
    df_trd = df_trd.loc[:, ~df_trd.columns.duplicated()].copy()
    
    # Dynamically detect time column
    trd_time_col = next((col for col in df_trd.columns if 'time' in col.lower() or 'date' in col.lower()), 'time')
    
    # Robust Date Parsing for Trades Data
    trd_numeric = pd.to_numeric(df_trd[trd_time_col], errors='coerce')
    if trd_numeric.notna().sum() > 0.5 * len(df_trd):
        if trd_numeric.max() < 1e11:
            df_trd['datetime_utc'] = pd.to_datetime(trd_numeric, unit='s', errors='coerce')
        else:
            df_trd['datetime_utc'] = pd.to_datetime(trd_numeric, unit='ms', errors='coerce')
    else:
        df_trd['datetime_utc'] = pd.to_datetime(df_trd[trd_time_col], errors='coerce')
        
    # Standardize trade dates securely to datetime64 at midnight to match sentiment dates
    df_trd['Date'] = df_trd['datetime_utc'].dt.tz_localize(None).dt.normalize()
    
    # Dynamically standardize other essential trade columns
    col_map = {}
    mapped_targets = set()
    
    for col in df_trd.columns:
        cl = col.lower()
        target = None
        
        if ('pnl' in cl or 'profit' in cl or 'loss' in cl) and 'closedPnL' not in mapped_targets: target = 'closedPnL'
        elif ('price' in cl or 'exec' in cl) and 'execution price' not in mapped_targets: target = 'execution price'
        elif ('size' in cl or 'amount' in cl or 'qty' in cl or 'quantity' in cl) and 'size' not in mapped_targets: target = 'size'
        elif ('leverage' in cl or 'lev' in cl) and 'leverage' not in mapped_targets: target = 'leverage'
        elif ('account' in cl or 'user' in cl) and 'account' not in mapped_targets: target = 'account'
        
        if target:
            col_map[col] = target
            mapped_targets.add(target)

    df_trd.rename(columns=col_map, inplace=True)

    # Clean nulls safely by only referencing columns that actually exist
    expected_drop_cols = ['closedPnL', 'execution price', 'size', 'leverage', 'Date']
    actual_drop_cols = [c for c in expected_drop_cols if c in df_trd.columns]
    
    df_trd.dropna(subset=actual_drop_cols, inplace=True)
    
    numeric_cols = ['closedPnL', 'execution price', 'size', 'leverage']
    actual_numeric_cols = [c for c in numeric_cols if c in df_trd.columns]
    
    for col in actual_numeric_cols:
        df_trd[col] = pd.to_numeric(df_trd[col], errors='coerce')
    
    df_trd.dropna(subset=actual_numeric_cols, inplace=True) 
    
    # Feature Engineering (with safety checks)
    if 'closedPnL' in df_trd.columns:
        df_trd['is_win'] = df_trd['closedPnL'] > 0
    if 'execution price' in df_trd.columns and 'size' in df_trd.columns:
        df_trd['trade_volume_usd'] = df_trd['execution price'] * df_trd['size']
    
    # ---------------------------------------------
    # 3. Data Debugging & Merge
    # ---------------------------------------------
    sent_min, sent_max = df_sent['Date'].min(), df_sent['Date'].max()
    trd_min, trd_max = df_trd['Date'].min(), df_trd['Date'].max()
    
    print("\n--- Date Alignment Check ---")
    print(f"Sentiment Data Available From: {sent_min.date() if pd.notnull(sent_min) else 'NaT'} to {sent_max.date() if pd.notnull(sent_max) else 'NaT'}")
    print(f"Trades Data Available From:    {trd_min.date() if pd.notnull(trd_min) else 'NaT'} to {trd_max.date() if pd.notnull(trd_max) else 'NaT'}")
    print("----------------------------\n")
    
    merged_df = pd.merge(df_trd, df_sent, on='Date', how='inner')
    
    return merged_df

df_merged = clean_and_merge(df_sentiment, df_trades)
print(f"Data merged successfully. Total valid records analyzed: {len(df_merged)}")

# %% [markdown]
# ## 3. Exploratory Data Analysis (EDA)

# %%
# 3.1 Overall Win Rate & PnL Distribution
if len(df_merged) > 0:
    total_win_rate = df_merged['is_win'].mean() * 100
    print(f"Overall Win Rate: {total_win_rate:.2f}%")

    plt.figure(figsize=(10, 5))
    # Using 1st and 99th percentile to filter out extreme liquidation outliers for a cleaner chart
    pnl_1 = df_merged['closedPnL'].quantile(0.01)
    pnl_99 = df_merged['closedPnL'].quantile(0.99)
    filtered_pnl = df_merged[(df_merged['closedPnL'] >= pnl_1) & (df_merged['closedPnL'] <= pnl_99)]['closedPnL']
    
    sns.histplot(filtered_pnl, bins=100, kde=True, color='blue')
    plt.title('Distribution of Closed PnL (1st - 99th Percentile)')
    plt.xlabel('PnL ($)')
    plt.ylabel('Frequency')
    plt.axvline(0, color='red', linestyle='--', label='Breakeven')
    plt.legend()
    plt.show()

# %%
# 3.2 Sentiment Breakdown
if len(df_merged) > 0:
    sentiment_counts = df_merged['Classification'].value_counts()

    plt.figure(figsize=(6, 4))
    sns.barplot(x=sentiment_counts.index, y=sentiment_counts.values, palette='viridis')
    plt.title('Trade Volume by Market Sentiment')
    plt.ylabel('Number of Trades')
    plt.show()

# %% [markdown]
# ## 4. Patterns: Sentiment vs. Trader Performance

# %%
if len(df_merged) > 0:
    agg_dict = {
        'Avg_PnL': ('closedPnL', 'mean'),
        'Median_PnL': ('closedPnL', 'median'),
        'Win_Rate': ('is_win', lambda x: x.mean() * 100)
    }
    
    # Dynamically add leverage and account if they exist in the dataset
    if 'leverage' in df_merged.columns:
        agg_dict['Avg_Leverage'] = ('leverage', 'mean')
    if 'account' in df_merged.columns:
        agg_dict['Trade_Count'] = ('account', 'count')
    else:
        agg_dict['Trade_Count'] = ('closedPnL', 'count')

    sentiment_stats = df_merged.groupby('Classification').agg(**agg_dict).reset_index()

    print("\n--- Performance Metrics by Market Sentiment ---")
    print(sentiment_stats.to_string(index=False))

    # Visualization: Win Rate by Sentiment
    plt.figure(figsize=(8, 5))
    sns.barplot(data=sentiment_stats, x='Classification', y='Win_Rate', palette='coolwarm')
    plt.title('Trader Win Rate by Market Sentiment')
    plt.ylabel('Win Rate (%)')
    plt.ylim(0, 100)
    for i, v in enumerate(sentiment_stats['Win_Rate']):
        plt.text(i, v + 1, f"{v:.1f}%", ha='center')
    plt.show()

# %% [markdown]
# ## 5. Leverage Analysis

# %%
if len(df_merged) > 0 and 'leverage' in df_merged.columns:
    bins = [0, 5, 10, 20, 50, 101, float('inf')]
    labels = ['1-5x', '6-10x', '11-20x', '21-50x', '51-100x', '100x+']
    df_merged['leverage_tier'] = pd.cut(df_merged['leverage'], bins=bins, labels=labels)

    leverage_stats = df_merged.groupby('leverage_tier', observed=True).agg(
        Avg_PnL=('closedPnL', 'mean'),
        Trade_Count=('closedPnL', 'count')
    ).reset_index()
    # Filter out empty tiers
    leverage_stats = leverage_stats[leverage_stats['Trade_Count'] > 0]

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=leverage_stats, x='leverage_tier', y='Avg_PnL', marker='o', color='red', linewidth=2)
    plt.title('Average PnL across Leverage Tiers')
    plt.ylabel('Average PnL ($)')
    plt.xlabel('Leverage Tier')
    plt.axhline(0, color='black', linestyle='--')
    plt.show()
elif len(df_merged) > 0:
    print("\nSkipping Leverage Analysis: 'leverage' column not found in dataset.")

# %% [markdown]
# ## 6. Account-Level Profiling (Whales vs Retail)

# %%
if len(df_merged) > 0 and 'account' in df_merged.columns:
    acc_agg = {
        'Total_PnL': ('closedPnL', 'sum'),
        'Total_Volume': ('trade_volume_usd', 'sum'),
        'Win_Rate': ('is_win', 'mean'),
        'Total_Trades': ('closedPnL', 'count')
    }
    if 'leverage' in df_merged.columns:
        acc_agg['Avg_Leverage'] = ('leverage', 'mean')
        
    account_stats = df_merged.groupby('account').agg(**acc_agg)

    whale_threshold = account_stats['Total_Volume'].quantile(0.90)
    account_stats['Trader_Type'] = np.where(account_stats['Total_Volume'] >= whale_threshold, 'Whale', 'Retail')

    trader_type_agg = {
        'Mean_Total_PnL': ('Total_PnL', 'mean'),
        'Mean_Win_Rate': ('Win_Rate', lambda x: x.mean() * 100),
        'Unique_Traders': ('Total_Volume', 'count')
    }
    if 'Avg_Leverage' in account_stats.columns:
        trader_type_agg['Avg_Leverage_Used'] = ('Avg_Leverage', 'mean')

    trader_type_stats = account_stats.groupby('Trader_Type').agg(**trader_type_agg).reset_index()

    print("\n--- Account Profiling: Whales vs Retail ---")
    print(trader_type_stats.to_string(index=False))
elif len(df_merged) > 0:
    print("\nSkipping Account Profiling: 'account' column not found in dataset.")

# %% [markdown]
# ## 7. Statistical Evidence & Hypothesis Testing

# %%
if len(df_merged) > 0:
    # We test against the two most common sentiment labels, typically 'Fear' and 'Greed'
    sentiments_present = df_merged['Classification'].unique()
    
    fear_labels = [s for s in sentiments_present if 'fear' in s.lower()]
    greed_labels = [s for s in sentiments_present if 'greed' in s.lower()]
    
    if fear_labels and greed_labels:
        fear_pnl = df_merged[df_merged['Classification'].isin(fear_labels)]['closedPnL']
        greed_pnl = df_merged[df_merged['Classification'].isin(greed_labels)]['closedPnL']

        if len(fear_pnl) > 0 and len(greed_pnl) > 0:
            t_stat, p_val = stats.ttest_ind(fear_pnl, greed_pnl, equal_var=False, nan_policy='omit')

            print("\n--- Statistical Testing ---")
            print(f"T-test (Fear vs Greed PnL): t-statistic = {t_stat:.4f}, p-value = {p_val:.4e}")
            if p_val < 0.05:
                print("Result: Statistically significant difference in PnL between Fear and Greed market conditions.")
            else:
                print("Result: No statistically significant difference found (p >= 0.05).")
    
    # Correlation Testing
    if 'leverage' in df_merged.columns and df_merged['leverage'].std() > 0 and df_merged['closedPnL'].std() > 0:
        corr, p_val_corr = stats.pearsonr(df_merged['leverage'], df_merged['closedPnL'])
        print(f"\nPearson Correlation (Leverage vs PnL): r = {corr:.4f}, p-value = {p_val_corr:.4e}")
        if corr < 0 and p_val_corr < 0.05:
            print("Result: Significant negative correlation between leverage and PnL (Higher leverage -> lower PnL).")

    print("\nAnalysis Complete. Refer to Final_Report.md for business insights.")
else:
    print("\nNo data available to process. Check data sources and date overlap.")