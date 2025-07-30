import sys
import os
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

# backend_logic.pyがimportできるようにパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import backend_logic
from constants import AnalysisMode, ConfigKeys, FileAndDir, ColumnName, DataStructure

class TestBackendLogic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # テスト前にconfig.iniをロード
        backend_logic.load_config()

    def setUp(self):
        # 各テストの前に実行されるセットアップ
        pass

    def tearDown(self):
        # 各テストの後に実行されるクリーンアップ
        pass

    # --- 面談分析のテスト ---
    def test_process_interviews_logic_single_csv(self):
        # 単一CSVファイルの面談分析テスト
        dummy_csv_path = "./tests/dummy_interview.csv"
        
        # backend_logic.process_interviews_logicのモック化
        with patch('backend_logic.load_data') as mock_load_data:
            with patch('backend_logic.analyze_dataframe_structure_with_ai') as mock_analyze_structure:
                with patch('backend_logic.get_summary_from_ai') as mock_get_summary:
                    with patch('backend_logic.get_advice_from_ai') as mock_get_advice:
                        with patch('backend_logic.save_individual_reports') as mock_save_reports:
                            with patch('database_handler.save_interview_to_db') as mock_save_to_db:

                                # モックの戻り値を設定
                                # ダミーCSVの内容に合わせたDataFrameを作成
                                mock_df = pd.DataFrame({
                                    ColumnName.EMPLOYEE_NAME: ["山田太郎"],
                                    "面談内容": ["今日の面談は順調でした。新しいプロジェクトへの参加意欲が高いです。"],
                                    ColumnName.SKILLS: ["Python"],
                                    "面談日": ["2023/01/15"]
                                })
                                mock_load_data.return_value = mock_df

                                mock_analyze_structure.return_value = {
                                    'structure': DataStructure.WIDE,
                                    'employee_col': ColumnName.EMPLOYEE_NAME,
                                    'comment_col': "面談内容",
                                    'skills_col': ColumnName.SKILLS,
                                    'interview_date_col': "面談日"
                                }
                                mock_get_summary.return_value = "要約テスト"
                                mock_get_advice.return_value = "アドバイステスト"
                                mock_save_reports.return_value = "./output/test_report.csv"
                                mock_save_to_db.return_value = None

                                # テスト実行
                                result_msg, saved_paths = backend_logic.process_interviews_logic(dummy_csv_path)

                                # アサーション
                                self.assertIn("面談分析の処理が完了しました。", result_msg)
                                self.assertGreater(len(saved_paths), 0)
                                mock_load_data.assert_called_once_with(dummy_csv_path)
                                mock_analyze_structure.assert_called_once()
                                mock_get_summary.assert_called_once()
                                mock_get_advice.assert_called_once()
                                mock_save_reports.assert_called_once()
                                mock_save_to_db.assert_called_once()

    def test_process_interviews_logic_folder(self):
        # フォルダ内の複数CSVファイルの面談分析テスト
        dummy_folder_path = "./tests/dummy_folder"
        
        # backend_logic.process_interviews_logicのモック化
        with patch('os.listdir', return_value=['dummy_interview_2.csv', 'dummy_interview_3.csv']):
            with patch('os.path.isfile', side_effect=lambda x: x.endswith('.csv') or x.endswith('.xlsx')):
                with patch('backend_logic.load_data') as mock_load_data:
                    with patch('backend_logic.analyze_dataframe_structure_with_ai') as mock_analyze_structure:
                        with patch('backend_logic.get_summary_from_ai') as mock_get_summary:
                            with patch('backend_logic.get_advice_from_ai') as mock_get_advice:
                                with patch('backend_logic.save_individual_reports') as mock_save_reports:
                                    with patch('database_handler.save_interview_to_db') as mock_save_to_db:

                                        # モックの戻り値を設定
                                        mock_df_2 = pd.DataFrame({
                                            ColumnName.EMPLOYEE_NAME: ["佐藤花子"],
                                            "面談内容": ["チームとの連携がスムーズでした。"],
                                            ColumnName.SKILLS: ["JavaScript"],
                                            "面談日": ["2023/02/01"]
                                        })
                                        mock_df_3 = pd.DataFrame({
                                            ColumnName.EMPLOYEE_NAME: ["田中次郎"],
                                            "面談内容": ["新しい技術の習得に意欲的です。"],
                                            ColumnName.SKILLS: ["Java"],
                                            "面談日": ["2023/02/05"]
                                        })
                                        mock_load_data.side_effect = [mock_df_2, mock_df_3]

                                        mock_analyze_structure.return_value = {
                                            'structure': DataStructure.WIDE,
                                            'employee_col': ColumnName.EMPLOYEE_NAME,
                                            'comment_col': "面談内容",
                                            'skills_col': ColumnName.SKILLS,
                                            'interview_date_col': "面談日"
                                        }
                                        mock_get_summary.side_effect = ["要約テスト2", "要約テスト3"]
                                        mock_get_advice.side_effect = ["アドバイステスト2", "アドバイステスト3"]
                                        mock_save_reports.side_effect = ["./output/test_report_2.csv", "./output/test_report_3.csv"]
                                        mock_save_to_db.return_value = None

                                        # テスト実行
                                        result_msg, saved_paths = backend_logic.process_interviews_logic(dummy_folder_path)

                                        # アサーション
                                        self.assertIn("面談分析の処理が完了しました。", result_msg)
                                        self.assertEqual(len(saved_paths), 2)
                                        self.assertEqual(mock_load_data.call_count, 2)
                                        self.assertEqual(mock_analyze_structure.call_count, 2)
                                        self.assertEqual(mock_get_summary.call_count, 2)
                                        self.assertEqual(mock_get_advice.call_count, 2)
                                        self.assertEqual(mock_save_reports.call_count, 2)
                                        self.assertEqual(mock_save_to_db.call_count, 2)

    # --- 日報分析のテスト ---
    def test_process_daily_reports_logic(self):
        # 日報分析テスト
        dummy_excel_path = "./tests/dummy_daily_report.xlsx"

        with patch('backend_logic.load_data') as mock_load_data:
            with patch('backend_logic.get_daily_report_summary_from_ai') as mock_get_summary:
                with patch('backend_logic.get_daily_report_advice_from_ai') as mock_get_advice:
                    with patch('backend_logic.get_danger_signal_from_ai') as mock_get_danger_signal:
                        with patch('database_handler.save_daily_report_to_db') as mock_save_to_db:
                            with patch('backend_logic.DAILY_REPORT_PERIOD', 'monthly'): # 月次集計をテスト

                                # モックの戻り値を設定
                                # load_dataがシート名に応じて異なるDataFrameを返すように設定
                                mock_df_yamada = pd.DataFrame({
                                    'タイムスタンプ': [
                                        pd.Timestamp('2023-07-03 09:00:00'),
                                        pd.Timestamp('2023-07-04 09:00:00'),
                                        pd.Timestamp('2023-07-05 09:00:00'),
                                        pd.Timestamp('2023-07-10 09:00:00'),
                                        pd.Timestamp('2023-07-11 09:00:00'),
                                    ],
                                    '今日の体調': ['良好', '良好', '普通', '良好', 'やや疲労'],
                                    '今日の気分': ['良い', '良い', '普通', '良い', '普通'],
                                    '今日の業務内容': ['Aプロジェクトの設計', 'Aプロジェクトの実装', 'Bプロジェクトのレビュー', 'Cプロジェクトの打ち合わせ', 'Aプロジェクトのテスト'],
                                    '業務での課題や悩み': ['特になし', '特になし', '設計で考慮漏れがあった', '特になし', 'テスト環境の構築に手間取った'],
                                    'その他、共有事項': ['なし', 'なし', 'なし', 'なし', 'なし'],
                                })
                                mock_df_sato = pd.DataFrame({
                                    'タイムスタンプ': [
                                        pd.Timestamp('2023-07-03 09:00:00'),
                                        pd.Timestamp('2023-07-04 09:00:00'),
                                        pd.Timestamp('2023-07-05 09:00:00'),
                                    ],
                                    '今日の体調': ['良好', '良好', '良好'],
                                    '今日の気分': ['良い', '良い', '良い'],
                                    '今日の業務内容': ['Dプロジェクトの資料作成', 'Dプロジェクトの進捗報告', 'Eプロジェクトの調査'],
                                    '業務での課題や悩み': ['特になし', '特になし', '情報収集に時間がかかった'],
                                    'その他、共有事項': ['なし', 'なし', 'なし'],
                                })
                                
                                # ExcelFileのモックを作成し、sheet_namesプロパティを設定
                                mock_excel_file = MagicMock()
                                mock_excel_file.sheet_names = ["山田太郎", "佐藤花子"]
                                
                                # backend_logic.load_dataがシート名に応じて異なるDataFrameを返すように設定
                                def load_data_side_effect(file_path, sheet_name=None):
                                    if sheet_name == "山田太郎":
                                        return mock_df_yamada
                                    elif sheet_name == "佐藤花子":
                                        return mock_df_sato
                                    return None

                                mock_load_data.side_effect = load_data_side_effect

                                mock_get_summary.return_value = "日報要約テスト"
                                mock_get_advice.return_value = "日報アドバイステスト"
                                mock_get_danger_signal.return_value = {"signal": "false", "reason": "問題なし"}
                                mock_save_to_db.return_value = None

                                # backend_logic.process_daily_reports_logicの内部でExcelFileが使われるため、
                                # pd.ExcelFileをモック化し、そのインスタンスがsheet_namesを持つようにする
                                with patch('pandas.ExcelFile', return_value=mock_excel_file):
                                    # テスト実行
                                    result_msg, saved_paths = backend_logic.process_daily_reports_logic(dummy_excel_path)

                                    # アサーション
                                    self.assertIn("日報データの処理が完了しました。", result_msg)
                                    # 山田太郎（1期間）と佐藤花子（1期間）で合計2つのファイルが保存される想定
                                    self.assertEqual(len(saved_paths), 2)
                                    self.assertEqual(mock_load_data.call_count, 2) # 山田太郎と佐藤花子の2シート
                                    self.assertEqual(mock_get_summary.call_count, 2) # 山田太郎1期間、佐藤花子1期間
                                    self.assertEqual(mock_get_advice.call_count, 2)
                                    self.assertEqual(mock_get_danger_signal.call_count, 2)
                                    self.assertEqual(mock_save_to_db.call_count, 2)

    # --- AI対話のテスト ---
    def test_ask_question_to_ai_gemini(self):
        # Gemini AI対話テスト
        with patch('google.generativeai.GenerativeModel') as MockGenerativeModel:
            with patch('backend_logic.AI_BACKEND', ConfigKeys.GEMINI):
            
                mock_chat_session = MagicMock()
                mock_chat_session.send_message.return_value.text = "AIからの回答です。"
                MockGenerativeModel.return_value.start_chat.return_value = mock_chat_session

                question = "今日の天気は？"
                initial_context = ""
                
                result = backend_logic.ask_question_to_ai(question, mock_chat_session, initial_context)
                
                self.assertEqual(result, "AIの回答: AIからの回答です。")
                mock_chat_session.send_message.assert_called_once_with(question)

    def test_ask_question_to_ai_ollama(self):
        # Ollama AI対話テスト
        with patch('requests.post') as mock_post:
            with patch('backend_logic.AI_BACKEND', ConfigKeys.OLLAMA):
                with patch('backend_logic.OLLAMA_URL', "http://localhost:11434"):
                    with patch('backend_logic.OLLAMA_MODEL', "llama2"):
            
                        mock_response = MagicMock()
                        mock_response.json.return_value = {'message': {'content': "Ollamaからの回答です。"}}
                        mock_response.raise_for_status.return_value = None
                        mock_post.return_value = mock_response

                        question = "今日の天気は？"
                        chat_history = [] # Ollamaの場合はメッセージ履歴を渡す
                        
                        result = backend_logic.ask_question_to_ai(question, chat_history)
                        
                        self.assertEqual(result, "AIの回答: Ollamaからの回答です。")
                        mock_post.assert_called_once()
                        self.assertEqual(len(chat_history), 2) # 質問と回答が追加される
                        self.assertEqual(chat_history[0]['content'], question)
                        self.assertEqual(chat_history[1]['content'], "Ollamaからの回答です。")

    # --- 削除機能のテスト ---
    def test_handle_delete_request_single(self):
        # 単一データ削除テスト
        with patch('database_handler.delete_record_from_db') as mock_delete_record:
            mock_delete_record.return_value = True
            selection_string = "山田太郎 ID:yamada_001 (20230115) (面談)"
            result = backend_logic.handle_delete_request(selection_string)
            self.assertIn("データを正常に削除しました", result)
            mock_delete_record.assert_called_once_with("山田太郎", "yamada_001", "(20230115) (面談)", False)

    def test_handle_delete_request_bulk(self):
        # まとめ削除テスト
        with patch('database_handler.delete_record_from_db') as mock_delete_record:
            mock_delete_record.return_value = True
            selection_string = "[まとめ] 山田太郎 ID:yamada_001 (全データ削除)"
            result = backend_logic.handle_delete_request(selection_string)
            self.assertIn("データを正常に削除しました", result)
            mock_delete_record.assert_called_once_with("山田太郎", "yamada_001", "", True)

    # --- その他のユーティリティ関数のテスト ---
    def test_load_config(self):
        # config.iniのロードテスト
        mock_config = MagicMock()
        mock_config.__getitem__.side_effect = lambda key: {
            'ai_backend': {'ai_backend': 'gemini'},
            'gemini': {'api_key': 'test_api_key', 'model_version': 'gemini-pro'},
            'ollama': {'ollama_url': 'http://localhost:11434', 'ollama_model': 'llama2'},
            'daily_report': {'period': 'weekly'}
        }[key]
        mock_config.sections.return_value = ['ai_backend', 'gemini', 'ollama', 'daily_report']
        mock_config.get.side_effect = lambda section, option, fallback=None: {
            'gemini': {'model_version': 'gemini-pro'}
        }.get(section, {}).get(option, fallback)

        with patch('configparser.ConfigParser', return_value=mock_config):
            with patch('backend_logic.genai.configure') as mock_genai_configure:
                with patch('backend_logic.logging.error') as mock_logging_error:

                    result = backend_logic.load_config()
                    self.assertTrue(result)
                    self.assertEqual(backend_logic.AI_BACKEND, 'gemini')
                    self.assertEqual(backend_logic.GEMINI_MODEL, 'gemini-pro')
                    self.assertEqual(backend_logic.DAILY_REPORT_PERIOD, 'weekly')
                    mock_genai_configure.assert_called_once_with(api_key='test_api_key')
                    mock_logging_error.assert_not_called()

        # エラーケースのテスト (APIキーなし)
        mock_config_no_api_key = MagicMock()
        mock_config_no_api_key.__getitem__.side_effect = lambda key: {
            'ai_backend': {'ai_backend': 'gemini'},
            'gemini': {'api_key': 'YOUR_API_KEY'},
            'daily_report': {'period': 'weekly'}
        }[key]
        mock_config_no_api_key.sections.return_value = ['ai_backend', 'gemini', 'daily_report']
        mock_config_no_api_key.get.side_effect = lambda section, option, fallback=None: {
            'gemini': {'model_version': 'gemini-pro'}
        }.get(section, {}).get(option, fallback)

        with patch('configparser.ConfigParser', return_value=mock_config_no_api_key):
            with patch('backend_logic.genai.configure'):
                with patch('backend_logic.logging.error') as mock_logging_error:

                    result = backend_logic.load_config()
                    self.assertFalse(result)
                    mock_logging_error.assert_called_with("Gemini APIが選択されていますが、APIキーがconfig.iniに設定されていません。")

    def test_call_ai_model_gemini(self):
        # Geminiモデル呼び出しテスト
        with patch('backend_logic.genai.GenerativeModel') as MockGenerativeModel:
            with patch('backend_logic.AI_BACKEND', ConfigKeys.GEMINI):
                with patch('backend_logic.GEMINI_MODEL', 'gemini-pro'):
            
                    mock_model_instance = MagicMock()
                    mock_model_instance.generate_content.return_value.text = "Geminiからの応答です。"
                    MockGenerativeModel.return_value = mock_model_instance

                    prompt = "テストプロンプト"
                    result = backend_logic.call_ai_model(prompt)
                    
                    self.assertEqual(result, "Geminiからの応答です。")
                    MockGenerativeModel.assert_called_once_with('gemini-pro')
                    mock_model_instance.generate_content.assert_called_once_with(prompt, request_options={'timeout': 60})

    def test_call_ai_model_ollama(self):
        # Ollamaモデル呼び出しテスト
        with patch('requests.post') as mock_post:
            with patch('backend_logic.AI_BACKEND', ConfigKeys.OLLAMA):
                with patch('backend_logic.OLLAMA_URL', "http://localhost:11434"):
                    with patch('backend_logic.OLLAMA_MODEL', "llama2"):
            
                        mock_response = MagicMock()
                        mock_response.json.return_value = {'response': "Ollamaからの応答です。"}
                        mock_response.raise_for_status.return_value = None
                        mock_post.return_value = mock_response

                        prompt = "テストプロンプト"
                        result = backend_logic.call_ai_model(prompt)
                        
                        self.assertEqual(result, "Ollamaからの応答です。")
                        mock_post.assert_called_once_with("http://localhost:11434/api/generate", headers={'Content-Type': 'application/json'}, json={'model': 'llama2', 'prompt': prompt, 'stream': False}, timeout=60)

    def test_get_summary_from_ai(self):
        # AI要約生成テスト
        with patch('backend_logic.call_ai_model') as mock_call_ai_model:
            mock_call_ai_model.return_value = "AIによる要約です。"
            text_data = "面談内容のテキストデータ"
            summary = backend_logic.get_summary_from_ai(text_data)
            self.assertEqual(summary, "AIによる要約です。")
            mock_call_ai_model.assert_called_once()

    def test_get_advice_from_ai(self):
        # AIアドバイス生成テスト
        with patch('backend_logic.call_ai_model') as mock_call_ai_model:
            mock_call_ai_model.return_value = "AIによるアドバイスです。"
            summary = "要約されたテキストデータ"
            advice = backend_logic.get_advice_from_ai(summary)
            self.assertEqual(advice, "AIによるアドバイスです。")
            mock_call_ai_model.assert_called_once()

    def test_get_danger_signal_from_ai(self):
        # AI危険信号判定テスト
        with patch('backend_logic.call_ai_model') as mock_call_ai_model:
            mock_call_ai_model.return_value = '{"signal": "true", "reason": "体調不良の兆候あり"}'
            daily_reports_text = "日報のテキストデータ"
            result = backend_logic.get_danger_signal_from_ai(daily_reports_text)
            self.assertEqual(result['signal'], "true")
            self.assertEqual(result['reason'], "体調不良の兆候あり")
            mock_call_ai_model.assert_called_once()

    def test_analyze_dataframe_structure_with_ai(self):
        # データフレーム構造分析テスト
        with patch('backend_logic.call_ai_model') as mock_call_ai_model:
            mock_call_ai_model.return_value = '{"structure": "横持ち", "employee_col": "従業員名"}'
            df_head_str = "CSVのヘッダー部分"
            result = backend_logic.analyze_dataframe_structure_with_ai(df_head_str)
            self.assertEqual(result['structure'], "横持ち")
            self.assertEqual(result['employee_col'], "従業員名")
            mock_call_ai_model.assert_called_once()

if __name__ == '__main__':
    unittest.main()
