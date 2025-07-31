import pandas as pd
import google.generativeai as genai
import configparser
import logging
from datetime import datetime, timedelta
import os
import requests # Ollama用
import json # AI応答パース用
import time # リトライ処理用
import database_handler # 追加
from constants import ( # 定数をインポート
    AnalysisMode, ColumnName, UIDefaults, ConfigKeys, FileAndDir, DataStructure,
    DEFAULT_COMMENT_ITEMS
)

# --- 1. 基本設定 ---
# ロギング設定
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_filename = os.path.join(log_dir, datetime.now().strftime('%Y%m%d_%H%M%S_processing.log'))
# GUI用にハンドラを保持しておく
log_handler_file = logging.FileHandler(log_filename, encoding='utf-8')
log_handler_stream = logging.StreamHandler()
log_handler_stream.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
log_handler_stream.setLevel(logging.INFO)
if hasattr(log_handler_stream, 'stream') and log_handler_stream.stream is not None:
    try:
        log_handler_stream.stream.reconfigure(encoding='utf-8')
    except Exception as e:
        # ストリームがreconfigureをサポートしていない場合や、その他のエラーをキャッチ
        logging.warning(f"Stream reconfigure failed: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[log_handler_file, log_handler_stream]
)

# グローバル変数でAIバックエンドとモデルを保持
AI_BACKEND = None
OLLAMA_URL = None
OLLAMA_MODEL = None
GEMINI_MODEL = None # 追加
DAILY_REPORT_PERIOD = None # 日報集計期間設定

# --- 2. 設定ファイル読み込み ---
def load_config():
    """config.iniから設定を読み込む"""
    global AI_BACKEND, OLLAMA_URL, OLLAMA_MODEL, DAILY_REPORT_PERIOD
    config = configparser.ConfigParser()
    try:
        logging.debug("Attempting to read config.ini.")
        config.read(FileAndDir.CONFIG_FILE, encoding='utf-8')
        logging.debug(f"config.ini sections: {config.sections()}")
        AI_BACKEND = config[ConfigKeys.AI_BACKEND_SECTION][ConfigKeys.AI_BACKEND].lower()
        if AI_BACKEND not in [ConfigKeys.GEMINI, ConfigKeys.OLLAMA]:
            logging.error(f"config.iniの[{ConfigKeys.AI_BACKEND_SECTION}]セクションの'{ConfigKeys.AI_BACKEND}'は'{ConfigKeys.GEMINI}'または'{ConfigKeys.OLLAMA}'である必要があります。")
            return False
        if AI_BACKEND == ConfigKeys.GEMINI:
            api_key = config[ConfigKeys.GEMINI_SECTION][ConfigKeys.API_KEY]
            if api_key == 'YOUR_API_KEY' or not api_key:
                logging.error("Gemini APIが選択されていますが、APIキーがconfig.iniに設定されていません。")
                return False
            genai.configure(api_key=api_key)
            global GEMINI_MODEL # グローバル変数を宣言
            GEMINI_MODEL = config[ConfigKeys.GEMINI_SECTION].get(ConfigKeys.MODEL_VERSION, 'gemini-2.0-flash') # model_versionを読み込み、デフォルト値を設定
            logging.info(f"Gemini APIが正常に設定されました。使用モデル: {GEMINI_MODEL}")
        elif AI_BACKEND == ConfigKeys.OLLAMA:
            OLLAMA_URL = config[ConfigKeys.OLLAMA_SECTION][ConfigKeys.OLLAMA_URL]
            OLLAMA_MODEL = config[ConfigKeys.OLLAMA_SECTION][ConfigKeys.OLLAMA_MODEL]
            if not OLLAMA_URL or not OLLAMA_MODEL:
                logging.error("Ollamaが選択されていますが、URLまたはモデル名がconfig.iniに設定されていません。")
                return False
            logging.info(f"Ollamaバックエンドが設定されました。URL: {OLLAMA_URL}, モデル: {OLLAMA_MODEL}")
        DAILY_REPORT_PERIOD = config[ConfigKeys.DAILY_REPORT_SECTION][ConfigKeys.PERIOD].lower()
        logging.debug(f"DAILY_REPORT_PERIOD set to {DAILY_REPORT_PERIOD}.")
        if DAILY_REPORT_PERIOD not in [ConfigKeys.WEEKLY, ConfigKeys.MONTHLY]:
            logging.error(f"config.iniの[{ConfigKeys.DAILY_REPORT_SECTION}]セクションの'{ConfigKeys.PERIOD}'は'{ConfigKeys.WEEKLY}'または'{ConfigKeys.MONTHLY}'である必要があります。")
            return False
        logging.info(f"日報集計期間が'{DAILY_REPORT_PERIOD}'に設定されました。")
        logging.debug("load_config successful.")
        return True
    except Exception as e:
        logging.debug(f"Error loading config.ini: {e}")
        logging.error(f"config.iniの読み込み中にエラーが発生しました: {e}")
        return False

# --- 3. AI呼び出し関数（共通化） ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10

# テキストチャンクの最大サイズ（文字数）
# Gemini 2.0 Flashの入力トークン制限を考慮し、安全な値を設定
# 経験的に、日本語の場合、1文字あたり約1.5トークンと仮定し、
# 128kトークン制限のモデルに対して、プロンプトや応答のオーバーヘッドを考慮して
# 80,000文字程度を上限とする。
# ただし、これはあくまで目安であり、実際のトークン数とは異なる場合がある。
# より厳密な制御が必要な場合は、トークナイザーを使用する必要がある。
CHUNK_SIZE = 80000 # 8万文字

def split_text_into_chunks(text, chunk_size):
    """テキストを指定されたチャンクサイズに分割する"""
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


def call_ai_model(prompt, model_type="generative"):
    """AIバックエンドに応じてモデルを呼び出す共通関数"""
    for attempt in range(MAX_RETRIES):
        try:
            if AI_BACKEND == ConfigKeys.GEMINI:
                logging.info(f"        DEBUG: Attempting to initialize Gemini model ({GEMINI_MODEL}).")
                try:
                    model = genai.GenerativeModel(GEMINI_MODEL)
                    logging.info("        DEBUG: Gemini model initialized successfully.")
                except Exception as e:
                    logging.error(f"        ERROR: Failed to initialize Gemini model: {e}")
                    raise e # リトライのために例外を再送出

                logging.info(f"        DEBUG: Calling generate_content with timeout=60...")
                response = model.generate_content(prompt, request_options={'timeout': 60})
                logging.info("        DEBUG: generate_content call finished.")
                
                # response.textがNoneでないことを確認
                if response and hasattr(response, 'text') and response.text:
                    logging.info("        Gemini API応答受信")
                    logging.info(f"        DEBUG: Gemini API response text (first 100 chars): {response.text[:100]}...")
                    return response.text.strip()
                else:
                    # レスポンスにテキストがない場合、問題の詳細をログに出力
                    logging.error(f"        ERROR: Gemini API response is empty or invalid. Response object: {response}")
                    # レスポンスにプロンプトフィードバックがあるか確認
                    if response and hasattr(response, 'prompt_feedback'):
                        logging.error(f"        Prompt Feedback: {response.prompt_feedback}")
                    logging.error("        DEBUG: call_ai_model returning None due to empty/invalid response.")
                    return None # 不正なレスポンスの場合はNoneを返す

            elif AI_BACKEND == ConfigKeys.OLLAMA:
                headers = {'Content-Type': 'application/json'}
                data = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
                response = requests.post(f"{OLLAMA_URL}/api/generate", headers=headers, json=data, timeout=60) # タイムアウトを60秒に設定
                response.raise_for_status()
                return response.json()['response'].strip()
        except requests.exceptions.Timeout:
            logging.warning(f"AI API呼び出しがタイムアウトしました (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except requests.exceptions.RequestException as e:
            logging.warning(f"AI API呼び出し中にエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        except Exception as e:
            logging.error(f"予期せぬエラーが発生しました: {e} (試行 {attempt + 1}/{MAX_RETRIES})。再試行します...")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY_SECONDS)
    
    logging.error(f"AI API呼び出しが{MAX_RETRIES}回試行されましたが、すべて失敗しました。")
    return None

def get_summary_from_ai(interview_data_text):
    """AIを使用して面談データ全体のテキストを要約する"""
    if not interview_data_text:
        return "要約できませんでした"

    logging.info("    AIに面談データ全体の要約をリクエスト中...")

    if len(interview_data_text) > CHUNK_SIZE:
        logging.info(f"    入力テキストが大きすぎるため、チャンクに分割して段階的に要約します。テキスト長: {len(interview_data_text)}")
        chunks = split_text_into_chunks(interview_data_text, CHUNK_SIZE)
        chunk_summaries = []

        for i, chunk in enumerate(chunks):
            logging.info(f"    チャンク {i+1}/{len(chunks)} を要約中...")
            chunk_prompt = f"""以下のテキストを要約してください。\n\n{chunk}"""
            summary = call_ai_model(chunk_prompt)
            if summary:
                chunk_summaries.append(summary)
            else:
                logging.warning(f"    チャンク {i+1} の要約に失敗しました。")

        if not chunk_summaries:
            logging.error("    すべてのチャンクの要約に失敗しました。")
            return "要約できませんでした"

        combined_summaries_text = "\n\n".join(chunk_summaries)
        logging.info(f"    結合されたチャンク要約を最終要約のためにAIに送信中... テキスト長: {len(combined_summaries_text)}")
        final_prompt = f"""以下の要約のリストを統合し、面談シートの主要なポイントを以下の項目に沿って箇条書きで要約してください。具体的な固有名詞やエピソードは省略せず含めてください。

        # 面談シートの全内容の要約リスト
        ---
        {combined_summaries_text}
        ---

        # 要約結果
        ## 1. 主要な成果と強み (Positive Points)
        - [具体的な成果や強みを箇条書きで抽出]

        ## 2. 課題と改善点 (Areas for Improvement)
        - [具体的な課題や改善点を箇条書きで抽出]

        ## 3. 今後の目標と期待 (Future Goals & Expectations)
        - [具体的な目標や期待される役割を抽出]

        ## 4. その他の特記事項 (Other Notes)
        - [上記に含まれない重要な情報を抽出]
        """
        summary = call_ai_model(final_prompt)

    else:
        logging.info(f"    AIへの入力テキスト（先頭部分）: {interview_data_text[:500]}... (省略)")
        prompt = f"""以下の面談シートの内容全体を分析し、主要なポイントを以下の項目に沿って箇条書きで要約してください。具体的な固有名詞やエピソードは省略せず含めてください。

        # 面談シートの全内容
        ---
        {interview_data_text}
        ---

        # 要約結果
        ## 1. 主要な成果と強み (Positive Points)
        - [具体的な成果や強みを箇条書きで抽出]

        ## 2. 課題と改善点 (Areas for Improvement)
        - [具体的な課題や改善点を箇条書きで抽出]

        ## 3. 今後の目標と期待 (Future Goals & Expectations)
        - [具体的な目標や期待される役割を抽出]

        ## 4. その他の特記事項 (Other Notes)
        - [上記に含まれない重要な情報を抽出]
        """
        summary = call_ai_model(prompt)

    logging.info("    AIからの面談コメント要約応答を受信しました。")
    logging.info(f"    DEBUG: Summary from AI (type: {type(summary)}): {summary[:100] if summary else 'None'}...")
    if summary is None:
        logging.error("    DEBUG: Summary is None, returning '要約できませんでした'.")
        return "要約できませんでした"
    return summary

def get_advice_from_ai(summary):
    """AIを使用して、要約からアドバイスを生成する"""
    if not summary or summary == "要約できませんでした":
        return "アドバイスを生成できませんでした"
    prompt = f"""あなたは経験豊富なITコンサルタントです。
    以下の面談要約を基に、従業員がさらに成長するための、具体的でポジティブなアドバイスを2~3行で生成してください。
    会話的な前置きは一切不要で、アドバイス本文のみを出力してください。

    # 面談要約
    {summary}

    # アドバイス
    """
    advice = call_ai_model(prompt)
    if advice is None:
        return "アドバイスを生成できませんでした"
    return advice

def get_daily_report_summary_from_ai(daily_reports_text):
    """AIを使用して日報の内容を要約する"""
    if not daily_reports_text:
        return "要約できませんでした"
    prompt = f"""以下の期間の日報の内容を分析し、主要なポイントを以下の項目に沿って箇条書きで要約してください。具体的な固有名詞やエピソードは省略せず含めてください。

    # 日報の内容
    ---
    {daily_reports_text}
    ---

    # 要約結果
    ## 1. 主要な業務内容と成果 (Main Tasks & Achievements)
    - [具体的な業務内容や成果を箇条書きで抽出]

    ## 2. 課題と改善点 (Issues and Improvements)
    - [具体的な課題や改善点を箇条書きで抽出]

    ## 3. 気づきや学び (Insights and Learnings)
    - [業務を通じて得た気づきや学びを箇条書きで抽出]

    ## 4. その他の特記事項 (Other Notes)
    - [上記に含まれない重要な情報を抽出]
    """
    summary = call_ai_model(prompt)
    if summary is None:
        return "要約できませんでした"
    return summary

def get_daily_report_advice_from_ai(summary):
    """AIを使用して、日報要約からアドバイスを生成する"""
    if not summary or summary == "要約できませんでした":
        return "アドバイスを生成できませんでした"
    prompt = f"""あなたは経験豊富なITコンサルタントです。
    以下の日報要約を基に、従業員がさらに成長するための、具体的でポジティブなアドバイスを2~3行で生成してください。

    # 日報要約
    {summary}

    # アドバイス
    """
    advice = call_ai_model(prompt)
    if advice is None:
        return "アドバイスを生成できませんでした"
    return advice

def get_danger_signal_from_ai(daily_reports_text):
    """AIを使用して日報から危険信号を判定し、その根拠を生成する"""
    if not daily_reports_text:
        return {"signal": "false", "reason": "日報内容がありません。"}
    prompt = f"""あなたは優秀な人事コンサルタントです。以下の日報の内容を分析し、業務上の問題、体調不良のいずれか、または複数に該当する「危険信号」があるかどうかを判断してください。

    # 指示
    - 危険信号がある場合は "true"、ない場合は "false" を出力してください。
    - その判断をした根拠を簡潔に説明してください。
    - 出力はJSON形式でお願いします。

    # 日報の内容
    ---
    {daily_reports_text}
    ---

    # 出力形式 (JSON)
    ```json
    {{
        "signal": "true" or "false",
        "reason": "判断の根拠"
    }}
    ```
    """
    response_text = call_ai_model(prompt)
    if response_text is None:
        return {"signal": "false", "reason": "AIによる危険信号の判定に失敗しました。"}
    
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end != -1 and json_start < json_end:
            json_str = response_text[json_start:json_end].strip()
        else:
            logging.error(f"AIの応答からJSONオブジェクトを見つけられませんでした。応答: {response_text}")
            return {"signal": "false", "reason": "AI応答のパースに失敗しました。"}
        parsed_response = json.loads(json_str)
        parsed_response['signal'] = str(parsed_response.get('signal', 'false')).lower()
        return parsed_response
    except json.JSONDecodeError as e:
        logging.error(f"AIの応答がJSON形式ではありませんでした: {e}\n応答: {response_text}")
        return {"signal": "false", "reason": "AI応答のパースに失敗しました。"}

def analyze_dataframe_structure_with_ai(df_head_str):
    """AIを使用してDataFrameの構造（縦持ち/横持ち）と必要な列/項目名を特定する"""
    logging.info("    AIにデータ構造分析をリクエスト中...")
    logging.info(f"    AIへの入力データ（先頭部分）: {df_head_str[:200]}... (省略)")
    prompt = f"""あなたはデータ構造を分析するボットです。提供されたCSVデータの構造を分析し、結果を単一のJSONオブジェクトで返してください。説明や他のテキストは不要です。

    # 分析と出力のルール:
    1.  **構造**: データが「横持ち」（各行が1つのレコード）か「縦持ち」（項目と値のペア）かを判断し、`structure`キーに設定してください。
    2.  **列名/項目名**: CSVデータに存在する**完全一致**の列名または項目名を使用してください。
    3.  **従業員名/ID**: 従業員の**氏名**が含まれる列を`employee_col`（横持ち）または`employee_item`（縦持ち）として特定してください。また、従業員IDが含まれる列を`employee_id_col`（横持ち）または`employee_id_item`（縦持ち）として特定してください。もし氏名が見つからない場合は、`employee_item`に従業員IDが含まれる列を特定してください。
    4.  **面談日**: 面談日が含まれる列を`interview_date_col`（横持ち）または`interview_date_item`（縦持ち）として特定してください。
    5.  **コメント**: 面談内容の自由記述テキストが含まれる**すべての**項目を`comment_items`（縦持ち）または`comment_col`（横持ち）として特定してください。特に、以下の項目がデータに存在する場合、それらを**漏れなく全て**`comment_items`に含めてください。例: 「現在の担当業務」「最近学習した技術」「技術的な課題と解決策」「チームでの役割」「今後のキャリア目標」「上長コメント」「面談内容」「面談コメント」「業務での課題や悩み」「その他、共有事項」。
    6.  **スキル**: 従業員のスキルや得意分野に関する項目を`skills_item`（縦持ち）または`skills_col`（横持ち）として特定してください。
    7.  **見つからない場合**: 該当する項目がない場合は、空文字列 `""` を設定してください。

    # 出力JSONフォーマット:
    - **横持ちの場合**: `{{"structure": "横持ち", "employee_col": "", "employee_id_col": "", "interview_date_col": "", "comment_col": "", "skills_col": ""}}`
    - **縦持ちの場合**: `{{"structure": "縦持ち", "item_col": "", "value_col": "", "employee_item": "", "employee_id_item": "", "interview_date_item": "", "comment_items": [], "skills_item": ""}}`

    # 分析対象データ:
    ---
    {df_head_str}
    ---
    """
    logging.info(f"        DEBUG: AI prompt length: {len(prompt)} characters.")
    response_text = call_ai_model(prompt)
    logging.info("    AIからのデータ構造分析応答を受信しました。")
    if response_text is None:
        logging.error("AIによるデータ構造の分析に失敗しました。")
        return None
    logging.info(f"AIからの生応答: {response_text}")
    try:
        logging.info("    AI応答をJSONとしてパース中...")
        # AI応答がNoneの場合のハンドリングを追加
        if response_text is None:
            logging.error("AIからの応答がNoneでした。")
            return None

        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start != -1 and json_end != -1 and json_start < json_end:
            json_str = response_text[json_start:json_end].strip()
        else:
            logging.error(f"AIの応答からJSONオブジェクトを見つけられませんでした。応答: {response_text}")
            return None
        parsed_response = json.loads(json_str)
        logging.info("    AI応答のパースが完了しました。")
        return parsed_response
    except json.JSONDecodeError as e:
        logging.error(f"AIの応答がJSON形式ではありませんでした: {e}\n生応答: {response_text}") # 生応答をログに出力
        return None # パース失敗時はNoneを返すように変更
    except Exception as e: # その他の予期せぬエラーを捕捉
        logging.error(f"AI応答のパース中に予期せぬエラーが発生しました: {e}\n生応答: {response_text}")
        return None



# --- 4. データ処理 ---
def load_data(file_path, sheet_name=None):
    """CSVまたはExcelファイルを読み込む"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig') # BOM付きUTF-8を試す
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            logging.error("対応していないファイル形式です。CSVまたはExcelファイルを指定してください。")
            return None
        logging.info(f"ファイル '{file_path}' を正常に読み込みました。")
        return df
    except FileNotFoundError:
        logging.error(f"ファイルが見つかりません: {file_path}")
        return None
    except Exception as e:
        logging.error(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return None

def process_interviews_logic(input_path):
    """面談分析のメインロジック"""
    logging.info("モード: 面談分析を開始します。")
    output_directory = FileAndDir.INTERVIEW_RESULT_DIR
    # Ensure the output directory exists and get its absolute path
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    absolute_output_directory = os.path.abspath(output_directory)
    saved_file_paths = []
    if not input_path or not os.path.exists(input_path):
        msg = f"指定されたパスが見つかりません: {input_path}"
        logging.warning(msg)
        return msg, []
    
    final_name_col = ColumnName.EMPLOYEE_NAME
    processed_dfs = []

    files_to_process = []
    if os.path.isfile(input_path):
        files_to_process.append(input_path)
        logging.info(f"単一ファイル '{input_path}' を処理します。")
    elif os.path.isdir(input_path):
        logging.info(f"ディレクトリ '{input_path}' 内のファイルを処理します。")
        all_files_in_dir = [os.path.join(input_path, f) for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f)) and (f.lower().endswith('.csv') or f.lower().endswith('.xlsx'))]
        files_to_process.extend(all_files_in_dir)
        if not files_to_process:
            msg = "指定されたディレクトリから処理可能なファイルが見つかりませんでした。"
            logging.error(msg)
            return msg, []
        logging.info(f"合計 {len(files_to_process)} 個のファイルが見つかりました。")
    else:
        msg = f"指定されたパスが見つかりません: {input_path}"
        logging.warning(msg)
        return msg, []

    for i, file_path in enumerate(files_to_process):
        logging.info(f"[{i+1}/{len(files_to_process)}] ファイル '{file_path}' を処理中...")
        df_single = load_data(file_path)
        if df_single is None or df_single.empty:
            logging.warning(f"ファイル '{file_path}' の読み込みに失敗したか、ファイルが空です。スキップします。")
            continue
        
        logging.info(f"  ファイル '{file_path}' のデータ構造をAIで分析中...")
        logging.info("  DEBUG: converting df_single.head() to csv string...")
        df_head_str = df_single.head().to_csv(index=False)
        logging.info("  DEBUG: df_single.head() converted to csv string successfully.")
        logging.info("  DEBUG: Calling analyze_dataframe_structure_with_ai...")
        analysis_result = analyze_dataframe_structure_with_ai(df_head_str)
        logging.info("  DEBUG: analyze_dataframe_structure_with_ai returned.")
        if analysis_result is None:
            logging.error(f"  ファイル '{file_path}' のAIによるデータ構造の分析に失敗しました。スキップします。")
            continue
        
        # 従業員名、得意分野、面談日、そしてAIに渡すテキストを初期化
        employee_name = '不明な従業員'
        employee_id = '' # 新しく従業員IDを追加
        skills = ''
        interview_date_str = '' # 面談日を文字列として保持
        interview_data_text = ''

        # AIの判断結果に基づき、プログラムが全データをテキスト化
        if analysis_result.get('structure') == DataStructure.WIDE:
            name_col = analysis_result.get('employee_col')
            employee_id_col = analysis_result.get('employee_id_col') # 追加
            skills_col = analysis_result.get('skills_col')
            interview_date_col = analysis_result.get('interview_date_col')

            if not df_single.empty:
                # 従業員名、スキル、面談日を取得
                if name_col and name_col in df_single.columns:
                    employee_name = str(df_single.iloc[0][name_col])
                    logging.info(f"        DEBUG: Extracted employee_name (from file): {employee_name}")
                
                # 従業員IDを抽出
                if employee_id_col and employee_id_col in df_single.columns:
                    employee_id = str(df_single.iloc[0][employee_id_col])
                if skills_col and skills_col in df_single.columns:
                    skills = df_single.iloc[0][skills_col]
                if interview_date_col and interview_date_col in df_single.columns:
                    # 日付形式をYYYYMMDDに変換
                    try:
                        interview_date_str = pd.to_datetime(df_single.iloc[0][interview_date_col]).strftime('%Y%m%d')
                    except Exception as e:
                        logging.warning(f"面談日の変換に失敗しました: {e}。処理実行日時を使用します。")
                        interview_date_str = datetime.now().strftime('%Y%m%d-%H%M%S')
                else:
                    interview_date_str = datetime.now().strftime('%Y%m%d-%H%M%S')
                # 面談コメントのみをテキスト化
                comment_col = analysis_result.get('comment_col')
                if comment_col and comment_col in df_single.columns:
                    interview_data_text = "\n".join(df_single[comment_col].dropna().astype(str))
                    logging.info(f"  横持ちデータからコメント列 '{comment_col}' を抽出しました。")
                else:
                    logging.warning(f"  コメント列 '{comment_col}' が見つからなかったため、全データをテキスト化します。")
                    # フォールバックとして全データをテキスト化
                    for index, row in df_single.iterrows():
                        interview_data_text += f"--- Record {index + 1} ---\n"
                        for col, value in row.items():
                            interview_data_text += f"{col}: {value}\n"

        elif analysis_result.get('structure') == DataStructure.LONG:
            logging.info(f"  ファイル '{file_path}' は縦持ち構造と判断されました。")
            item_col = analysis_result.get('item_col')
            value_col = analysis_result.get('value_col')
            employee_item = analysis_result.get('employee_item')
            employee_id_item = analysis_result.get('employee_id_item') # 追加
            skills_item = analysis_result.get('skills_item')
            interview_date_item = analysis_result.get('interview_date_item')

            if item_col and value_col in df_single.columns:
                data_dict = pd.Series(df_single[value_col].values, index=df_single[item_col]).to_dict()
                # 従業員名、スキル、面談日を取得
                if employee_item in data_dict:
                    employee_name = str(data_dict[employee_item])
                
                # 従業員IDを抽出
                if employee_id_item in data_dict:
                    employee_id = str(data_dict[employee_id_item])
                if skills_item in data_dict:
                    skills = data_dict[skills_item]
                    logging.info(f"        DEBUG: Extracted skills: {skills}") # New log
                if interview_date_item in data_dict:
                    # 日付形式をYYYYMMDDに変換
                    try:
                        interview_date_str = pd.to_datetime(data_dict[interview_date_item]).strftime('%Y%m%d')
                    except Exception as e:
                        logging.warning(f"面談日の変換に失敗しました: {e}。処理実行日時を使用します。")
                        interview_date_str = datetime.now().strftime('%Y%m%d-%H%M%S')
                else:
                    interview_date_str = datetime.now().strftime('%Y%m%d-%H%M%S')
                # 面談コメントのみをテキスト化
                comment_items = analysis_result.get('comment_items', [])
                
                # AIがコメント項目を十分に特定できなかった場合、デフォルトのリストを使用
                if not comment_items or (len(comment_items) == 1 and comment_items[0] == "現在の担当業務"):
                    logging.warning("  AIがコメント項目を十分に特定できなかったため、デフォルトのコメント項目リストを使用します。")
                    comment_items = DEFAULT_COMMENT_ITEMS

                if comment_items:
                    # comment_itemsがリストであることを確認
                    if not isinstance(comment_items, list):
                        logging.warning(f"  comment_itemsがリストではないため、処理をスキップします: {comment_items}")
                        comment_items = [] # エラーを防ぐために空のリストに設定
                    
                    # 抽出したコメントを結合
                    comments_to_join = []
                    for item in comment_items:
                        if item in data_dict:
                            comments_to_join.append(f"{item}: {str(data_dict[item])}") # 項目名も追加
                    interview_data_text = "\n".join(comments_to_join)
                    logging.info(f"  縦持ちデータからコメント項目 {comment_items} を抽出しました。")
                else:
                    logging.warning("  コメント項目が見つからなかったため、全データをテキスト化します。")
                    # フォールバックとして全データをテキスト化
                    for item, value in data_dict.items():
                        interview_data_text += f"{item}: {value}\n"
            else:
                logging.error(f"  縦持ち構造の必須列が見つかりません: '{item_col}', '{value_col}'。スキップします。")
                continue
        else:
            logging.error(f"AIが不明なデータ構造を返しました: {analysis_result.get('structure')}。ファイル '{file_path}' をスキップします。")
            continue

        if not interview_data_text.strip():
            logging.warning(f"ファイル '{file_path}' からテキストデータを抽出できませんでした。スキップします。")
            continue

        logging.info(f"  ファイル '{file_path}' の面談データをAIで要約中...")
        summary = get_summary_from_ai(interview_data_text)
        logging.info(f"  DEBUG: Summary received from get_summary_from_ai (type: {type(summary)}): {summary[:100] if summary else 'None'}...")
        
        logging.info(f"  ファイル '{file_path}' のAIによるアドバイスを生成中...")
        advice = get_advice_from_ai(summary)

        # ファイル名を生成 (従業員名が不明な従業員でなければ従業員名を優先、そうでなければ従業員ID)
        if employee_name != '不明な従業員':
            output_filename_base = f"{employee_name}_{interview_date_str}"
        elif employee_id: # employee_nameが不明な従業員で、employee_idがある場合
            output_filename_base = f"{employee_id}_{interview_date_str}"
        else: # どちらも不明な場合
            output_filename_base = f"不明な従業員_{interview_date_str}"

        safe_output_filename_base = "".join(c for c in output_filename_base if c.isalnum() or c in ('_', '-')).rstrip()
        
        result_df_single = pd.DataFrame([{
            final_name_col: employee_name,
            ColumnName.EMPLOYEE_ID: employee_id, # 追加
            ColumnName.SKILLS: skills,
            ColumnName.INTERVIEW_SUMMARY: summary,
            ColumnName.AI_ADVICE: advice
        }])
        
        # save_individual_reportsにファイル名を渡す
        saved_path = save_individual_reports(result_df_single, final_name_col, output_directory, safe_output_filename_base)
        if saved_path:
            saved_file_paths.append(saved_path)
            # DBにも保存
            db_data = {
                'employee_name': employee_name,
                'employee_id': employee_id, # 追加
                'interview_date': interview_date_str,
                'summary_positive': summary, # ここは要約全体を渡す
                'summary_negative': '', # 面談分析ではネガティブは別途抽出しないので空
                'summary_action_items': '', # 面談分析ではアクションアイテムは別途抽出しないので空
                'ai_advice': advice
            }
            database_handler.save_interview_to_db(db_data)
        processed_dfs.append(result_df_single)
        
        logging.info(f"  ファイル '{file_path}' の処理が完了しました。")
    
    msg = "面談分析の処理が完了しました。"
    logging.info(msg)
    return msg, saved_file_paths

def save_individual_reports(df, name_col, output_dir='.', custom_filename_base=None):
    """従業員ごとに個別のCSVファイルとして保存する"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"出力ディレクトリ '{output_dir}' を作成しました。")
    
    # 保存する列を定義
    output_columns = [name_col, ColumnName.EMPLOYEE_ID, ColumnName.SKILLS, ColumnName.INTERVIEW_SUMMARY, ColumnName.AI_ADVICE]
    
    for index, row in df.iterrows():
        if custom_filename_base:
            output_filename = os.path.join(output_dir, f"{custom_filename_base}.csv")
        else:
            employee_name = row[name_col]
            # ファイル名に使えない文字を置換
            safe_employee_name = "".join(c for c in employee_name if c.isalnum() or c in ('_', '-')).rstrip()
            output_filename = os.path.join(output_dir, f"{safe_employee_name}_要約データ.csv")
        
        # 保存するデータを選択
        employee_df = pd.DataFrame([row])
        # 存在する列のみを選択してエラーを防ぐ
        save_columns = [col for col in output_columns if col in employee_df.columns]
        employee_df_to_save = employee_df[save_columns]

        try:
            employee_df_to_save.to_csv(output_filename, index=False, encoding='utf-8-sig')
            logging.info(f"'{output_filename}' を保存しました。")
            return output_filename # 保存したファイルのパスを返す
        except Exception as e:
            logging.error(f"'{output_filename}' の保存中にエラーが発生しました: {e}")
            return None # エラーの場合はNoneを返す

def process_daily_reports_logic(file_path):
    """日報データを処理し、週ごと/月ごとに要約、アドバイス、危険信号を生成する"""
    logging.info(f"日報データファイル '{file_path}' の処理を開始します。")
    saved_file_paths = [] # これを追加
    try:
        xls = pd.ExcelFile(file_path)
        all_sheet_names = xls.sheet_names
    except Exception as e:
        logging.error(f"Excelファイルの読み込み中にエラーが発生しました: {e}")
        return f"Excelファイルの読み込み中にエラーが発生しました: {e}", []
    output_dir = FileAndDir.DAILY_REPORT_RESULT_DIR
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"出力ディレクトリ '{output_dir}' を作成しました。")
    for sheet_name in all_sheet_names:
        if sheet_name == "表紙" or sheet_name == "Summary":
            logging.info(f"シート '{sheet_name}' は表紙のためスキップします。")
            continue
        employee_name = sheet_name
        logging.info(f"従業員 '{employee_name}' の日報データを処理中...")
        df_daily = load_data(file_path, sheet_name=sheet_name)
        if df_daily is None or df_daily.empty: continue
        date_col = ColumnName.TIMESTAMP
        if date_col not in df_daily.columns:
            logging.error(f"シート '{sheet_name}' に日付列（'{date_col}'）が見つかりませんでした。スキップします。")
            continue
        try:
            df_daily[date_col] = pd.to_datetime(df_daily[date_col], format='%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.error(f"シート '{sheet_name}' の日付列の変換に失敗しました: {e}。スキップします。")
            continue
        daily_report_content_cols = [
            ColumnName.HEALTH_CONDITION, ColumnName.MOOD, ColumnName.DAILY_業務内容,
            ColumnName.ISSUES_AND_CONCERNS, ColumnName.OTHER_SHARED_ITEMS
        ]
        existing_content_cols = [col for col in daily_report_content_cols if col in df_daily.columns]
        if not existing_content_cols:
            logging.error(f"シート '{sheet_name}' に日報内容の列が見つかりませんでした。スキップします。")
            continue
        df_daily[ColumnName.COMBINED_CONTENT] = df_daily[existing_content_cols].astype(str).agg(' '.join, axis=1)
        content_col = ColumnName.COMBINED_CONTENT
        df_daily = df_daily.sort_values(by=date_col)
        if DAILY_REPORT_PERIOD == ConfigKeys.WEEKLY:
            df_daily[ColumnName.PERIOD_START] = df_daily[date_col].apply(lambda x: x - timedelta(days=x.weekday()))
            grouped = df_daily.groupby(ColumnName.PERIOD_START)
        elif DAILY_REPORT_PERIOD == ConfigKeys.MONTHLY:
            df_daily[ColumnName.PERIOD_START] = df_daily[date_col].dt.to_period('M').dt.start_time
            grouped = df_daily.groupby(ColumnName.PERIOD_START)
        else:
            logging.error(f"無効な日報集計期間設定: {DAILY_REPORT_PERIOD}。スキップします。")
            continue
        for period_start, group in grouped:
            period_end = group[date_col].max()
            if DAILY_REPORT_PERIOD == 'weekly':
                period_str = f"{period_start.strftime('%Y%m%d')}-{period_end.strftime('%Y%m%d')}"
            elif DAILY_REPORT_PERIOD == 'monthly':
                period_str = f"{period_start.strftime('%Y%m')}"
            logging.info(f"  期間: {period_str} の日報を処理中...")
            combined_daily_reports_text = "\n".join(group[content_col].dropna().astype(str).tolist())
            summary = get_daily_report_summary_from_ai(combined_daily_reports_text)
            advice = get_daily_report_advice_from_ai(summary)
            danger_signal_result = get_danger_signal_from_ai(combined_daily_reports_text)
            result_df = pd.DataFrame([{
                ColumnName.EMPLOYEE_NAME: employee_name, 
                ColumnName.PERIOD: period_str, 
                ColumnName.DAILY_REPORT_SUMMARY: summary, 
                ColumnName.AI_ADVICE: advice, 
                ColumnName.DANGER_SIGNAL: danger_signal_result['signal'], 
                ColumnName.DANGER_SIGNAL_REASON: danger_signal_result['reason']
            }])
            output_filename = os.path.join(output_dir, f"{employee_name}_{period_str}_日報分析.csv")
            try:
                result_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
                logging.info(f"  '{output_filename}' を保存しました。")
                saved_file_paths.append(output_filename) # これを追加！
                # DBにも保存
                db_data = {
                    'employee_name': employee_name,
                    'period_start_date': period_str,
                    'summary_achievements': summary, # ここは要約全体を渡す
                    'summary_issues': '', # 日報分析では課題は別途抽出しないので空
                    'summary_next_steps': '', # 日報分析では次のステップは別途抽出しないので空
                    'danger_signal': danger_signal_result['signal'],
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S') # created_atを追加
                }
                database_handler.save_daily_report_to_db(db_data)
            except Exception as e:
                logging.error(f"  '{output_filename}' の保存中にエラーが発生しました: {e}")
    msg = "日報データの処理が完了しました。"
    logging.info(msg)
    return msg, saved_file_paths # saved_file_paths を返すように変更



def load_all_analysis_data_for_qa():
    """AI質問応答のために、面談要約と日報分析の両方のデータをDBから読み込み、データフレームと各種件数を返す"""
    return database_handler.load_all_analysis_data_for_qa()
def get_deletable_data_for_ui():
    """UIの削除ドロップダウンに表示するデータをDBから取得する"""
    return database_handler.get_deletable_data_list()

def handle_delete_request(selection_string):
    """UIからの削除リクエストを処理し、DBからレコードを削除する"""
    import re
    logging.info(f"削除リクエストを受信しました: {selection_string}")

    employee_name = ""
    employee_id = ""
    date_str = ""
    is_bulk_delete = False

    if selection_string.startswith("[まとめ]"):
        is_bulk_delete = True
        # [まとめ] 従業員名 ID:従業員ID (全データ削除) または [まとめ] 従業員名 (全データ削除)
        match = re.match(r"\[まとめ\]\s*(.*?)(?:\s*ID:(\w+))?\s*\(全データ削除\)", selection_string)
        if match:
            employee_name = match.group(1).strip()
            employee_id = match.group(2) if match.group(2) else ""
    else:
        # 従業員名 ID:従業員ID (日付) (面談) または 従業員名 (日付) (日報)
        match = re.match(r"(.*?)(?:\s*ID:(\w+))?\s*\((.*?)\)\s*\((面談|日報)\)", selection_string)
        if match:
            employee_name = match.group(1).strip()
            employee_id = match.group(2) if match.group(2) else ""
            date_str = match.group(3).strip()
            data_type = match.group(4).strip()
            # date_str にデータタイプを含めてdatabase_handlerに渡す
            date_str = f"({date_str}) ({data_type})"
        else:
            logging.error(f"削除文字列のパースに失敗しました: {selection_string}")
            return "削除に失敗しました: 無効な選択です。"

    if not employee_name and not employee_id:
        return "削除に失敗しました: 従業員名または従業員IDが特定できませんでした。"

    success = database_handler.delete_record_from_db(employee_name, employee_id, date_str, is_bulk_delete)

    if success:
        return f"データを正常に削除しました: {selection_string}"
    else:
        return f"データの削除に失敗しました: {selection_string}"
def generate_qa_context(df):
    """AI質問応答のためのコンテキストを生成する"""
    context = """以下の従業員の面談要約とアドバイスを参考に、質問に答えてください。

"""
    name_col = ColumnName.EMPLOYEE_NAME
    if name_col not in df.columns:
        logging.error(f"コンテキスト生成に必要な'{name_col}'列が見つかりません。")
        return ""

    # 列の存在を確認
    summary_col_interview = ColumnName.INTERVIEW_SUMMARY
    summary_col_daily = ColumnName.DAILY_REPORT_SUMMARY
    advice_col = ColumnName.AI_ADVICE
    
    for index, row in df.iterrows():
        employee_name = row.get(name_col, '不明')
        if pd.isna(employee_name):
            employee_name = '不明な従業員'
        
        data_type = row.get('データ種別', '不明')
        logging.info(f'  コンテキスト生成中: 従業員名="{employee_name}", データ種別="{data_type}"') # New log
        
        if data_type == '面談要約':
            summary = row.get(summary_col_interview, None)
            if pd.isna(summary):
                summary = 'N/A'
            else:
                summary = str(summary)
        else:
            summary = row.get(summary_col_daily, None)
            if pd.isna(summary):
                summary = 'N/A'
            else:
                summary = str(summary)
            
        advice = row.get(advice_col, None)
        if pd.isna(advice):
            advice = 'N/A'
        else:
            advice = str(advice)

        danger_signal = row.get(ColumnName.DANGER_SIGNAL, None)
        if pd.isna(danger_signal):
            danger_signal = 'N/A'
        else:
            danger_signal = str(danger_signal)

        danger_reason = row.get(ColumnName.DANGER_SIGNAL_REASON, None)
        if pd.isna(danger_reason):
            danger_reason = 'N/A'
        else:
            danger_reason = str(danger_reason)
        context += f"--- 従業員: {employee_name} ({data_type}) ---\n"
        context += f"要約: {summary}\n"
        context += f"AIによるアドバイス: {advice}\n"
        if data_type == '日報分析':
            context += f"危険信号: {danger_signal}, 根拠: {danger_reason}\n"
        context += "\n"
    return context

def ask_question_to_ai(question, chat_session, initial_context=None):
    """AIに質問して回答を得る（チャットセッション対応）"""
    if not question:
        logging.warning("AIへの質問が空です。")
        return "質問が入力されていません。"
    logging.info(f"AIへの質問: {question}")
    try:
        if AI_BACKEND == ConfigKeys.GEMINI:
            # initial_contextはprepare_qa_dataで既に設定されているため、ここでは不要
            response = chat_session.send_message(question)
            ai_response = response.text.strip()
            logging.info(f"AIからの応答: {ai_response}")
            return f"AIの回答: {ai_response}"
        elif AI_BACKEND == ConfigKeys.OLLAMA:
            # Ollamaの場合は、chat_sessionがメッセージ履歴を保持していると仮定
            # ここでは、既存のメッセージ履歴に新しい質問を追加して送信する
            messages = chat_session # chat_sessionがメッセージリストとして渡されると仮定
            messages.append({"role": "user", "content": question})
            headers = {'Content-Type': 'application/json'}
            data = {"model": OLLAMA_MODEL, "messages": messages, "stream": False}
            response = requests.post(f"{OLLAMA_URL}/api/chat", headers=headers, json=data)
            response.raise_for_status()
            ai_response = response.json()['message']['content'].strip()
            messages.append({"role": "assistant", "content": ai_response}) # AIの応答を履歴に追加
            logging.info(f"AIからの応答: {ai_response}")
            return f"AIの回答: {ai_response}"
    except Exception as e:
        logging.error(f"AIの回答生成中にエラーが発生しました: {e}")
        return "AIの回答: 回答を生成できませんでした。"

def prepare_qa_data():
    """AI対話の準備として、データを読み込み、件数とコンテキスト、チャットセッションを生成する"""
    logging.info("AI対話の準備を開始します。")
    if not load_config():
        msg = "設定の読み込みに失敗しました。処理を中断します。"
        logging.error(msg)
        return None, 0, 0, msg, None # chat_sessionもNoneで返す

    combined_qa_df, interview_count, daily_report_count = load_all_analysis_data_for_qa()
    
    if combined_qa_df is None or combined_qa_df.empty:
        msg = "質問応答を開始するためのデータが見つかりませんでした。"
        logging.warning(msg)
        return None, 0, 0, msg, None

    initial_context = generate_qa_context(combined_qa_df)

    chat_session = None
    if AI_BACKEND == ConfigKeys.GEMINI:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # initial_contextをシステムプロンプトとしてhistoryの最初の要素に設定
        chat_session = model.start_chat(history=[
            {'role':'user', 'parts':[initial_context]},
            {'role':'model', 'parts':['はい、何でもお聞きください。']} # AIの最初の応答例
        ])
    elif AI_BACKEND == ConfigKeys.OLLAMA:
        # Ollamaの場合は、メッセージ履歴をリストとして初期化
        chat_session = [{"role": "system", "content": initial_context}] # システムプロンプトとして初期コンテキストを設定

    return initial_context, interview_count, daily_report_count, "データの読み込みが完了しました。", chat_session

# --- 5. GUIから呼び出されるメイン実行ブロック ---
def run_backend_process(mode, input_path=None, question=None, context=None, chat_session=None):
    """GUIから呼び出されるメイン処理"""
    logging.info(f"バックエンド処理を開始します。モード: {mode}")
    # データベースの初期化
    database_handler.initialize_database()
    if not load_config():
        msg = "設定の読み込みに失敗しました。処理を中断します。"
        logging.error(msg)
        return msg, [], None

    # --- API接続テスト ---
    # AIモデルを使用するモードでのみAPI接続テストを実行
    if mode in [AnalysisMode.INTERVIEW, AnalysisMode.QA, AnalysisMode.DAILY_REPORT]:
        logging.info("--- API接続の独立テストを開始します ---")
        try:
            if AI_BACKEND == ConfigKeys.GEMINI:
                logging.info(f"    [Test] Geminiモデルを初期化しています... ({GEMINI_MODEL})")
                test_model = genai.GenerativeModel(GEMINI_MODEL) # テストには本番と同じモデルを使用
                logging.info("    [Test] Geminiモデルの初期化が完了しました。")
                logging.info("    [Test] 単純なプロンプトでコンテンツを生成しています...")
                test_response = test_model.generate_content("これは接続テストです。", request_options={'timeout': 30})
                logging.info(f"    [Test] APIからの応答を受信しました: {test_response.text.strip()}")
                logging.info("--- API接続の独立テストは成功しました ---")
            else:
                logging.info("    [Test] Ollamaバックエンドのため、このテストはスキップします。")
        except Exception as e:
            logging.error(f"--- API接続の独立テスト中にエラーが発生しました: {e} ---")
            logging.error("    APIキーが正しいか、ネットワーク接続（ファイアウォールなど）に問題がないか確認してください。")
            # テストが失敗した場合は、ここで処理を中断してエラーメッセージを返す
            return f"API接続テストに失敗しました。設定を確認してください。エラー: {e}", [], None
        # --- テスト終了 ---

    if mode == AnalysisMode.INTERVIEW:
        message, saved_paths = process_interviews_logic(input_path)
        return message, saved_paths, None
    elif mode == AnalysisMode.QA:
        logging.info("モード: AI対話 - 回答生成")
        # chat_sessionをask_question_to_aiに渡す
        message = ask_question_to_ai(question, chat_session, initial_context=context)
        return message, [], None
    elif mode == AnalysisMode.DAILY_REPORT:
        message, saved_paths = process_daily_reports_logic(input_path)
        return message, saved_paths, None
    elif mode == AnalysisMode.GET_DELETE_LIST:
        deletable_items = get_deletable_data_for_ui()
        return deletable_items, [], None
    elif mode == AnalysisMode.EXECUTE_DELETE:
        message = handle_delete_request(input_path)
        return message, [], None
    else:
        msg = f"無効なモードが指定されました: {mode}"
        logging.warning(msg)
        return msg, [], None