# プロジェクト引き継ぎ資料: Interview Analyzer

このドキュメントは、Interview Analyzerプロジェクトをスムーズに引き継ぐための情報を提供します。

## 1. プロジェクト概要

Interview Analyzerは、ExcelまたはCSV形式の面談データや日報データをAI（Google GeminiまたはOllama）で分析し、要約、アドバイス、危険信号の判定を行うデスクトップアプリケーションです。生成されたデータはSQLiteデータベースに保存され、AIとのチャット形式での対話も可能です。

## 2. プロジェクト構造

```
interview_analyzer_py/
├── .git/                 # Gitリポジトリ情報
├── build/                # PyInstallerビルド時の一時ファイル (Git管理外)
├── dist/                 # PyInstallerビルド成果物 (exeファイルのみGit管理)
├── docs/                 # 各種ドキュメント、設計書、コードレビューノート
├── handover_docs/        # この引き継ぎ資料が格納される
├── logs/                 # アプリケーションのログファイル (Git管理外)
├── src/                  # アプリケーションのソースコード
│   ├── app_gui.py        # GUIのメインロジック
│   ├── backend_logic.py  # バックエンドの主要処理（AI連携、データ分析）
│   ├── constants.py      # 各種定数定義
│   ├── database_handler.py # SQLiteデータベース操作
│   ├── template_config.ini # config.iniのテンプレート
│   └── ui_state_manager.py # UIの状態管理
├── tests/                # テストコードとテスト用ダミーファイル
│   ├── dummy_folder/     # 面談分析テスト用ダミーCSV
│   ├── dummy_interview.csv # 面談分析テスト用ダミーCSV
│   ├── dummy_daily_report.xlsx # 日報分析テスト用ダミーExcel
│   └── test_backend_logic.py # backend_logicのテスト
│   └── README.md         # テストツールの説明
├── tools/                # 開発・デバッグ用ユーティリティスクリプト
│   ├── detect_encoding.py # ファイルエンコーディング検出
│   └── inspect_db.py     # データベース内容確認
│   └── README.md         # ツール説明
├── website/              # HTML形式の説明資料
├── .gitignore            # Git管理対象外ファイル・ディレクトリ指定
├── interview_analyzer.spec # PyInstallerビルド設定ファイル
├── requirements.txt      # Python依存ライブラリリスト
```

## 3. 開発環境のセットアップ

1.  **リポジトリのクローン**: 
    `git clone [リポジトリURL]`
2.  **Python環境の準備**: 
    Python 3.8以上を推奨します。venvなどで仮想環境を構築してください。
3.  **依存ライブラリのインストール**: 
    `pip install -r requirements.txt`
4.  **`config.ini`の準備**: 
    プロジェクトルートに`config.ini`ファイルを作成し、`src/template_config.ini`を参考にAIバックエンドの設定を行ってください。
    *注意: `config.ini`はGit管理外です。*

## 4. 主要な機能とロジック

*   **`app_gui.py`**: カスタムTkinterを使用したGUIアプリケーションのメインエントリポイントです。UIの構築、イベントハンドリング、バックエンドロジックとの連携を担当します。
*   **`backend_logic.py`**: アプリケーションの主要なビジネスロジックが含まれています。AIモデル（Gemini/Ollama）との連携、データ分析（面談要約、日報分析）、危険信号の判定などを行います。
*   **`database_handler.py`**: SQLiteデータベース（`analyzer_data.db`）へのデータの保存、読み込み、削除などの操作を管理します。
*   **`constants.py`**: アプリケーション全体で使用される定数（モード名、カラム名、UIテキストなど）を一元的に管理します。

## 5. ビルドと配布

PyInstallerを使用してアプリケーションを単一の実行ファイル（`.exe`）としてバンドルします。

1.  **ビルドコマンド**: 
    `pyinstaller interview_analyzer.spec`
2.  **ビルド成果物**: 
    `dist/interview_analyzer_gui.exe` が生成されます。
    *注意: `dist`フォルダ内の`.exe`ファイルのみがGit管理対象です。その他のファイルはビルド時に自動生成されるため、Git管理外です。*
3.  **配布時の注意点**: 
    `interview_analyzer_gui.exe` と同じディレクトリに、適切に設定された`config.ini`ファイルを配置する必要があります。

## 6. Gitワークフロー

*   **ブランチ**: `development`ブランチで開発を行います。
*   **コミット**: 意味のある変更ごとにコミットを行い、分かりやすいコミットメッセージを記述してください。
*   **プッシュ**: `git push`でリモートリポジトリにプッシュします。

## 7. 既知の問題と今後の課題

`docs/code_review_notes.md`に詳細が記載されていますが、主要なものを以下に示します。

*   **設定ファイルのパス解決**: PyInstallerでバンドルされた際の`config.ini`、ログファイル、出力ディレクトリのパス解決の柔軟性向上。
*   **エラーハンドリングの粒度**: `backend_logic.py`の`call_ai_model`関数におけるエラーハンドリングの粒度をより具体的にする。
*   **APIキーの管理**: `config.ini`に直接APIキーを記述する形式のセキュリティ強化。
*   **Ollamaのセットアップ**: ユーザーがOllamaをセットアップする際の負担軽減。
*   **UI/UXの改善**: エラーメッセージのユーザーフレンドリー化、パフォーマンス改善など。

## 8. その他

*   **テストツール**: `tests/`ディレクトリにバックエンドロジックのテストコードがあります。`python -m unittest tests/test_backend_logic.py`で実行できます。
*   **開発用ユーティリティ**: `tools/`ディレクトリに開発・デバッグ用のスクリプトがあります。