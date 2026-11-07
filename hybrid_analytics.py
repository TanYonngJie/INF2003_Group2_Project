import pandas as pd
from db_controller import get_pg_connection, get_mongo_collection

def analyze_cart_abandonment():
    print("1. Extracting 'cart' events from MongoDB...")
    mongo_col = get_mongo_collection()
    
    cart_cursor = mongo_col.find({"event_type": "cart"}, {"_id": 0, "user_id": 1, "product_id": 1})
    carts_df = pd.DataFrame(list(cart_cursor))
    
    if carts_df.empty:
        print("No cart events found in MongoDB.")
        return
        
    carts_df = carts_df.drop_duplicates()

    print("2. Extracting 'purchase' receipts from PostgreSQL...")
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, product_id FROM purchases;")
    
    # RealDictCursor returns dictionaries, which Pandas converts perfectly
    purchases_df = pd.DataFrame(cur.fetchall()) 
    
    cur.close()
    conn.close()

    # Force casting happens here, exactly after both DataFrames have been created
    carts_df['user_id'] = carts_df['user_id'].astype(int)
    carts_df['product_id'] = carts_df['product_id'].astype(int)
    purchases_df['user_id'] = purchases_df['user_id'].astype(int)
    purchases_df['product_id'] = purchases_df['product_id'].astype(int)

    print("3. Merging datasets to find abandoned carts...")
    merged_df = carts_df.merge(purchases_df, on=['user_id', 'product_id'], how='left', indicator=True)
    
    abandoned_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

    total_carts = len(carts_df)
    total_abandoned = len(abandoned_df)
    abandonment_rate = (total_abandoned / total_carts) * 100 if total_carts > 0 else 0

    print("-" * 40)
    print("=== CART ABANDONMENT REPORT ===")
    print(f"Total Unique Carts: {total_carts}")
    print(f"Total Abandoned:    {total_abandoned}")
    print(f"Abandonment Rate:   {abandonment_rate:.2f}%")
    print("-" * 40)
    
    if not abandoned_df.empty:
        print("\nSample of Users who abandoned their carts (User ID | Product ID):")
        print(abandoned_df.head(5).to_string(index=False))

if __name__ == "__main__":
    analyze_cart_abandonment()