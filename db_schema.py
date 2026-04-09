import sqlite3
import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

DB_FILE_PATH = os.getenv('DB_FILE_PATH')
DB_FILE_NAME = os.getenv('DB_FILE_NAME')

connection = None

def create_connection():
    os.makedirs(DB_FILE_PATH, exist_ok=True)
    return sqlite3.connect(DB_FILE_PATH + DB_FILE_NAME)

def __get_connection():
    global connection
    if connection is None:
        connection = create_connection()
    return connection

def initialize_schema_if_missing():
    conn = __get_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS servers(server_id, server_name)')
    cursor.execute('CREATE TABLE IF NOT EXISTS runs(run_id INTEGER PRIMARY KEY AUTOINCREMENT, server_id, dungeon_name, key_level, completion_time)')
    cursor.execute('CREATE TABLE IF NOT EXISTS participants(run_id, server_id, user_id, role)')
    cursor.close()
    conn.close()
    print("Successfully validated schema and db connection")
    return

