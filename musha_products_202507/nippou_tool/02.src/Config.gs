const CONFIG = {
  // シート名
  BOT_QUESTION_LOG_SHEET_NAME: 'BOT質問ログ',
  DAILY_REPORT_LOG_SHEET_NAME: '日報ログ',
  CHATWORK_SETTINGS_SHEET_NAME: 'Chatwork設定',

  // メンバーごとの日報ログシート
  
  MEMBER_DAILY_REPORT_LOG_HEADERS: ['タイムスタンプ', '氏名', 'マネージャー', '日報日付', '今日の業務内容', '今日の気分', '困っていること'],

  // 日報・レポート関連
  
  WEEKLY_REPORT_FETCH_DAYS: 7, // 週次レポート用日報ログ取得日数
  REPRESENTATIVE_REPORTS_COUNT: 5, // getDailyReportDataForEmployee内の代表日報抜粋数
  REPORT_TAG: '#日報',

  // テキスト・メッセージ関連
  TRUNCATE_TEXT_MAX_LENGTH: 100,
  TRUNCATE_TEXT_MAX_LENGTH_EXCERPT: 50,
  DEFAULT_VALUES: {
    NOT_APPLICABLE: 'N/A',
    NO_PROBLEM: '特になし',
    UNKNOWN: '不明',
    NO_RESPONSE: 'Gemini APIからの応答がありませんでした。'
  },
  ANONYMOUS_EMPLOYEE_NAME: '対象者',
  ANONYMOUS_EMPLOYEE_NAME_SHORT: 'メンバー',

  // Chatwork関連
  CHATWORK_API_BASE_URL: 'https://api.chatwork.com/v2',
  CHATWORK_FETCH_MESSAGE_COUNT: 50,
  CHATWORK_ROLE_MANAGER: 'manager',
  CHATWORK_ROLE_EMPLOYEE: 'employee',
  CHATWORK_SETTINGS_HEADERS: ['グループ名', '氏名', 'ルームID', '役割', '週次レポートモード'],

  // ステータス文字列
  STATUS_STRINGS: {
    SUCCESS: '返信済み_処理成功',
    PENDING: '未返信',
    INVALID_FORMAT: '返信済み_フォーマット不正',
    ERROR_GENERAL: 'エラー発生_その他',
    ERROR_PREFIX: 'エラー発生',
    DANGER: '危険',
    WARNING: '少し悪い',
    BAD: '悪い',
    NORMAL: '普通',
  },

  // 気分選択肢
  MOOD_OPTIONS: ['良い', '普通', '少し悪い', '悪い'],

  // 問題キーワード
  PROBLEM_KEYWORDS: ['疲労', '残業', '人間関係', '遅延', 'プレッシャー', 'モチベーション', 'コミュニケーション', 'スキル', '不明点', '認識齟齬'],
  
  // ポジティブキーワード
  POSITIVE_KEYWORDS: {
    RELEASE: 'リリース',
    CUSTOMER_APPRECIATION_KEYWORDS: ['顧客', '高評価', '感謝'],
    IMPROVEMENT: '改善',
    ACHIEVEMENT: '達成'
  },

  // 自己評価関連
  

  // スクリプトプロパティキー
  CHATWORK_API_KEY: 'CHATWORK_API_KEY',
  GEMINI_API_KEY: 'GEMINI_API_KEY',
  CHATWORK_BOT_ACCOUNT_ID_KEY: 'CHATWORK_BOT_ACCOUNT_ID',
  

  // Gemini API
  GEMINI_MODEL_NAME: 'gemini-2.0-flash',

  // 定期実行トリガー設定
  TRIGGER_SETTINGS: {
    WEEKLY_REPORT_HOUR: 10,
    CLEANUP_HOUR: 2,
    CLEANUP_LOG_OLDER_THAN_DAYS: 7,
  },
  SCHEDULE_DEFAULTS: {
    questionHour: 9,
    questionMinute: 0,
    replyHour: 18,
    replyMinute: 0
  },
  
  // 週次レポート関連
  COMMON_PROBLEMS_MIN_COUNT: 2, // 共通課題として認識する最小出現回数
  COMMON_PROBLEMS_MAX_DISPLAY: 5, // 共通課題の最大表示数
  DEFAULT_WEEKLY_REPORT_MODE: 'individual', // 週次レポートモードのデフォルト値
  WEEKLY_REPORT_MODES: { 
    INDIVIDUAL: 'individual', 
    TEAM: 'team' 
  },

  // 日報ログシートのフォーマット
  DAILY_REPORT_LOG_COLUMN_WIDTHS: [
    { index: 1, width: 125 }, // A列: タイムスタンプ
    { index: 2, width: 100 }, // B列: 氏名
    { index: 3, width: 100 }, // C列: マネージャー
    { index: 4, width: 100 }, // D列: 日報日付
    { index: 5, width: 300 }, // E列: 今日の業務内容
    { index: 6, width: 100 }, // F列: 今日の気分
    { index: 7, width: 430 }, // G列: 困っていること
  ],
  DAILY_REPORT_LOG_HEADER_BG_COLOR: '#A4C2F4', // 明るいコーンフラワー ブルー 3

  // --- 正規表現 ---
  CHATWORK_REPLY_REGEX: /\[rp aid=(\d+) to=(\d+)-(\d+)\]/,
  PARSE_REPORT_REGEX: {
    WORK_CONTENT: /業務内容：\s*([\s\S]*?)(?=\n*気分：|\n*困っていること：|$)/,
    MOOD: /気分：\s*([\s\S]*?)(?=\n*困っていること：|$)/,
    PROBLEMS: /困っていること：\s*([\s\S]*)/
  },

  // --- Geminiプロンプトテンプレート ---
  DAILY_REPORT_QUESTION_MESSAGE_TEMPLATE: `[To:{employeeRoomId}] {employeeName}さん\nおはようございます！\n本日の日報を以下のフォーマットでご返信ください。\n\n#日報\n業務内容：\n気分：(良い/普通/少し悪い/悪い)\n困っていること：`,

  DAILY_REPORT_ASSESS_PROMPT_TEMPLATE: `以下の日報の内容を分析し、提出者の現在の心理状態や業務の調子について、**4段階（良い、普通、少し悪い、悪い）で評価してください。ただし、特に「今日の気分」が悪い場合や、「困っていること」にネガティブな兆候が見られる場合は、評価を「危険」としてください。**\n氏名は匿名化し、「提出者」として言及してください。\n\n業務内容：{workContent}\n気分：{mood}\n困っていること：{problems}\n\n結果はJSON形式で返してください。例: { "status": "危険", "reason": "具体例：今日の気分が悪いと申告しており、困っている内容にXXとあるため。" }`,

  DAILY_REPORT_ALERT_SUBJECT_TEMPLATE: `【注意】日報から社員の調子に懸念 - {employeeName}`,
  DAILY_REPORT_ALERT_BODY_TEMPLATE: `[info][title]{subject}[/title]提出者：{employeeName}\n日付：{date}\nGemini AIによる評価：{geminiStatus}\n理由：{geminiReason}\n[hr]▼ 日報抜粋\n今日の気分：{mood}\n困っていること：{problems}\n[hr]詳細については、スプレッドシートをご確認ください。[/info]`,

  WEEKLY_REPORT_PROMPT_TEMPLATE: `以下の{subjectName}の過去1週間分のデータから、この{reportType}のコンディションの傾向、主な課題、ポジティブな動きについて分析し、簡潔なサマリーレポートを生成してください。
マネージャーが週ごとの傾向を**一目で把握できるよう、以下のフォーマットに厳密に従って**記述してください。

**過去1週間分の{subjectName}のデータ：**
{dataSummary}

▼ 今週の{subjectName}コンディションサマリー
ここにレポート本文を記述。物語形式で、メンバーまたはチームの「空気感」を伝えるように記述してください。全体で最大250文字程度に収めてください。
以下の要素を盛り込むことを推奨します。
- 全体的な傾向や雰囲気
- 特に注目すべきポジティブな点（具体的な業務内容や成果に触れる）
- 潜在的な課題や懸念点（背景や影響にも触れる）
- 変化の兆候や、今後注目すべき点
`,
  INDIVIDUAL_REPORT_SUBJECT_TEMPLATE: `【週次メンバーコンディションレポート】{anonymousName} - {date}週`,
  INDIVIDUAL_REPORT_BODY_TEMPLATE: ``, // This seems unused in the code, keeping it empty as per prompt.
  TEAM_SUMMARY_SUBJECT_TEMPLATE: `【週次チームコンディションサマリー】{groupName} - {date}週`,
  TEAM_SUMMARY_BODY_TEMPLATE: `{subject}\n\n{reportBody}`,
};