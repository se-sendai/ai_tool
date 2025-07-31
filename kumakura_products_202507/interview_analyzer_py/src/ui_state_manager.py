import customtkinter
from tkinterdnd2 import DND_FILES
from constants import AnalysisMode

class UiStateManager:
    """
    GUIアプリケーションのUI要素の活性・非活性、表示・非表示を一元的に管理するクラス。
    Appクラスのインスタンスを受け取り、そのUI要素の状態を操作します。
    """
    def __init__(self, app_instance):
        """
        UiStateManagerのコンストラクタ。
        Appクラスのインスタンスを受け取り、UI要素への参照を保持します。

        Args:
            app_instance: Appクラスのインスタンス。
        """
        self.app = app_instance

        # Appクラスから主要なUI要素への参照を取得
        # これらの要素はAppクラスの__init__メソッドで初期化されていることを前提とします。
        self.interview_radio = app_instance.interview_radio
        self.daily_report_radio = app_instance.daily_report_radio
        self.qa_radio = app_instance.qa_radio

        self.path_frame = app_instance.path_frame
        self.path_entry = app_instance.path_entry
        self.file_button = app_instance.file_button
        self.folder_button = app_instance.folder_button

        self.run_button = app_instance.run_button
        self.qa_chat_frame = app_instance.qa_chat_frame
        self.qa_input_entry = app_instance.qa_input_entry
        self.qa_send_button = app_instance.qa_send_button
        self.qa_end_button = app_instance.qa_end_button

        self.delete_frame = app_instance.delete_frame
        self.delete_combobox = app_instance.delete_combobox
        self.delete_button = app_instance.delete_button
        self.update_delete_list_button = app_instance.update_delete_list_button

        self.result_file_button = app_instance.result_file_button
        self.result_folder_button = app_instance.result_folder_button

        # DND登録状態を追跡するフラグ (app_gui.pyのis_path_entry_dnd_registeredと連携)
        self.is_path_entry_dnd_registered = app_instance.is_path_entry_dnd_registered

    def set_mode_normal_state(self):
        """
        「面談分析」または「日報分析」モード（通常モード）のUI状態を設定します。
        ファイル/フォルダ選択UIを活性化し、AI対話・削除関連UIを非表示にします。
        """
        print("DEBUG: UiStateManager.set_mode_normal_state called.")
        # ファイル/フォルダ選択フレームを表示
        self.path_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # ドラッグ＆ドロップのバインディングを再設定（安全に）
        if not self.is_path_entry_dnd_registered:
            self.path_entry.drop_target_register(DND_FILES)
            self.app.path_entry.dnd_bind('<<Drop>>', self.app.handle_drop) # Appインスタンスのhandle_dropをバインド
            self.is_path_entry_dnd_registered = True
            self.app.is_path_entry_dnd_registered = True # Appインスタンスのフラグも更新

        # ファイル/フォルダ選択関連UIを活性化
        self.path_entry.configure(state="normal")
        self.file_button.configure(state="normal")
        self.folder_button.configure(state="normal")

        # 実行ボタンのテキストとコマンドを元に戻す
        self.run_button.configure(text="分析実行", command=self.app.start_analysis)

        # AI対話・削除関連UIを非表示
        self.qa_chat_frame.grid_forget()
        self.delete_frame.grid_forget()

        # 結果表示ボタンを非表示に
        self.result_file_button.grid_remove()
        self.result_folder_button.grid_remove()

        # モード選択ラジオボタンを活性化
        self.interview_radio.configure(state="normal")
        self.daily_report_radio.configure(state="normal")
        self.qa_radio.configure(state="normal")

    def set_mode_qa_initial_state(self):
        """
        「AI対話」モードの初期UI状態を設定します。
        ファイル/フォルダ選択UIを非表示にし、AI対話・削除関連UIを表示しますが、
        入力欄などは初期状態では非活性にします。
        """
        print("DEBUG: UiStateManager.set_mode_qa_initial_state called.")
        # ファイル/フォルダ選択フレームを非表示
        self.path_frame.grid_forget()

        # ドラッグ＆ドロップのバインディングを解除（安全に）
        if self.is_path_entry_dnd_registered:
            self.path_entry.drop_target_unregister()
            self.is_path_entry_dnd_registered = False
            self.app.is_path_entry_dnd_registered = False # Appインスタンスのフラグも更新

        # 実行ボタンのテキストとコマンドを変更し、活性化する
        self.run_button.configure(text="AI対話開始", command=self.app.start_qa_session_flow, state="normal")

        # AI対話・削除関連UIを表示
        self.qa_chat_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.delete_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # AI対話関連UIは初期状態では非活性
        self.qa_input_entry.configure(state="disabled")
        self.qa_send_button.configure(state="disabled")
        self.qa_end_button.configure(state="disabled")

        # 削除関連UIも初期状態では非活性
        self.delete_combobox.configure(state="normal")
        self.delete_button.configure(state="disabled")
        self.update_delete_list_button.configure(state="normal")

        # 結果表示ボタンを非表示に
        self.result_file_button.grid_remove()
        self.result_folder_button.grid_remove()

        # モード選択ラジオボタンを活性化
        self.interview_radio.configure(state="normal")
        self.daily_report_radio.configure(state="normal")
        self.qa_radio.configure(state="normal")

    def set_qa_active_state(self):
        """
        AI対話セッションが開始され、ユーザーが質問を入力できる状態を設定します。
        AI対話関連UIを活性化し、その他のUIを非活性化します。
        """
        print("DEBUG: UiStateManager.set_qa_active_state called.")
        # AI対話関連UIを活性化
        self.qa_input_entry.configure(state="normal")
        self.qa_send_button.configure(state="normal")
        self.qa_end_button.configure(state="normal")
        self.qa_input_entry.focus_set() # 入力フィールドにフォーカス

        # 削除関連UIを活性化
        self.delete_combobox.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.update_delete_list_button.configure(state="disabled")

        # その他のUIを無効化
        self.interview_radio.configure(state="disabled")
        self.daily_report_radio.configure(state="disabled")
        self.qa_radio.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        self.file_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")
        self.run_button.configure(state="disabled") # AI対話開始ボタンは再度押せないように無効化

    def set_qa_inactive_state(self):
        """
        AI対話セッションが終了した状態を設定します。
        AI対話関連UIと削除関連UIを非活性化し、通常モードのUI状態に戻します。
        """
        print("DEBUG: UiStateManager.set_qa_inactive_state called.")
        # AI対話関連UIを無効化
        self.qa_input_entry.configure(state="disabled")
        self.qa_send_button.configure(state="disabled")
        self.qa_end_button.configure(state="disabled")

        # 削除関連UIをあなたの要求通りに設定
        self.delete_combobox.configure(state="normal")
        self.delete_button.configure(state="disabled")
        self.update_delete_list_button.configure(state="normal")

        # AI対話開始ボタンを活性化
        self.run_button.configure(state="normal")

    def set_processing_state(self):
        """
        処理実行中（スピナー表示中）のUI状態を設定します。
        全ての主要なUI要素を一時的に無効化します。
        """
        print("DEBUG: UiStateManager.set_processing_state called.")
        # モード選択ラジオボタンを無効化
        self.interview_radio.configure(state="disabled")
        self.daily_report_radio.configure(state="disabled")
        self.qa_radio.configure(state="disabled")

        # ファイル/フォルダ選択関連を無効化
        self.path_entry.configure(state="disabled")
        self.file_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")

        # 実行ボタンを無効化
        self.run_button.configure(state="disabled")

        # AI対話関連UIを無効化
        self.qa_input_entry.configure(state="disabled")
        self.qa_send_button.configure(state="disabled")
        self.qa_end_button.configure(state="disabled")

        # 削除関連UIを無効化
        self.delete_combobox.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.update_delete_list_button.configure(state="disabled")

    def set_idle_state(self):
        """
        処理完了後（スピナー停止後）のUI状態を設定します。
        現在のモードに応じて、適切なUI要素を活性化します。
        """
        print("DEBUG: UiStateManager.set_idle_state called.")
        selected_mode = self.app.mode_variable.get() # Appインスタンスから現在のモードを取得

        if selected_mode == AnalysisMode.QA:
            # AI対話モードの場合、AI対話関連UIと削除関連UIを活性化
            if self.app.in_qa_session:
                self.set_qa_active_state()
            else:
                self.set_mode_qa_initial_state()
        else:
            # 通常モードの場合、ファイル/フォルダ選択関連UIとモード選択ラジオボタンを活性化
            self.set_mode_normal_state()

    def set_delete_ui_active(self):
        """
        削除関連UIを活性化します。
        """
        print("DEBUG: UiStateManager.set_delete_ui_active called.")
        self.delete_combobox.configure(state="normal")
        self.delete_button.configure(state="normal")
        self.update_delete_list_button.configure(state="normal")

    def set_delete_ui_inactive(self):
        """
        削除関連UIを非活性化します。
        """
        print("DEBUG: UiStateManager.set_delete_ui_inactive called.")
        self.delete_combobox.configure(state="disabled")
        self.delete_button.configure(state="disabled")
        self.update_delete_list_button.configure(state="disabled")
