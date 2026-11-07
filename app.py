import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from db_controller import get_pg_connection, get_pg_user_purchases, get_mongo_collection

# --- PAGE SETUP ---
st.set_page_config(page_title="Hybrid DB Demo", layout="wide")
st.title("🛒 eCommerce Hybrid Database Demo")
st.markdown("**PostgreSQL & MongoDB Integration System**")

# Create 4 tabs to keep the UI clean
tab1, tab2, tab3, tab4= st.tabs([
    "User Profile Lookup", 
    "Cart Abandonment", 
    "Top Products Conversion",
    "Sales Analytics"
])

# --- TAB 1: USER PROFILE LOOKUP ---
with tab1:
    st.subheader("Cross-Database Customer Search")
    st.write("Fetch financial data from PostgreSQL and behavioral data from MongoDB simultaneously.")
    
    purchase_ids = [531531043, 513668525, 518645197, 544929585, 517438679]
    abandonment_ids = [536415846, 513852171, 519840569, 554507659, 512766455]

    st.markdown(f"**💡 Quick Test IDs (Conversion / Purchases):** `{', '.join(map(str, purchase_ids))}`")
    st.markdown(f"**💡 Quick Test IDs (Cart Abandonment):** `{', '.join(map(str, abandonment_ids))}`")

    user_id_input = st.text_input("Enter User ID:", value=str(purchase_ids[0]), key="tab1_user_input")

    all_available_columns = ["purchase_id", "event_time", "product_id", "brand", "category_code", "purchase_price"]
    current_selections = []
    
    with st.expander("Toggle Columns", expanded=True):
        for col in all_available_columns:
            if st.checkbox(col, value=True, key=f"pre_search_{col}"):
                current_selections.append(col)

    def execute_database_search():
        current_user_id = st.session_state.tab1_user_input
        
        # 1. FETCH MONGODB DATA (Behavior logs)
        mongo_client = MongoClient("mongodb://localhost:27017/")
        db = mongo_client["ecommerce"]
        events_collection = db["behavior_logs"]
        
        try:
            search_id = int(current_user_id)
        except ValueError:
            search_id = current_user_id
            
        st.session_state.user_events = list(events_collection.find({"user_id": search_id}))
        mongo_client.close()

        # 2. FETCH STRICT POSTGRESQL DATA BASED ON CHECKBOXES
        try:
            st.session_state.pg_purchases = get_pg_user_purchases(int(current_user_id), current_selections)
        except ValueError:
            st.session_state.pg_purchases = get_pg_user_purchases(current_user_id, current_selections)

    metric_choice = st.radio(
        "Select Metric to View:",
        ["Conversion Rate", "Cart Abandonment"],
        horizontal=True,
        key="tab1_metric_choice",
        on_change=execute_database_search
    )

    if "pg_purchases" not in st.session_state:
        st.session_state.pg_purchases = None
    if "user_events" not in st.session_state:
        st.session_state.user_events = []

    st.button("Search User Profile", key="tab1_search_btn", on_click=execute_database_search)

    if st.session_state.pg_purchases is not None:
        user_events = st.session_state.user_events
        views = sum(1 for e in user_events if e.get('event_type') == 'view')
        carts = sum(1 for e in user_events if e.get('event_type') == 'cart')

        pg_purchases = st.session_state.pg_purchases
        purchases_count = len(pg_purchases) if pg_purchases is not None else 0

        conversion_rate = (purchases_count / views * 100) if views > 0 else 0.0
        cart_abandoned = "Yes" if (carts > 0 and purchases_count == 0) else "No"

        if metric_choice == "Conversion Rate":
            col1, col2 = st.columns(2)
            col1.metric("Total Views", views)
            col2.metric("Conversion Rate", f"{conversion_rate:.2f}%")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Total Cart Adds", carts)
            col2.metric("Cart Abandoned?", cart_abandoned)

        st.markdown("---")
        
        st.subheader("User Purchase History (PostgreSQL)")
        
        if len(pg_purchases) > 0:
            df_purchases = pd.DataFrame(pg_purchases)
            # Renders exactly what the database returned
            st.dataframe(df_purchases, use_container_width=True)
        else:
            st.info("No finalized purchases found for this user in PostgreSQL.")
            
# --- TAB 2: CART ABANDONMENT REPORT ---
with tab2:
    st.subheader("Hybrid Analytics: Cart Abandonment")
    st.write("Subtracts strictly verified SQL purchases from NoSQL intent logs.")
    
    if st.button("Generate Abandonment Report"):
        with st.spinner("Querying both databases..."):
            # 1. Fetch NoSQL Carts
            mongo_col = get_mongo_collection()
            cart_cursor = mongo_col.find({"event_type": "cart"}, {"_id": 0, "user_id": 1, "product_id": 1})
            carts_df = pd.DataFrame(list(cart_cursor)).drop_duplicates()
            
            # 2. Fetch SQL Purchases
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT user_id, product_id FROM purchases;")
            purchases_df = pd.DataFrame(cur.fetchall())
            cur.close()
            conn.close()

            # 3. Cast & Merge
            carts_df['user_id'] = carts_df['user_id'].astype(int)
            carts_df['product_id'] = carts_df['product_id'].astype(int)
            purchases_df['user_id'] = purchases_df['user_id'].astype(int)
            purchases_df['product_id'] = purchases_df['product_id'].astype(int)

            merged_df = carts_df.merge(purchases_df, on=['user_id', 'product_id'], how='left', indicator=True)
            abandoned_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])

            # 4. Calculate Metrics
            total_carts = len(carts_df)
            total_abandoned = len(abandoned_df)
            rate = (total_abandoned / total_carts) * 100 if total_carts > 0 else 0

            # 5. Display Clean UI Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Unique Carts", total_carts)
            col2.metric("Abandoned Carts", total_abandoned)
            col3.metric("Abandonment Rate", f"{rate:.2f}%")
            
            st.write("Sample of Users with Abandoned Carts:")
            abandoned_df = abandoned_df.reset_index(drop=True)
            abandoned_df.index = abandoned_df.index + 1
            st.dataframe(abandoned_df.head(10), use_container_width=True)

# --- TAB 3: TOP PRODUCTS CONVERSION ---
with tab3:
    st.subheader("Hybrid Analytics: Top 5 Products Conversion")
    st.write("Matches the 5 most viewed NoSQL items against finalized SQL receipts.")
    
    if st.button("Generate Conversion Report"):
        with st.spinner("Running MongoDB Aggregation Pipeline..."):
            # 1. MongoDB Aggregation
            mongo_col = get_mongo_collection()
            pipeline = [
                {"$match": {"event_type": "view"}},
                {"$group": {"_id": "$product_id", "view_count": {"$sum": 1}}},
                {"$sort": {"view_count": -1}},
                {"$limit": 5}
            ]
            views_df = pd.DataFrame(list(mongo_col.aggregate(pipeline))).rename(columns={"_id": "product_id"})
            top_product_ids = tuple(views_df['product_id'].astype(int).tolist())

            # 2. SQL Check
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT product_id, COUNT(purchase_id) as purchase_count FROM purchases WHERE product_id IN %s GROUP BY product_id;", (top_product_ids,))
            purchases_df = pd.DataFrame(cur.fetchall())
            cur.close()
            conn.close()

            # 3. Cast & Merge
            views_df['product_id'] = views_df['product_id'].astype(int)
            if not purchases_df.empty:
                purchases_df['product_id'] = purchases_df['product_id'].astype(int)
                merged_df = views_df.merge(purchases_df, on='product_id', how='left')
                merged_df['purchase_count'] = merged_df['purchase_count'].fillna(0)
            else:
                merged_df = views_df.copy()
                merged_df['purchase_count'] = 0

            merged_df['conversion_rate (%)'] = (merged_df['purchase_count'] / merged_df['view_count']) * 100

            merged_df = merged_df.sort_values(by='conversion_rate (%)', ascending=False)
            merged_df = merged_df.reset_index(drop=True)
            merged_df.index = merged_df.index + 1
            
            # 4. Display
            st.dataframe(merged_df.style.format({'conversion_rate (%)': '{:.2f}'}), use_container_width=True)


with tab4: 
    st.header("eCommerce Data Visualizations")
    
    # 1. Fetch data directly into a pandas DataFrame 
    conn = get_pg_connection()
    query = """
        SELECT 
             p.event_time, 
            pr.brand, 
            c.category_code, 
            p.purchase_price, 
            p.user_id 
        FROM purchases p
        JOIN products pr ON p.product_id = pr.product_id
        JOIN categories c ON pr.category_id = c.category_id
        WHERE pr.brand IS NOT NULL;
    """
    # Load directly to DataFrame for easy matplotlib plotting
    cur = conn.cursor()
    cur.execute(query)
    records = cur.fetchall()
    df = pd.DataFrame(records)
    cur.close()
    conn.close()

    if not df.empty:
        # Convert database Decimals to standard Python floats for matplotlib
        df['purchase_price'] = df['purchase_price'].astype(float)
    
        # Convert timestamp to datetime for time-series charts
        df['event_time'] = pd.to_datetime(df['event_time'])

        col1, col2 = st.columns(2)

        with col1:
            # --- SCATTER PLOT (Lab Q5) ---
            st.subheader("1. User Spend vs. Items Bought")
            # Aggregate data per user
            user_stats = df.groupby('user_id').agg(
                total_spend=('purchase_price', 'sum'),
                items_bought=('purchase_price', 'count')
            )
            fig_scatter, ax_scatter = plt.subplots()
            ax_scatter.scatter(user_stats['items_bought'], user_stats['total_spend'], alpha=0.5, color='purple')
            ax_scatter.set_xlabel("Number of Items Bought")
            ax_scatter.set_ylabel("Total Spend ($)")
            st.pyplot(fig_scatter)

            # --- BOX PLOT (Lab Q8) ---
            st.subheader("3. Price Distribution: Samsung vs Apple")
            # Filter for two specific brands
            samsung_prices = df[df['brand'] == 'samsung']['purchase_price'].dropna()
            apple_prices = df[df['brand'] == 'apple']['purchase_price'].dropna()
            
            fig_box, ax_box = plt.subplots()
            ax_box.boxplot([samsung_prices, apple_prices], labels=['Samsung', 'Apple'])
            ax_box.set_ylabel("Purchase Price ($)")
            st.pyplot(fig_box)

            # --- BAR CHART (Lab Q10) ---
            st.subheader("5. Revenue by Top Categories")
            top_cats = df.groupby('category_code')['purchase_price'].sum().sort_values(ascending=False).head(10)
            
            fig_bar, ax_bar = plt.subplots(figsize=(10, 6)) # Wider figure as suggested in Q10
            ax_bar.bar(top_cats.index, top_cats.values, color='teal')
            ax_bar.set_ylabel("Total Revenue ($)")
            plt.xticks(rotation=90) # Rotate x-ticks 90 degrees as requested in Q10
            st.pyplot(fig_bar)

        with col2:
            # --- HISTOGRAM (Lab Q6 & Q7) ---
            st.subheader("2. Price Distribution (50 Bins)")
            fig_hist, ax_hist = plt.subplots()
            # Plotting price distribution with exactly 50 bins as requested in Q7
            ax_hist.hist(df['purchase_price'], bins=50, color='skyblue', edgecolor='black')
            ax_hist.set_xlabel("Price ($)")
            ax_hist.set_ylabel("Frequency")
            st.pyplot(fig_hist)


            # --- LINE CHART / TREND (Lab Q9) ---
            st.subheader("4. Hourly Purchase Trend")

            # Extract the hour instead of the date
            df['hour'] = df['event_time'].dt.hour

            # Group by hour
            hourly_sales = df.groupby('hour')['purchase_price'].sum()

            fig_line, ax_line = plt.subplots()
            ax_line.plot(hourly_sales.index, hourly_sales.values, marker='o', linestyle='-', color='orange')
            ax_line.set_xlabel("Hour of Day (0-23)")
            ax_line.set_ylabel("Hourly Revenue ($)")
            plt.xticks(rotation=0)
            st.pyplot(fig_line)

            # --- PIE CHART (Lab Q11) ---
            st.subheader("6. Brand Market Share")
            top_brands = df['brand'].value_counts().head(5)
            
            fig_pie, ax_pie = plt.subplots()
            ax_pie.pie(top_brands.values, labels=top_brands.index, autopct='%1.1f%%', startangle=90)
            ax_pie.axis('equal') # Ensures pie is drawn as a perfect circle
            st.pyplot(fig_pie)