import logging
import sqlite3
import pandas as pd
import os
from datetime import datetime

DATABASE_PATH = 'analyzer_data.db' # DBファイルをプロジェクトルートに配置

def initialize_database():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # interview_results テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interview_results (
                interview_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT NOT NULL,
                employee_id TEXT,
                interview_date TEXT NOT NULL,
                summary_positive TEXT,
                summary_negative TEXT,
                summary_action_items TEXT,
                ai_advice TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(employee_name, interview_date)
            )
        ''')

        # daily_report_summaries テーブルの作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_report_summaries (
                daily_report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT NOT NULL,
                period_start_date TEXT NOT NULL,
                summary_achievements TEXT,
                summary_issues TEXT,
                summary_next_steps TEXT,
                danger_signal TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(employee_name, period_start_date)
            )
        ''')
        conn.commit()
        logging.info("Database initialized successfully.") # ログ出力
    except sqlite3.Error as e:
        logging.error(f"Database initialization error (SQLite): {e}") # エラーログ
    except Exception as e: # その他の予期せぬエラーを捕捉
        logging.error(f"Database initialization error (General): {e}") # エラーログ
    finally:
        if conn:
            conn.close()

def save_interview_to_db(data):
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"DEBUG: Saving employee_name to DB: {data.get('employee_name')}")
        cursor.execute('''
            INSERT OR REPLACE INTO interview_results (
                employee_name, employee_id, interview_date, summary_positive, summary_negative,
                summary_action_items, ai_advice, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('employee_name'), data.get('employee_id'), data.get('interview_date'),
            data.get('summary_positive'), data.get('summary_negative'),
            data.get('summary_action_items'), data.get('ai_advice'),
            data.get('created_at', now), now # created_atがなければ現在時刻、あれば既存値
        ))
        conn.commit()
        print(f"Interview data for {data.get('employee_name')} on {data.get('interview_date')} saved to DB.")
    except sqlite3.Error as e:
        print(f"Error saving interview data to DB: {e}")
    finally:
        if conn:
            conn.close()

def save_daily_report_to_db(data):
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR REPLACE INTO daily_report_summaries (
                employee_name, period_start_date, summary_achievements,
                summary_issues, summary_next_steps, danger_signal,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('employee_name'), data.get('period_start_date'),
            data.get('summary_achievements'), data.get('summary_issues'),
            data.get('summary_next_steps'), data.get('danger_signal'),
            data.get('created_at', now), now # created_atがなければ現在時刻、あれば既存値
        ))
        conn.commit()
        print(f"Daily report data for {data.get('employee_name')} on {data.get('period_start_date')} saved to DB.")
    except sqlite3.Error as e:
        print(f"Error saving daily report data to DB: {e}")
    finally:
        if conn:
            conn.close()

def load_all_analysis_data_for_qa():
    conn = None
    interview_df = pd.DataFrame()
    daily_report_df = pd.DataFrame()
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # interview_results からデータを読み込み
        interview_query = "SELECT employee_name, employee_id, interview_date, summary_positive AS 面談結果要約, ai_advice AS AIによるアドバイス FROM interview_results"
        interview_df = pd.read_sql_query(interview_query, conn)
        if not interview_df.empty:
            interview_df = interview_df.rename(columns={'employee_name': '従業員名'}) # 列名をリネーム
            interview_df['データ種別'] = '面談要約'
            interview_count = len(interview_df)
            print(f"面談要約データ {interview_count}件をDBから読み込みました。")
        else:
            interview_count = 0
            print("DBに面談要約データが見つかりませんでした。")

        # daily_report_summaries からデータを読み込み
        daily_report_query = "SELECT employee_name, period_start_date AS 期間, summary_achievements AS 日報内容要約, danger_signal AS 危険信号, created_at AS 作成日時 FROM daily_report_summaries"
        daily_report_df = pd.read_sql_query(daily_report_query, conn)
        if not daily_report_df.empty:
            daily_report_df = daily_report_df.rename(columns={'employee_name': '従業員名'}) # 列名をリネーム
            daily_report_df['データ種別'] = '日報分析'
            daily_report_count = len(daily_report_df)
            print(f"日報分析データ {daily_report_count}件をDBから読み込みました。")
        else:
            daily_report_count = 0
            print("DBに日報分析データが見つかりませんでした。")

        combined_df = pd.concat([interview_df, daily_report_df], ignore_index=True)
        return combined_df, interview_count, daily_report_count

    except sqlite3.Error as e:
        logging.error(f"Error loading data from DB for QA: {e}")
        return pd.DataFrame(), 0, 0
    finally:
        if conn:
            conn.close()

def get_deletable_data_list():
    conn = None
    deletable_items = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # interview_results からデータを取得
        cursor.execute("SELECT employee_name, employee_id, interview_date FROM interview_results ORDER BY employee_name, interview_date")
        interview_records = cursor.fetchall()
        
        # daily_report_summaries からデータを取得
        cursor.execute("SELECT employee_name, period_start_date FROM daily_report_summaries ORDER BY employee_name, period_start_date")
        daily_report_records = cursor.fetchall()

        # 各従業員の全データ削除オプションを管理するためのセット
        processed_employees = set()

        # 面談データを整形
        for name, emp_id, date in interview_records:
            display_name = name if name else "不明な従業員"
            display_id = f"ID:{emp_id}" if emp_id else ""
            display_date = f"({date})" if date else ""
            deletable_items.append(f"{display_name} {display_id} {display_date} (面談)")
            
            # 全データ削除オプションの追加を検討
            if (name, emp_id) not in processed_employees:
                deletable_items.append(f"[まとめ] {display_name} {display_id} (全データ削除)")
                processed_employees.add((name, emp_id))

        # 日報データを整形
        for name, date in daily_report_records:
            display_name = name if name else "不明な従業員"
            # 日報データにはemployee_idがないので、ここでは表示しない
            display_date = f"({date})" if date else ""
            deletable_items.append(f"{display_name} {display_date} (日報)")

            # 全データ削除オプションの追加を検討 (面談データで既に処理済みでなければ)
            # 日報データにはemployee_idがないため、employee_nameのみで判断
            if (name, '') not in processed_employees: # employee_idがない場合は空文字列で区別
                deletable_items.append(f"[まとめ] {display_name} (全データ削除)")
                processed_employees.add((name, ''))

        return sorted(list(set(deletable_items))) # 重複を削除してソート
    except sqlite3.Error as e:
        logging.error(f"Error getting deletable data list from DB: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_record_from_db(employee_name, employee_id, date_str, is_bulk_delete):
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if is_bulk_delete:
            # 面談データの一括削除
            cursor.execute("DELETE FROM interview_results WHERE employee_name = ? AND employee_id = ?", (employee_name, employee_id))
            # 日報データの一括削除 (employee_idがないためemployee_nameのみで判断)
            cursor.execute("DELETE FROM daily_report_summaries WHERE employee_name = ?", (employee_name,))
            logging.info(f"Bulk deleted data for employee: {employee_name} (ID: {employee_id})")
        else:
            # 単一レコードの削除
            # 面談データか日報データかを判断して削除
            if "(面談)" in date_str: # 面談データの場合
                # 日付部分を抽出 (例: (2025-07-04) から 2025-07-04 を取得)
                import re
                match = re.search(r'\((.*?)\)', date_str)
                if match:
                    extracted_date = match.group(1)
                    cursor.execute("DELETE FROM interview_results WHERE employee_name = ? AND employee_id = ? AND interview_date = ?", (employee_name, employee_id, extracted_date))
                    logging.info(f"Deleted interview data for {employee_name} (ID: {employee_id}) on {extracted_date}")
                else:
                    logging.warning(f"Could not extract date from: {date_str} for interview data deletion.")
                    return False
            elif "(日報)" in date_str: # 日報データの場合
                # 日付部分を抽出 (例: (20240101-20240107) から 20240101-20240107 を取得)
                import re
                match = re.search(r'\((.*?)\)', date_str)
                if match:
                    extracted_date = match.group(1)
                    cursor.execute("DELETE FROM daily_report_summaries WHERE employee_name = ? AND period_start_date = ?", (employee_name, extracted_date))
                    logging.info(f"Deleted daily report data for {employee_name} on {extracted_date}")
                else:
                    logging.warning(f"Could not extract date from: {date_str} for daily report data deletion.")
                    return False
            else:
                logging.warning(f"Unknown data type for deletion: {date_str}")
                return False
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        logging.error(f"Error deleting record from DB: {e}")
        return False
    finally:
        if conn:
            conn.close()