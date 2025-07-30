import sys # これを追加！
import traceback # これを追加！
import customtkinter
from tkinter import filedialog
import threading
import backend_logic # backend_logic.pyをインポート
from tkinterdnd2 import DND_FILES, TkinterDnD as tkdnd # tkinterdnd2をインポート
import itertools # for spinner animation
import os # これを追加！
import logging # これを追加！
from tkinter import messagebox # 追加
from ui_state_manager import UiStateManager # UiStateManagerをインポート
from constants import AnalysisMode, UIDefaults # 定数をインポート

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        logging.debug("App.__init__ started.")
        self.TkdndVersion = tkdnd._require(self) # tkinterdnd2を有効化
        

        self.title("Interview Analyzer")
        self.geometry("800x600")

        # --- レイアウト設定 ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # ログエリアの行を拡張可能に

        # --- ウィジェットの作成と配置 ---

        # 1. モード選択フレーム
        self.mode_frame = customtkinter.CTkFrame(self)
        self.mode_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.mode_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.mode_variable = customtkinter.StringVar(value=AnalysisMode.INTERVIEW)
        self.interview_radio = customtkinter.CTkRadioButton(self.mode_frame, text=UIDefaults.INTERVIEW_MODE_TEXT, variable=self.mode_variable, value=AnalysisMode.INTERVIEW, command=self.on_mode_change)
        self.interview_radio.grid(row=0, column=0, padx=10, pady=10)
        self.daily_report_radio = customtkinter.CTkRadioButton(self.mode_frame, text=UIDefaults.DAILY_REPORT_MODE_TEXT, variable=self.mode_variable, value=AnalysisMode.DAILY_REPORT, command=self.on_mode_change)
        self.daily_report_radio.grid(row=0, column=1, padx=10, pady=10)
        self.qa_radio = customtkinter.CTkRadioButton(self.mode_frame, text=UIDefaults.QA_MODE_TEXT, variable=self.mode_variable, value=AnalysisMode.QA, command=self.on_mode_change)
        self.qa_radio.grid(row=0, column=2, padx=10, pady=10)

        # 2. 説明ラベル
        self.description_label = customtkinter.CTkLabel(self, text="「面談分析」: CSVファイルまたはフォルダを選択 | 「日報分析」: Excelファイルを選択 | 「AI対話」: 事前に分析が必要です", text_color="gray")
        self.description_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        # 3. ファイル/フォルダ選択フレーム (通常モード用)
        self.path_frame = customtkinter.CTkFrame(self)
        self.path_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        self.path_entry = customtkinter.CTkEntry(self.path_frame, placeholder_text="分析対象のファイルまたはフォルダのパス")
        self.path_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.path_entry.drop_target_register(DND_FILES)
        self.path_entry.dnd_bind('<<Drop>>', self.handle_drop)

        self.select_button_frame = customtkinter.CTkFrame(self.path_frame)
        self.select_button_frame.grid(row=0, column=1, padx=10, pady=10)

        self.file_button = customtkinter.CTkButton(self.select_button_frame, text="ファイル選択", command=self.select_file)
        self.file_button.pack(side="left", padx=5)
        self.folder_button = customtkinter.CTkButton(self.select_button_frame, text="フォルダ選択", command=self.select_folder)
        self.folder_button.pack(side="left", padx=5)

        # 4. 実行ボタンとステータスラベルのフレーム
        self.run_status_frame = customtkinter.CTkFrame(self)
        self.run_status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.run_status_frame.grid_columnconfigure(0, weight=1) # ボタンが中央に来るように

        self.run_button = customtkinter.CTkButton(self.run_status_frame, text="分析実行", command=self.start_analysis)
        self.run_button.grid(row=0, column=0, padx=10, pady=5)

        self.status_label = customtkinter.CTkLabel(self.run_status_frame, text="", text_color="yellow")
        self.status_label.grid(row=1, column=0, padx=10, pady=5)

        # 結果ファイル表示ボタン
        self.result_file_button = customtkinter.CTkButton(self.run_status_frame, text="", command=self.open_result_file)
        self.result_file_button.grid(row=2, column=0, padx=10, pady=5)
        self.result_file_button.grid_remove() # 最初は非表示
        self.result_file_path = None # 結果ファイルのパスを保持する変数

        # 結果フォルダ表示ボタン
        self.result_folder_button = customtkinter.CTkButton(self.run_status_frame, text="", command=self.open_result_folder)
        self.result_folder_button.grid(row=3, column=0, padx=10, pady=5)
        self.result_folder_button.grid_remove() # 最初は非表示
        self.result_folder_path = None # 結果フォルダのパスを保持する変数

        # AI対話モード用UI
        self.qa_chat_frame = customtkinter.CTkFrame(self)
        self.qa_chat_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew") # ログエリアの下に配置
        self.qa_chat_frame.grid_columnconfigure(0, weight=1) # 入力フィールドが広がるように
        self.qa_chat_frame.grid_columnconfigure(1, weight=0) # 送信ボタンは固定幅

        self.qa_input_entry = customtkinter.CTkEntry(self.qa_chat_frame, placeholder_text="AIへの質問を入力してください", state="disabled")
        self.qa_input_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.qa_send_button = customtkinter.CTkButton(self.qa_chat_frame, text="送信", command=self.send_qa_message, state="disabled")
        self.qa_send_button.grid(row=0, column=1, padx=10, pady=10)
        self.qa_end_button = customtkinter.CTkButton(self.qa_chat_frame, text="対話終了", command=self.end_qa_session, state="disabled")
        self.qa_end_button.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # 削除機能用UI
        self.delete_frame = customtkinter.CTkFrame(self)
        self.delete_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        self.delete_frame.grid_columnconfigure(0, weight=1) # ドロップダウンが広がるように

        self.delete_combobox = customtkinter.CTkComboBox(self.delete_frame, values=[UIDefaults.DELETE_PROMPT], command=self.on_delete_combobox_change)
        self.delete_combobox.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.delete_combobox.set(UIDefaults.DELETE_PROMPT) # 初期表示

        # 削除リスト更新ボタン (名称変更、位置変更)
        self.update_delete_list_button = customtkinter.CTkButton(self.delete_frame, text="要約結果リスト更新", command=self.update_delete_combobox)
        self.update_delete_list_button.grid(row=0, column=1, padx=10, pady=10)

        # 削除実行ボタン (位置変更、色変更)
        self.delete_button = customtkinter.CTkButton(self.delete_frame, text="削除実行", command=self.execute_delete, fg_color="red") # 色を赤に変更
        self.delete_button.grid(row=0, column=2, padx=10, pady=10)

        # スピナー関連の変数
        self.spinner_chars = itertools.cycle(['-', '\\', '|', '/'])
        self.spinner_id = None

        # 5. ログ表示エリア
        self.log_textbox = customtkinter.CTkTextbox(self, state="disabled")
        self.log_textbox.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")

        # AI対話のコンテキストを保持する変数
        self.qa_context = None
        self.in_qa_session = False # AI対話セッション中かどうかのフラグ
        self.is_path_entry_dnd_registered = True # path_entryがDND登録されているかどうかのフラグを追加

        # UiStateManagerのインスタンスを作成
        self.ui_manager = UiStateManager(self)

        # 初期UI設定
        self.on_mode_change() 

        # DB初期化
        logging.debug("About to import database_handler.")
        import database_handler
        logging.debug("Calling database_handler.initialize_database()...")
        database_handler.initialize_database()
        logging.debug("database_handler.initialize_database() finished.")

    # --- UIの表示/非表示を切り替える関数 ---
    def on_mode_change(self):
        selected_mode = self.mode_variable.get()
        if selected_mode == AnalysisMode.QA:
            # AI対話モードの初期UI状態を設定
            self.ui_manager.set_mode_qa_initial_state()
        else:
            # 通常モードのUI状態を設定
            self.ui_manager.set_mode_normal_state()

        # ログエリアをクリア (これはUI状態管理とは独立しているため残します)
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    # --- ボタンのコールバック関数 ---

    def select_file(self):
        selected_mode = self.mode_variable.get()
        if selected_mode == AnalysisMode.INTERVIEW:
            filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        else:
            filepath = filedialog.askopenfilename()
        if filepath:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, filepath)

    def select_folder(self):
        folderpath = filedialog.askdirectory()
        if folderpath:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folderpath)

    def start_analysis(self):
        logging.debug("start_analysis called.")
        mode = self.mode_variable.get()
        path = os.path.normpath(self.path_entry.get())

        # UIの状態をUiStateManager経由で設定 (処理中状態)
        self.ui_manager.set_processing_state()
        self.start_spinner()

        # ログエリアをクリア (これはUI状態管理とは独立しているため残します)
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

        # 結果ファイル表示ボタンを非表示に
        self.result_file_button.grid_remove()
        self.result_file_path = None

        # 結果フォルダ表示ボタンを非表示に
        self.result_folder_button.grid_remove()
        self.result_folder_path = None

        # その他のモードは既存の処理
        thread = threading.Thread(target=self.run_backend, args=(mode, path, None, None))
        thread.start()

    def start_qa_session_flow(self):
        logging.debug("start_qa_session_flow called.")
        # UIの状態をUiStateManager経由で設定 (処理中状態)
        self.ui_manager.set_processing_state()
        self.start_spinner()

        # 結果フォルダ表示ボタンを非表示に (これはUI状態管理とは独立しているため残します)
        self.result_folder_button.grid_remove()
        self.result_folder_path = None

        thread = threading.Thread(target=self._prepare_qa_session)
        thread.start()

    def _prepare_qa_session(self):
        logging.debug("_prepare_qa_session called.")
        self.log("AI対話モードの準備を開始します...")
        
        # backend_logicからデータを読み込み、件数とチャットセッションを取得
        initial_context, interview_count, daily_report_count, message, chat_session = backend_logic.prepare_qa_data()
        
        if initial_context is None:
            self.log(f"エラー: {message}")
            self.stop_spinner()
            self.run_button.configure(state="normal") # エラー時はAI対話開始ボタンを活性化
            return

        self.qa_context = initial_context # 初期コンテキストをインスタンス変数に保存
        self.chat_session = chat_session # チャットセッションをインスタンス変数に保存

        # 読み込み件数をログに表示
        self.log(f"面談要約データ {interview_count}件、日報分析データ {daily_report_count}件を読み込みました。")
        self.log("質問を入力して「送信」ボタンを押してください。")
        
        self.in_qa_session = True # AI対話セッション開始
        self.stop_spinner() # スピナーを停止

        # UIの状態をUiStateManager経由で設定
        self.ui_manager.set_qa_active_state()

    def update_delete_combobox(self):
        self.log("削除対象データを取得中...")
        # UIの状態をUiStateManager経由で設定 (削除関連UI非活性状態)
        self.ui_manager.set_delete_ui_inactive()
        self.start_spinner()
        thread = threading.Thread(target=self._update_delete_combobox_backend)
        thread.start()

    def _update_delete_combobox_backend(self):
        logging.debug("_update_delete_combobox_backend called.")
        deletable_items, _, _ = backend_logic.run_backend_process(mode=AnalysisMode.GET_DELETE_LIST)
        logging.debug(f"deletable_items from backend: {deletable_items}")
        if deletable_items and isinstance(deletable_items, list):
            self.after(0, lambda: self.delete_combobox.configure(values=deletable_items))
            self.after(0, lambda: self.delete_combobox.set(UIDefaults.DELETE_PROMPT))
            self.log(f"{len(deletable_items)}件の削除対象データを取得しました。")
        else:
            self.log("削除対象データが見つかりませんでした。")
            self.after(0, lambda: self.delete_combobox.configure(values=[UIDefaults.NO_ITEMS_TO_DELETE]))
            self.after(0, lambda: self.delete_combobox.set(UIDefaults.NO_ITEMS_TO_DELETE))
        
        self.stop_spinner()
        # UIの状態をUiStateManager経由で設定 (削除関連UI活性状態)
        self.ui_manager.set_delete_ui_active()

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def start_spinner(self):
        if self.spinner_id is None: # スピナーが既に実行中でないか確認
            self.status_label.configure(text="処理中...")
            self._animate_spinner()

    def _animate_spinner(self):
        current_char = next(self.spinner_chars)
        self.status_label.configure(text=f"処理中 {current_char}")
        self.spinner_id = self.after(100, self._animate_spinner) # 100msごとに更新

    def stop_spinner(self):
        if self.spinner_id:
            self.after_cancel(self.spinner_id)
            self.spinner_id = None
        self.status_label.configure(text="") # スピナー停止時にテキストをクリア

    def run_backend(self, mode, path, question, context):
        try:
            self.log(f"バックエンド処理開始: モード={mode}, パス={path if path else 'N/A'}")
            message, saved_paths = backend_logic.run_backend_process(mode, path, question, context)
            self.log(message)
            if saved_paths:
                if mode == AnalysisMode.INTERVIEW:
                    # 面談分析の場合、結果ファイル表示ボタンを表示
                    self.result_file_path = saved_paths[0] # 最初のファイルパスを保存
                    self.result_file_button.configure(text=f"結果ファイルを開く: {os.path.basename(self.result_file_path)}")
                    self.result_file_button.grid()
                    # 結果フォルダ表示ボタンも表示
                    self.result_folder_path = os.path.dirname(self.result_file_path)
                    self.result_folder_button.configure(text=f"結果フォルダを開く: {os.path.basename(self.result_folder_path)}")
                    self.result_folder_button.grid()
                elif mode == AnalysisMode.DAILY_REPORT:
                    # 日報分析の場合、結果フォルダ表示ボタンを表示
                    if saved_paths: # saved_pathsが空でないことを確認
                        self.result_folder_path = os.path.dirname(saved_paths[0]) # 最初のファイルパスのディレクトリを保存
                        self.result_folder_button.configure(text=f"結果フォルダを開く: {os.path.basename(self.result_folder_path)}")
                        self.result_folder_button.grid()
            self.stop_spinner()
            # 処理完了後、UIをアイドル状態に設定
            self.ui_manager.set_idle_state()
            
        except Exception as e:
            error_message = f"バックエンド処理中にエラーが発生しました: {e}\n{traceback.format_exc()}"
            self.log(error_message)
            messagebox.showerror("エラー", "バックエンド処理中にエラーが発生しました。ログを確認してください。")
            self.stop_spinner()
            # エラー発生後、UIをアイドル状態に設定
            self.ui_manager.set_idle_state()
            

    def open_result_file(self):
        if self.result_file_path and os.path.exists(self.result_file_path):
            os.startfile(self.result_file_path)
        else:
            self.log("結果ファイルが見つかりません。")

    def open_result_folder(self):
        if self.result_folder_path and os.path.exists(self.result_folder_path):
            os.startfile(self.result_folder_path)
        else:
            self.log("結果フォルダが見つかりません。")

    def handle_drop(self, event):
        # ドロップされたファイルパスを取得
        # Windowsの場合、パスは波括弧で囲まれていることがあるので除去
        filepath = event.data.replace("{", "").replace("}", "")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, filepath)
        self.log(f"ファイルがドロップされました: {filepath}")

    def send_qa_message(self):
        question = self.qa_input_entry.get()
        if not question:
            self.log("質問を入力してください。")
            return
        
        self.log(f"あなた: {question}")
        self.qa_input_entry.delete(0, "end") # 入力フィールドをクリア
        
        # UIの状態をUiStateManager経由で設定 (処理中状態)
        self.ui_manager.set_processing_state()
        self.start_spinner()
        
        # AIへの質問をスレッドで実行
        thread = threading.Thread(target=self._send_qa_message_backend, args=(question,))
        thread.start()

    def _send_qa_message_backend(self, question):
        try:
            # backend_logicのask_question_to_aiを呼び出す
            # chat_sessionとqa_contextを渡す
            response_message = backend_logic.ask_question_to_ai(question, self.chat_session, self.qa_context)
            self.log(response_message)
        except Exception as e:
            error_message = f"AIとの対話中にエラーが発生しました: {e}\n{traceback.format_exc()}"
            self.log(error_message)
            messagebox.showerror("エラー", "AIとの対話中にエラーが発生しました。ログを確認してください。")
        finally:
            self.stop_spinner()
            # UIの状態をUiStateManager経由で設定 (AI対話活性状態)
            self.ui_manager.set_qa_active_state()

    

    def end_qa_session(self):
        self.stop_spinner()
        
        # UIの状態をUiStateManager経由で設定 (AI対話非活性状態)
        self.ui_manager.set_qa_inactive_state()

        self.qa_context = None # コンテキストをクリア
        self.chat_session = None # チャットセッションをクリア
        self.log("AI対話セッションを終了します。")
        self.in_qa_session = False # AI対話セッション終了
        
        # UIを初期状態に戻す (on_mode_changeが通常モードのUI状態を設定します)
        self.on_mode_change()

    def execute_delete(self):
        selected_item = self.delete_combobox.get()
        if selected_item == UIDefaults.DELETE_PROMPT or selected_item == UIDefaults.NO_ITEMS_TO_DELETE:
            self.log("削除対象を選択してください。")
            return
        
        confirm = messagebox.askyesno("確認", f"本当に以下のデータを削除しますか？\n\n{selected_item}")
        if confirm:
            self.log(f"削除を実行中: {selected_item}")
            # UIの状態をUiStateManager経由で設定 (削除関連UI非活性状態)
            self.ui_manager.set_delete_ui_inactive()
            self.start_spinner()
            thread = threading.Thread(target=self._execute_delete_backend, args=(selected_item,))
            thread.start()
        else:
            self.log("削除がキャンセルされました。")

    def _execute_delete_backend(self, selected_item):
        try:
            message, _, _ = backend_logic.run_backend_process(mode=AnalysisMode.EXECUTE_DELETE, input_path=selected_item)
            self.log(message)
            self.update_delete_combobox() # 削除後にリストを更新
        except Exception as e:
            error_message = f"削除処理中にエラーが発生しました: {e}\n{traceback.format_exc()}"
            self.log(error_message)
            messagebox.showerror("エラー", "削除処理中にエラーが発生しました。ログを確認してください。")
        finally:
            self.stop_spinner()
            # UIの状態をUiStateManager経由で設定 (削除関連UI活性状態)
            self.ui_manager.set_delete_ui_active()

    def on_delete_combobox_change(self, choice):
        if choice not in [UIDefaults.DELETE_PROMPT, UIDefaults.NO_ITEMS_TO_DELETE]:
            self.delete_button.configure(state="normal")
        else:
            self.delete_button.configure(state="disabled")

if __name__ == "__main__":
    

    app = App()
    app.mainloop()