# Hybrid Database E-Commerce Dashboard

## Setup Instructions

**1. Install Dependencies**
Run this command in the terminal to install the required Python libraries:
pip install -r requirements.txt

**2. Database Setup**
*   **PostgreSQL:** Create a database named `ecommerce_sql`. Run the provided `postgres_setup.sql` script to build the tables and insert the data.
*   **MongoDB:** Create a database named `ecommerce`. Import the provided `mongo_setup.json` file into a collection named `behavior_logs`.

**3. Configure Credentials**
Open `db_controller.py` and update the `PG_PASSWORD` variable to match your local PostgreSQL password.

**4. Run the App**
Run this command in the terminal to start the application:
streamlit run app.py