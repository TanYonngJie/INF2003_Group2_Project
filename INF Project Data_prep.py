import pandas as pd

# 1. Load a manageable 100,000 row chunk of the massive CSV
print("Loading data...")
file_path = '2019-Oct.csv'
df = pd.read_csv(file_path, nrows=100000)

# 2. Clean the data by dropping rows missing critical schema information
print("Cleaning data...")
df_clean = df.dropna(subset=['category_code', 'brand', 'user_session'])

# 3. Split the data for the Relational (PostgreSQL) database
# We only want actual purchases for the transactional database
print("Isolating PostgreSQL purchases...")
postgresql_purchases = df_clean[df_clean['event_type'] == 'purchase'].copy()
postgresql_purchases.to_csv('sql_purchases_clean.csv', index=False)

# 4. Split the data for the Non-Relational (MongoDB) database
# We want views and cart additions for the behavioral ledger
print("Isolating MongoDB behavioral logs...")
mongodb_behavior = df_clean[df_clean['event_type'].isin(['view', 'cart'])].copy()
mongodb_behavior.to_csv('nosql_behavior_clean.csv', index=False)

print("Success! Created 'sql_purchases_clean.csv' and 'nosql_behavior_clean.csv'.")