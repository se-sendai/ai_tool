import sqlite3
import pandas as pd
import sys
import os

# プロジェクトルートをsys.pathに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database_handler

DATABASE_PATH = 'analyzer_data.db'

def inspect_database():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:")
        for table_name_tuple in tables:
            table_name = table_name_tuple[0]
            print(f"\n--- Table: {table_name} ---")
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", conn)
                if not df.empty:
                    print(df.to_string())
                else:
                    print("  (Table is empty or no data found)")
            except pd.io.sql.DatabaseError as e:
                print(f"  Error reading table {table_name}: {e}")
            except Exception as e:
                print(f"  An unexpected error occurred while reading table {table_name}: {e}")

        print("\n--- Checking load_all_analysis_data_for_qa() output ---")
        combined_df, interview_count, daily_report_count = database_handler.load_all_analysis_data_for_qa()
        print(f"Combined DataFrame columns: {combined_df.columns.tolist()}")
        print(f"Interview count: {interview_count}")
        print(f"Daily report count: {daily_report_count}")
        if not combined_df.empty:
            print("First 5 rows of combined_df:")
            print(combined_df.head().to_string())
        else:
            print("Combined DataFrame is empty.")

    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_database()