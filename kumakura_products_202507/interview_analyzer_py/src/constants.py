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