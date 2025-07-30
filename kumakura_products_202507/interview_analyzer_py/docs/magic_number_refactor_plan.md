# マジックナンバー/文字列の定数化 修正方針

`code_review_notes.md`の指摘に基づき、`backend_logic.py` と `app_gui.py` にハードコードされている文字列（マジックナンバー）を定数化し、保守性を向上させます。

## 修正方針

1.  **定数管理ファイルの作成**:
    *   `src` フォルダに `constants.py` を新規作成し、プロジェクト全体で使用する定数を一元管理します。

2.  **定数の定義**:
    *   `constants.py` に、モード名、カラム名、UIのデフォルトテキスト、設定キーなどを定数として定義します。可読性と管理のしやすさから、関連する定数はクラスとしてグループ化します。

3.  **既存コードの修正**:
    *   `backend_logic.py` と `app_gui.py` のハードコードされた文字列を、`constants.py` からインポートした定数に置き換えます。

## 修正箇所

### 1. `src/constants.py` (新規作成)

```python
# src/constants.py

class AnalysisMode:
    """分析モードを定義する定数クラス"""
    INTERVIEW = "interview"
    DAILY_REPORT = "daily_report"
    QA = "qa"
    GET_DELETE_LIST = "get_delete_list"
    EXECUTE_DELETE = "execute_delete"

class ColumnName:
    """データフレームやDBで使用するカラム名を定義する定数クラス"""
    # 共通
    EMPLOYEE_NAME = "従業員名"
    EMPLOYEE_ID = "従業員ID"
    AI_ADVICE = "AIによるアドバイス"

    # 面談分析
    SKILLS = "得意分野"
    INTERVIEW_SUMMARY = "面談結果要約"

    # 日報分析
    PERIOD = "期間"
    DAILY_REPORT_SUMMARY = "日報内容要約"
    DANGER_SIGNAL = "危険信号"
    DANGER_SIGNAL_REASON = "危険信号の根拠"
    TIMESTAMP = "タイムスタンプ"
    HEALTH_CONDITION = "今日の体調"
    MOOD = "今日の気分"
    DAILY_業務内容 = "今日の業務内容"
    ISSUES_AND_CONCERNS = "業務での課題や悩み"
    OTHER_SHARED_ITEMS = "その他、共有事項"
    COMBINED_CONTENT = "combined_content"
    PERIOD_START = "period_start"

class UIDefaults:
    """GUIで使用するデフォルトのテキストや値を定義する定数クラス"""
    # モード選択
    INTERVIEW_MODE_TEXT = "面談分析"
    DAILY_REPORT_MODE_TEXT = "日報分析"
    QA_MODE_TEXT = "AI対話"

    # 削除機能
    DELETE_PROMPT = "削除対象を選択してください..."
    NO_ITEMS_TO_DELETE = "削除対象なし"

class ConfigKeys:
    """config.iniのキーを定義する定数クラス"""
    # AI Backend
    AI_BACKEND_SECTION = "ai_backend"
    AI_BACKEND = "ai_backend"
    GEMINI = "gemini"
    OLLAMA = "ollama"

    # Gemini
    GEMINI_SECTION = "gemini"
    API_KEY = "api_key"
    MODEL_VERSION = "model_version"

    # Ollama
    OLLAMA_SECTION = "ollama"
    OLLAMA_URL = "ollama_url"
    OLLAMA_MODEL = "ollama_model"

    # Daily Report
    DAILY_REPORT_SECTION = "daily_report"
    PERIOD = "period"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class FileAndDir:
    """ファイル名やディレクトリ名を定義する定数クラス"""
    INTERVIEW_RESULT_DIR = "面談要約結果"
    DAILY_REPORT_RESULT_DIR = "日報分析結果"
    CONFIG_FILE = "config.ini"

class DataStructure:
    """データ構造の種別を定義する定数クラス"""
    WIDE = "横持ち"
    LONG = "縦持ち"

# デフォルトのコメント項目リスト
DEFAULT_COMMENT_ITEMS = [
    "現在の担当業務",
    "最近学習した技術",
    "技術的な課題と解決策",
    "チームでの役割",
    "今後のキャリア目標",
    "上長コメント",
    "面談内容",
    "面談コメント",
    "業務での課題や悩み",
    "その他、共有事項"
]
```

### 2. `src/app_gui.py` の修正案

**修正前 (抜粋):**
```python
# (略)
        self.mode_variable = customtkinter.StringVar(value="interview")
        self.interview_radio = customtkinter.CTkRadioButton(self.mode_frame, text="面談分析", variable=self.mode_variable, value="interview", command=self.on_mode_change)
        self.daily_report_radio = customtkinter.CTkRadioButton(self.mode_frame, text="日報分析", variable=self.mode_variable, value="daily_report", command=self.on_mode_change)
        self.qa_radio = customtkinter.CTkRadioButton(self.mode_frame, text="AI対話", variable=self.mode_variable, value="qa", command=self.on_mode_change)
# (略)
        self.delete_combobox = customtkinter.CTkComboBox(self.delete_frame, values=["削除対象を選択してください..."], command=self.on_delete_combobox_change)
        self.delete_combobox.set("削除対象を選択してください...") # 初期表示
# (略)
```

**修正後 (抜粋):**
```python
# (略)
import backend_logic # backend_logic.pyをインポート
from tkinterdnd2 import DND_FILES, TkinterDnD as tkdnd # tkinterdnd2をインポート
from constants import AnalysisMode, UIDefaults # 定数をインポート

# (略)
        self.mode_variable = customtkinter.StringVar(value=AnalysisMode.INTERVIEW)
        self.interview_radio = customtkinter.CTkRadioButton(self.mode_frame, text=UIDefaults.INTERVIEW_MODE_TEXT, variable=self.mode_variable, value=AnalysisMode.INTERVIEW, command=self.on_mode_change)
        self.daily_report_radio = customtkinter.CTkRadioButton(self.mode_frame, text=UIDefaults.DAILY_REPORT_MODE_TEXT, variable=self.mode_variable, value=AnalysisMode.DAILY_REPORT, command=self.on_mode_change)
        self.qa_radio = customtkinter.CTkRadioButton(self.mode_frame, text=UIDefaults.QA_MODE_TEXT, variable=self.mode_variable, value=AnalysisMode.QA, command=self.on_mode_change)
# (略)
        self.delete_combobox = customtkinter.CTkComboBox(self.delete_frame, values=[UIDefaults.DELETE_PROMPT], command=self.on_delete_combobox_change)
        self.delete_combobox.set(UIDefaults.DELETE_PROMPT) # 初期表示
# (略)
    def on_mode_change(self):
        selected_mode = self.mode_variable.get()
        if selected_mode == AnalysisMode.QA:
# (略)
    def select_file(self):
        selected_mode = self.mode_variable.get()
        if selected_mode == AnalysisMode.INTERVIEW:
# (略)
    def _update_delete_combobox_backend(self):
        self.log("DEBUG: _update_delete_combobox_backend called.")
        deletable_items, _, _ = backend_logic.run_backend_process(mode=AnalysisMode.GET_DELETE_LIST)
# (略)
            self.after(0, lambda: self.delete_combobox.configure(values=deletable_items))
            self.after(0, lambda: self.delete_combobox.set(UIDefaults.DELETE_PROMPT))
# (略)
        else:
            self.log("削除対象データが見つかりませんでした。")
            self.after(0, lambda: self.delete_combobox.configure(values=[UIDefaults.NO_ITEMS_TO_DELETE]))
            self.after(0, lambda: self.delete_combobox.set(UIDefaults.NO_ITEMS_TO_DELETE))
# (略)
    def run_backend(self, mode, path, question, context):
# (略)
            if saved_paths:
                if mode == AnalysisMode.INTERVIEW:
# (略)
                elif mode == AnalysisMode.DAILY_REPORT:
# (略)
    def execute_delete(self):
        selected_item = self.delete_combobox.get()
        if selected_item == UIDefaults.DELETE_PROMPT or selected_item == UIDefaults.NO_ITEMS_TO_DELETE:
# (略)
            thread = threading.Thread(target=self._execute_delete_backend, args=(selected_item,))
            thread.start()
# (略)
    def _execute_delete_backend(self, selected_item):
        try:
            message, _, _ = backend_logic.run_backend_process(mode=AnalysisMode.EXECUTE_DELETE, input_path=selected_item)
# (略)
    def on_delete_combobox_change(self, choice):
        if choice not in [UIDefaults.DELETE_PROMPT, UIDefaults.NO_ITEMS_TO_DELETE]:
# (略)
```

### 3. `src/backend_logic.py` の修正案

**修正前 (抜粋):**
```python
# (略)
# デフォルトのコメント項目リスト
DEFAULT_COMMENT_ITEMS = [
    "現在の担当業務",
    "最近学習した技術",
# (略)
]
# (略)
def load_config():
# (略)
        AI_BACKEND = config['ai_backend']['ai_backend'].lower()
        if AI_BACKEND not in ['gemini', 'ollama']:
# (略)
        if AI_BACKEND == 'gemini':
# (略)
        elif AI_BACKEND == 'ollama':
# (略)
        DAILY_REPORT_PERIOD = config['daily_report']['period'].lower()
        if DAILY_REPORT_PERIOD not in ['weekly', 'monthly']:
# (略)
def call_ai_model(prompt, model_type="generative"):
# (略)
            if AI_BACKEND == 'gemini':
# (略)
            elif AI_BACKEND == 'ollama':
# (略)
def process_interviews_logic(input_path):
    """面談分析のメインロジック"""
    logging.info("モード: 面談分析を開始します。")
    output_directory = "面談要約結果"
# (略)
    final_name_col = '従業員名'
# (略)
            if analysis_result.get('structure') == '横持ち':
# (略)
            elif analysis_result.get('structure') == '縦持ち':
# (略)
def process_daily_reports_logic(file_path):
# (略)
    output_dir = "日報分析結果"
# (略)
        if sheet_name == "表紙" or sheet_name == "Summary":
# (略)
        date_col = 'タイムスタンプ'
# (略)
        daily_report_content_cols = ['今日の体調', '今日の気分', '今日の業務内容', '業務での課題や悩み', 'その他、共有事項']
# (略)
        df_daily['combined_content'] = df_daily[existing_content_cols].astype(str).agg(' '.join, axis=1)
        content_col = 'combined_content'
# (略)
        if DAILY_REPORT_PERIOD == 'weekly':
            df_daily['period_start'] = df_daily[date_col].apply(lambda x: x - timedelta(days=x.weekday()))
            grouped = df_daily.groupby('period_start')
        elif DAILY_REPORT_PERIOD == 'monthly':
            df_daily['period_start'] = df_daily[date_col].dt.to_period('M').dt.start_time
            grouped = df_daily.groupby('period_start')
# (略)
def generate_qa_context(df):
# (略)
    name_col = '従業員名'
# (略)
    summary_col_interview = '面談結果要約'
    summary_col_daily = '日報内容要約'
    advice_col = 'AIによるアドバイス'
# (略)
        data_type = row.get('データ種別', '不明')
        if data_type == '面談要約':
# (略)
        danger_signal = str(row.get('危険信号', 'N/A')).replace("nan", "")
        danger_reason = str(row.get('危険信号の根拠', 'N/A')).replace("nan", "")
# (略)
        if data_type == '日報分析':
# (略)
def ask_question_to_ai(question, chat_session, initial_context=None):
# (略)
        if AI_BACKEND == 'gemini':
# (略)
        elif AI_BACKEND == 'ollama':
# (略)
def prepare_qa_data():
# (略)
    if AI_BACKEND == 'gemini':
# (略)
    elif AI_BACKEND == 'ollama':
# (略)
def run_backend_process(mode, input_path=None, question=None, context=None, chat_session=None):
# (略)
    if mode in ["interview", "qa", "daily_report"]:
# (略)
        if AI_BACKEND == 'gemini':
# (略)
    if mode == "interview":
# (略)
    elif mode == "qa":
# (略)
    elif mode == "daily_report":
# (略)
    elif mode == "get_delete_list":
# (略)
    elif mode == "execute_delete":
# (略)
```

**修正後 (抜粋):**
```python
# (略)
import json # AI応答パース用
import time # リトライ処理用
import database_handler # 追加
from constants import ( # 定数をインポート
    AnalysisMode, ColumnName, UIDefaults, ConfigKeys, FileAndDir, DataStructure,
    DEFAULT_COMMENT_ITEMS
)

# (略)
# デフォルトのコメント項目リストはconstants.pyに移動

# (略)
def load_config():
# (略)
        AI_BACKEND = config[ConfigKeys.AI_BACKEND_SECTION][ConfigKeys.AI_BACKEND].lower()
        if AI_BACKEND not in [ConfigKeys.GEMINI, ConfigKeys.OLLAMA]:
# (略)
        if AI_BACKEND == ConfigKeys.GEMINI:
            api_key = config[ConfigKeys.GEMINI_SECTION][ConfigKeys.API_KEY]
# (略)
            GEMINI_MODEL = config[ConfigKeys.GEMINI_SECTION].get(ConfigKeys.MODEL_VERSION, 'gemini-2.0-flash')
# (略)
        elif AI_BACKEND == ConfigKeys.OLLAMA:
            OLLAMA_URL = config[ConfigKeys.OLLAMA_SECTION][ConfigKeys.OLLAMA_URL]
            OLLAMA_MODEL = config[ConfigKeys.OLLAMA_SECTION][ConfigKeys.OLLAMA_MODEL]
# (略)
        DAILY_REPORT_PERIOD = config[ConfigKeys.DAILY_REPORT_SECTION][ConfigKeys.PERIOD].lower()
        if DAILY_REPORT_PERIOD not in [ConfigKeys.WEEKLY, ConfigKeys.MONTHLY]:
# (略)
def call_ai_model(prompt, model_type="generative"):
# (略)
            if AI_BACKEND == ConfigKeys.GEMINI:
# (略)
            elif AI_BACKEND == ConfigKeys.OLLAMA:
# (略)
def process_interviews_logic(input_path):
    """面談分析のメインロジック"""
    logging.info(f"モード: {AnalysisMode.INTERVIEW} を開始します。")
    output_directory = FileAndDir.INTERVIEW_RESULT_DIR
# (略)
    final_name_col = ColumnName.EMPLOYEE_NAME
# (略)
            if analysis_result.get('structure') == DataStructure.WIDE:
# (略)
            elif analysis_result.get('structure') == DataStructure.LONG:
# (略)
def process_daily_reports_logic(file_path):
# (略)
    output_dir = FileAndDir.DAILY_REPORT_RESULT_DIR
# (略)
        if sheet_name == "表紙" or sheet_name == "Summary": # これは定数化しにくいのでそのまま
# (略)
        date_col = ColumnName.TIMESTAMP
# (略)
        daily_report_content_cols = [
            ColumnName.HEALTH_CONDITION, ColumnName.MOOD, ColumnName.DAILY_業務内容,
            ColumnName.ISSUES_AND_CONCERNS, ColumnName.OTHER_SHARED_ITEMS
        ]
# (略)
        df_daily[ColumnName.COMBINED_CONTENT] = df_daily[existing_content_cols].astype(str).agg(' '.join, axis=1)
        content_col = ColumnName.COMBINED_CONTENT
# (略)
        if DAILY_REPORT_PERIOD == ConfigKeys.WEEKLY:
            df_daily[ColumnName.PERIOD_START] = df_daily[date_col].apply(lambda x: x - timedelta(days=x.weekday()))
            grouped = df_daily.groupby(ColumnName.PERIOD_START)
        elif DAILY_REPORT_PERIOD == ConfigKeys.MONTHLY:
            df_daily[ColumnName.PERIOD_START] = df_daily[date_col].dt.to_period('M').dt.start_time
            grouped = df_daily.groupby(ColumnName.PERIOD_START)
# (略)
def generate_qa_context(df):
# (略)
    name_col = ColumnName.EMPLOYEE_NAME
# (略)
    summary_col_interview = ColumnName.INTERVIEW_SUMMARY
    summary_col_daily = ColumnName.DAILY_REPORT_SUMMARY
    advice_col = ColumnName.AI_ADVICE
# (略)
        data_type = row.get('データ種別', '不明') # 'データ種別'はDBから来るので定数化対象外
        if data_type == '面談要約':
# (略)
        danger_signal = str(row.get(ColumnName.DANGER_SIGNAL, 'N/A')).replace("nan", "")
        danger_reason = str(row.get(ColumnName.DANGER_SIGNAL_REASON, 'N/A')).replace("nan", "")
# (略)
        if data_type == '日報分析':
# (略)
def ask_question_to_ai(question, chat_session, initial_context=None):
# (略)
        if AI_BACKEND == ConfigKeys.GEMINI:
# (略)
        elif AI_BACKEND == ConfigKeys.OLLAMA:
# (略)
def prepare_qa_data():
# (略)
    if AI_BACKEND == ConfigKeys.GEMINI:
# (略)
    elif AI_BACKEND == ConfigKeys.OLLAMA:
# (略)
def run_backend_process(mode, input_path=None, question=None, context=None, chat_session=None):
# (略)
    if mode in [AnalysisMode.INTERVIEW, AnalysisMode.QA, AnalysisMode.DAILY_REPORT]:
# (略)
        if AI_BACKEND == ConfigKeys.GEMINI:
# (略)
    if mode == AnalysisMode.INTERVIEW:
# (略)
    elif mode == AnalysisMode.QA:
# (略)
    elif mode == AnalysisMode.DAILY_REPORT:
# (略)
    elif mode == AnalysisMode.GET_DELETE_LIST:
# (略)
    elif mode == AnalysisMode.EXECUTE_DELETE:
# (略)
```
