import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient

# --- CONFIGURATION ---
PG_PASSWORD = "Password1234" 
PG_HOST = "localhost"
PG_DB = "ecommerce_sql"
PG_USER = "postgres"
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "ecommerce"

# --- CONNECTION FUNCTIONS ---
def get_pg_connection():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
        cursor_factory=RealDictCursor
    )

def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db["behavior_logs"]

# --- DATABASE OPERATIONS ---

def log_mongo_event(user_id, event_type, product_id, category_code, session_id):
    """Inserts a new behavioral log into MongoDB."""
    logs = get_mongo_collection()
    doc = {
        "user_id": user_id,
        "event_type": event_type,
        "product_id": product_id,
        "category_code": category_code,
        "user_session": session_id
    }
    result = logs.insert_one(doc)
    print(f"[MongoDB Success] Inserted '{event_type}' event with ID: {result.inserted_id}")

def get_pg_user_purchases(user_id, selected_columns=None):
    """Dynamically builds a multi-table SQL query based ONLY on ticked boxes."""
    conn = get_pg_connection()
    cur = conn.cursor()
    
    # Map the UI checkboxes to their actual database table aliases
    col_mapping = {
        "purchase_id": "p.purchase_id",
        "event_time": "p.event_time",
        "product_id": "pr.product_id",
        "brand": "pr.brand",
        "category_code": "c.category_code",
        "purchase_price": "p.purchase_price"
    }

    # Force PostgreSQL to strictly SELECT only the requested columns
    if not selected_columns:
        select_clause = ", ".join(col_mapping.values())
    else:
        select_clause = ", ".join([col_mapping[c] for c in selected_columns if c in col_mapping])

    query = f"""
        SELECT {select_clause}
        FROM 
            purchases p,
            products pr,
            categories c
        WHERE 
            p.user_id = %s
            AND p.product_id = pr.product_id
            AND pr.category_id = c.category_id;
    """
    cur.execute(query, (user_id,))
    records = cur.fetchall()
    cur.close()
    conn.close()
    return records

# --- QUICK VERIFICATION TEST ---
if __name__ == "__main__":
    print("Testing MongoDB Connection...")
    log_mongo_event(
        user_id=99999999,
        event_type="cart",
        product_id=1004856,
        category_code="electronics.smartphone",
        session_id="test_session_123"
    )

    print("\nTesting PostgreSQL Connection...")
    sample_user = 543272936 
    # Passing None here acts as if all checkboxes were ticked for the terminal test
    purchases = get_pg_user_purchases(sample_user, selected_columns=None)
    
    print(f"[PostgreSQL Success] Found {len(purchases)} purchases for user {sample_user}:")
    for row in purchases:
        print(dict(row))