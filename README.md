# Hybrid Database E-Commerce Dashboard

## Setup Instructions

**1. Install Dependencies**
Run this command in the terminal to install the required Python libraries:
pip install -r requirements.txt

**2. Database Setup**
*   **PostgreSQL:** Install PgAdmin4 and create a database named `ecommerce_sql`. Run the provided `postgres_setup.sql` script to build the tables and insert the data.
*   **MongoDB:** Install MongoDb and create a database named `ecommerce`. Import the provided `mongo_setup.json` file into a collection named `behavior_logs`.

**3. Configure Credentials**
Open `db_controller.py` and update the `PG_PASSWORD` variable to match your local PostgreSQL password, default password for code is Password1234

**4. Run the App**
Run this command in the terminal to start the application:
streamlit run app.py
