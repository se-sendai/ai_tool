# テストツール

このディレクトリには、`backend_logic.py`の各機能をGUIを介さずに検証するためのテストコードが含まれています。

## 目的

*   バックエンドロジックの単体テスト
*   機能追加や修正時のデグレード防止
*   GUIに依存しない形での機能検証

## 実行方法

プロジェクトのルートディレクトリで以下のコマンドを実行してください。

```bash
python -m unittest tests/test_backend_logic.py
```

## テストケースの概要

*   `test_process_interviews_logic_single_csv`: 単一のCSVファイルに対する面談分析処理をテストします。
*   `test_process_interviews_logic_folder`: フォルダ内の複数CSVファイルに対する面談分析処理をテストします。
*   `test_process_daily_reports_logic`: 日報分析処理をテストします。
*   `test_ask_question_to_ai_gemini`: Gemini AI対話機能をテストします。
*   `test_ask_question_to_ai_ollama`: Ollama AI対話機能をテストします。
*   `test_handle_delete_request_single`: 単一データ削除機能をテストします。
*   `test_handle_delete_request_bulk`: まとめ削除機能をテストします。
*   `test_load_config`: `config.ini`のロード処理をテストします。
*   `test_call_ai_model_gemini`: Geminiモデルの呼び出し処理をテストします。
*   `test_call_ai_model_ollama`: Ollamaモデルの呼び出し処理をテストします。
*   `test_get_summary_from_ai`: AIによる要約生成処理をテストします。
*   `test_get_advice_from_ai`: AIによるアドバイス生成処理をテストします。
*   `test_get_danger_signal_from_ai`: AIによる危険信号判定処理をテストします。
*   `test_analyze_dataframe_structure_with_ai`: データフレーム構造分析処理をテストします。

## テストの網羅性について

主要なバックエンドロジックの関数はすべてテストケースで網羅されています。

ただし、GUI (`app_gui.py`) のUI操作や、`database_handler.py`のデータベース操作（SQLiteの実際のファイル操作）については、モック化されているため、**実際のファイルシステムやデータベースとの連携部分のテストは含まれていません。**

また、`detect_encoding.py`や`inspect_db.py`のようなユーティリティスクリプトはテスト対象外です。