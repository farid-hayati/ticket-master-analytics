import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"

# Load the .env file explicitly from the root path
load_dotenv(dotenv_path=ENV_PATH)

load_dotenv()
db_host = os.getenv("DB_HOST")
db_port = int(os.getenv("DB_PORT"))
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

conn = psycopg2.connect(
    host=db_host,
    dbname=db_name,
    user=db_user,
    password=db_password,
    port=db_port
)

cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS venues(
        venue_id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        city VARCHAR(100),
        state VARCHAR(50),
        country VARCHAR(50),
        postal_code VARCHAR(20),
        longitude NUMERIC(9,6),
        latitude NUMERIC(9,6)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS attractions(
        attraction_id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        segment VARCHAR(30),
        genre VARCHAR(30),
        subgenre VARCHAR(30)
    );
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS events(
        event_id VARCHAR(255) PRIMARY KEY,
        name VARCHAR(255),
        date TIMESTAMPTZ,
        min_price NUMERIC(10,2),
        max_price NUMERIC(10,2),
        segment VARCHAR(30),
        genre VARCHAR(30),
        subgenre VARCHAR(30),
        venue_id VARCHAR(255),
        attraction_id VARCHAR(255),
        status VARCHAR(30),
        date_on_sale TIMESTAMPTZ,
        FOREIGN KEY (venue_id) REFERENCES venues(venue_id) ON DELETE CASCADE,
        FOREIGN KEY (attraction_id) REFERENCES attractions(attraction_id) ON DELETE CASCADE
    );
""")

conn.commit()

cur.close()
conn.close()