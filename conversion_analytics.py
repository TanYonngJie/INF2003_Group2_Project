import pandas as pd
from db_controller import get_pg_connection, get_mongo_collection

def analyze_top_products():
    print("1. Querying MongoDB for the top 5 most viewed products...")
    mongo_col = get_mongo_collection()
    
    # Aggregation pipeline to count 'view' events per product_id
    pipeline = [
        {"$match": {"event_type": "view"}},
        {"$group": {"_id": "$product_id", "view_count": {"$sum": 1}}},
        {"$sort": {"view_count": -1}},
        {"$limit": 5}
    ]
    
    top_views = list(mongo_col.aggregate(pipeline))
    views_df = pd.DataFrame(top_views).rename(columns={"_id": "product_id"})
    
    if views_df.empty:
        print("No view events found.")
        return
        
    # Extract the top 5 product IDs to send to PostgreSQL
    top_product_ids = tuple(views_df['product_id'].astype(int).tolist())

    print("2. Querying PostgreSQL for purchases of these specific 5 products...")
    conn = get_pg_connection()
    cur = conn.cursor()
    
    # Count purchases only for the 5 most viewed items
    query = """
        SELECT product_id, COUNT(purchase_id) as purchase_count 
        FROM purchases 
        WHERE product_id IN %s 
        GROUP BY product_id;
    """
    cur.execute(query, (top_product_ids,))
    purchases_df = pd.DataFrame(cur.fetchall())
    
    cur.close()
    conn.close()

    print("3. Calculating conversion rates...")
    # Merge the views and purchases
    if not purchases_df.empty:
        # Ensure datatypes match for merging
        views_df['product_id'] = views_df['product_id'].astype(int)
        purchases_df['product_id'] = purchases_df['product_id'].astype(int)
        
        merged_df = views_df.merge(purchases_df, on='product_id', how='left')
        merged_df['purchase_count'] = merged_df['purchase_count'].fillna(0)
    else:
        merged_df = views_df.copy()
        merged_df['purchase_count'] = 0

    # Calculate the percentage of views that turned into purchases
    merged_df['conversion_rate'] = (merged_df['purchase_count'] / merged_df['view_count']) * 100

    print("-" * 55)
    print("=== TOP 5 VIEWED PRODUCTS CONVERSION REPORT ===")
    print("-" * 55)
    
    # Format the output for clean terminal reading
    for index, row in merged_df.iterrows():
        pid = int(row['product_id'])
        views = int(row['view_count'])
        purchases = int(row['purchase_count'])
        rate = row['conversion_rate']
        print(f"Product ID: {pid} | Views: {views} | Purchases: {purchases} | Conversion: {rate:.2f}%")
        
if __name__ == "__main__":
    analyze_top_products()