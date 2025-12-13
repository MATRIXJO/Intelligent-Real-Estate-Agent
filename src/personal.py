import mysql.connector
import json
import os
from mysql.connector import Error

# Database Configuration from Environment Variables
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASS", ""), # Ensure you export this env var!
    'database': os.getenv("DB_NAME", "user_data_db")
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            user_id VARCHAR(255) PRIMARY KEY,
            profile_json JSON
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(255),
            doc_id VARCHAR(255),
            liked TINYINT(1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
    except Error as e:
        print(f"Error initializing DB: {e}")
    finally:
        cursor.close()
        conn.close()

def save_profile(user_id, profile_dict):
    """Saves or updates a user profile in MySQL."""
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO profiles (user_id, profile_json)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE profile_json = VALUES(profile_json)
        """
        cursor.execute(sql, (user_id, json.dumps(profile_dict)))
        conn.commit()
    except Error as e:
        print(f"Error saving profile: {e}")
    finally:
        cursor.close()
        conn.close()

def load_profile(user_id):
    conn = get_db_connection()
    if not conn: return {}
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT profile_json FROM profiles WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        if result:
            data = result[0]
            return json.loads(data) if isinstance(data, str) else data
        return {}
    except Error as e:
        print(f"Error loading profile: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def save_feedback(user_id, doc_id, liked):
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO feedback (user_id, doc_id, liked) VALUES (%s, %s, %s)", 
            (user_id, doc_id, int(bool(liked)))
        )
        conn.commit()
    except Error:
        pass
    finally:
        cursor.close()
        conn.close()
