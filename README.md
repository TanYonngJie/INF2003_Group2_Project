# Hybrid Database E-Commerce Dashboard

## Setup Instructions

### Step 1. Download MongoDB (If not downloaded)

### Step 2. Download PostgreSQL (PgAdmin4) (From https://www.postgresql.org/download/)
- Leave everything as default (including file path).
- Set your master password and remember it for later use.
- Leave port as `5432`.
- When prompted to install additional applications via Stack Builder, press **Cancel**.

### Step 3. Download & Extract Project Folder

### Step 4. Open MongoDB & Establish New Connection
- Create a new database under your connection:
  - **Database Name:** `ecommerce`
  - **Collection Name:** `behavior_logs`
- Click the green **Add Data** button.
- Import `mongo_setup.json`.
- MongoDB setup is complete.

### Step 5. Open PgAdmin4
- Press the white arrow next to PostgreSQL 18 to expand the folder.
- Enter your master password.
- Right-click **Databases** and create a new database called `ecommerce_sql`.

### Step 6. Open Coding Platform (VS Code Preferred)
- Open your terminal *inside* the project folder.
- Run the following command to install required dependencies:
  ```bash
  pip install -r requirements.txt
