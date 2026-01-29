#包版 pyinstaller --noconsole --onefile --name="FEP Release Manager" ReleaseNoteApp.py

import sys
import os
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QFormLayout, QLabel, QLineEdit, QTextEdit, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QMessageBox, QTabWidget, QFileDialog, QComboBox, QHeaderView,
                               QSplitter)
from PySide6.QtCore import Qt, QSettings

class FepReleaseManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FEP Release Manager v5.3 (Portable)")
        self.resize(1000, 750)
        
        # --- [修正] 決定正確的根目錄 ---
        if getattr(sys, 'frozen', False):
            # 情況 A: 如果是被打包成的 EXE
            # sys.executable 會給出 EXE 檔案的完整路徑
            # 我們取它的 dirname，就是 EXE 旁邊的資料夾
            application_path = os.path.dirname(sys.executable)
        else:
            # 情況 B: 如果是普通的 Python 腳本
            # 就用原本的 __file__ 邏輯
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        # 組合出 config.ini 的路徑 (放在 EXE 旁邊)
        ini_path = os.path.join(application_path, "config.ini")
        
        # 設定 QSettings 使用這個 .ini 檔
        self.settings = QSettings(ini_path, QSettings.Format.IniFormat)
        
        # 測試一下 (開發時可以在終端機看到路徑對不對)
        print(f"提示: 設定檔將存放在 -> {ini_path}")

        self.current_folder = ""
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tab_read = QWidget()
        self.tab_update = QWidget()
        
        self.tabs.addTab(self.tab_read, "📂 讀取與設定")
        self.tabs.addTab(self.tab_update, "📝 搜尋與更新")
        
        self.setup_read_tab()   #建立讀取設定分頁功能
        self.setup_update_tab() #建立更新分頁功能
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==========================
    # 分頁 1: 讀取
    # ==========================
    def setup_read_tab(self):
        layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("可直接貼上路徑並按 Enter，或點擊右側按鈕...路徑會自動記憶，不用每次都選...")
        self.path_input.setReadOnly(False)
        
        # 當你在框框裡按 Enter，就會呼叫 on_path_entered
        self.path_input.returnPressed.connect(self.on_path_entered)
        
        self.browse_btn = QPushButton("選擇路徑")
        self.browse_btn.clicked.connect(self.select_folder)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_btn)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(2)
        self.file_table.setHorizontalHeaderLabels(["檔案名稱", "完整內容"])
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.file_table.setColumnWidth(0, 250)
        self.file_table.setWordWrap(True)
        self.file_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        layout.addLayout(path_layout)
        layout.addWidget(self.file_table)
        self.tab_read.setLayout(layout)

    # ==========================
    # 分頁 2: 更新 (搜尋 + 預覽)
    # ==========================
    def setup_update_tab(self):

        # 改用 VBox，所有東西垂直排列
        layout = QVBoxLayout()
        
        # --- 1. 搜尋與選檔區 ---
        filter_group = QFormLayout()
        
        filter_hbox = QHBoxLayout()
        self.filter_combo_1 = QComboBox()
        self.filter_combo_1.setPlaceholderText("關鍵字 A")
        self.filter_combo_1.setEditable(True)
        self.filter_combo_1.currentTextChanged.connect(self.on_filter_1_changed)

        self.filter_combo_2 = QComboBox()
        self.filter_combo_2.setPlaceholderText("關鍵字 B")
        self.filter_combo_2.setEditable(True)
        self.filter_combo_2.currentTextChanged.connect(self.apply_final_filter)
        
        filter_hbox.addWidget(QLabel("搜尋條件(可不選):"))
        filter_hbox.addWidget(self.filter_combo_1)
        filter_hbox.addWidget(self.filter_combo_2)
        
        self.target_file_combo = QComboBox()
        self.target_file_combo.setPlaceholderText("請選擇目標檔案...")
        self.target_file_combo.currentIndexChanged.connect(self.preview_target_file)

        filter_group.addRow(filter_hbox)
        filter_group.addRow("👉 目標檔案:", self.target_file_combo)
        
        layout.addLayout(filter_group)
        
        # --- 2. [修改點] 原檔案內容預覽 (移到這裡，變成長條狀) ---
        layout.addWidget(QLabel("原始檔案內容 (Original Content):"))
        self.preview_area = QTextEdit()
        self.preview_area.setPlaceholderText("選擇檔案後，這裡會顯示原本的內容...")
        self.preview_area.setReadOnly(True)
        self.preview_area.setStyleSheet("background-color: #f0f0f0; color: #333;")
        self.preview_area.setMaximumHeight(150) # 限制高度，不要佔滿整個畫面
        layout.addWidget(self.preview_area)
        
        # --- 3. [修改點] 版號輸入區 (依照你的嚴格要求) ---
        # 格式: 階段(1/2) . 流水號 . 環境(D/T/P)
        ver_group = QHBoxLayout()
        
        self.ver_stage = QComboBox()
        self.ver_stage.addItems(["1", "2"]) # 階段別
        self.ver_stage.setFixedWidth(50)
        
        self.ver_seq = QLineEdit()
        self.ver_seq.setMaxLength(10)
        self.ver_seq.setFixedWidth(80)
        
        self.ver_env = QComboBox()
        self.ver_env.addItems(["D", "T", "P"]) # 環境別
        self.ver_env.setFixedWidth(50)
        
        ver_group.addWidget(QLabel("新版號設定:"))
        ver_group.addWidget(QLabel("    [階段別]"))
        ver_group.addWidget(self.ver_stage)
        ver_group.addWidget(QLabel("    [流水號]"))
        ver_group.addWidget(self.ver_seq)
        ver_group.addWidget(QLabel("    [環境別]"))
        ver_group.addWidget(self.ver_env)
        ver_group.addWidget(QLabel(""))
        ver_group.addStretch() # 把東西推到左邊
        
        layout.addLayout(ver_group)
        
        # --- 4. 更新內容輸入區 ---
        layout.addWidget(QLabel("本次更新內容:"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("請輸入新的 Release Note 內容...")
        layout.addWidget(self.content_input)
        
        # --- 5. 按鈕 ---
        self.update_btn = QPushButton("執行更新 (Update)")
        self.update_btn.setStyleSheet("background-color: #0078d7; color: white; font-weight: bold; padding: 10px;")
        self.update_btn.clicked.connect(self.update_file_logic)
        layout.addWidget(self.update_btn)
        
        self.tab_update.setLayout(layout)

    # ==========================
    # 核心邏輯
    # ==========================
    def on_path_entered(self):
        # 1. 取得使用者輸入的文字，並去除頭尾空白
        raw_path = self.path_input.text().strip()
        
        if not raw_path:
            return # 空的就不理你

        # 2. [防呆機制] 檢查路徑是否存在，且必須是「資料夾」
        if os.path.exists(raw_path) and os.path.isdir(raw_path):
            # 驗證通過！更新全域變數
            self.current_folder = raw_path
            
            # 這裡可以順便存入設定，這樣下次打開還是這個路徑
            self.settings.setValue("last_folder", raw_path)
            
            # 呼叫核心載入邏輯
            self.load_files_to_table()
            self.init_search_filters()
            
            # 給點回饋，讓使用者知道成功了 (可以在狀態列顯示，這裡用 Print 代替)
            print(f"認證: 路徑已切換至 {raw_path}")
            
        else:
            # 路徑錯誤，並還原
            QMessageBox.warning(self, "路徑錯誤", 
                                f"找不到這個路徑：\n{raw_path}\n\n請確認你沒打錯字，且這必須是一個「資料夾」！")
            
            # 如果之前有有效的路徑，幫你切換回去 (貼心吧？)
            if self.current_folder:
                self.path_input.setText(self.current_folder)
            else:
                self.path_input.clear()
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            self.path_input.setText(folder)
            self.on_path_entered()
            

    def load_settings(self):
        # 從設定檔讀取路徑
        saved_folder = self.settings.value("last_folder")
        if saved_folder and os.path.exists(saved_folder):
            self.current_folder = saved_folder
            self.path_input.setText(saved_folder)
            self.load_files_to_table()
            self.init_search_filters()
            print(f"記憶: 已自動載入 {saved_folder}")

    def load_files_to_table(self):
        self.file_table.setRowCount(0)
        if not self.current_folder: return
        
        try:
            files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
            for f_name in files:
                full_path = os.path.join(self.current_folder, f_name)
                
                content = ""
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # 過濾掉 # 開頭的行
                        filtered_lines = [line for line in lines if not line.strip().startswith("#")]
                        content = "".join(filtered_lines).strip()
                except: content = "(讀取失敗)"
                
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)
                
                # [修改點] 這裡！切掉副檔名再顯示
                # f_name 是 "abc.txt"，display_name 變成 "abc"
                display_name = os.path.splitext(f_name)[0] 
                
                self.file_table.setItem(row, 0, QTableWidgetItem(display_name))
                
                item = QTableWidgetItem(content)
                item.setToolTip(content[:200] + "...")
                self.file_table.setItem(row, 1, item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def init_search_filters(self):
        """ 初始化 Filter 1 (加入去副檔名邏輯) """
        self.filter_combo_1.blockSignals(True)
        self.filter_combo_1.clear()
        self.filter_combo_2.clear()
        self.target_file_combo.clear()
        
        if not self.current_folder: return
        
        files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
        tokens_1 = set()
        
        for f in files:
            parts = f.split("-")
            if len(parts) > 1:
                # [修改點] 這裡！針對 parts[1] 也要做淨化
                # 範例 A: fep-batch.txt      -> parts[1]="batch.txt" -> clean="batch"
                # 範例 B: fep-batch-task.txt -> parts[1]="batch"     -> clean="batch"
                raw_part_1 = parts[1]
                clean_part_1 = raw_part_1.split(".")[0]
                
                tokens_1.add(clean_part_1)
        
        sorted_tokens = sorted(list(tokens_1))
        self.filter_combo_1.addItem("") 
        self.filter_combo_1.addItems(sorted_tokens)
        
        self.filter_combo_1.blockSignals(False)
        # 觸發連動
        self.on_filter_1_changed(self.filter_combo_1.currentText())

    # ==========================================
    #  Logic: 級聯搜尋 (Cascading Search)
    # ==========================================

    def init_search_filters(self):
        """ 初始化 Filter 1 (加入去副檔名邏輯) """
        self.filter_combo_1.blockSignals(True)
        self.filter_combo_1.clear()
        self.filter_combo_2.clear()
        self.target_file_combo.clear()
        
        if not self.current_folder: return
        
        files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
        tokens_1 = set()
        
        for f in files:
            parts = f.split("-")
            if len(parts) > 1:
                # [修改點] 這裡！針對 parts[1] 也要做淨化
                # 範例 A: fep-batch.txt      -> parts[1]="batch.txt" -> clean="batch"
                # 範例 B: fep-batch-task.txt -> parts[1]="batch"     -> clean="batch"
                raw_part_1 = parts[1]
                clean_part_1 = raw_part_1.split(".")[0]
                
                tokens_1.add(clean_part_1)
        
        sorted_tokens = sorted(list(tokens_1))
        self.filter_combo_1.addItem("") 
        self.filter_combo_1.addItems(sorted_tokens)
        
        self.filter_combo_1.blockSignals(False)
        # 觸發連動
        self.on_filter_1_changed(self.filter_combo_1.currentText())

    def on_filter_1_changed(self, text):
        """ Filter 1 變動 -> 更新 Filter 2 (比對邏輯更新) """
        key1 = text.strip() # 這是選單裡已經乾淨的 "batch"
        
        self.filter_combo_2.blockSignals(True)
        self.filter_combo_2.clear()
        
        if not self.current_folder: return
        
        files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
        tokens_2 = set()
        
        for f in files:
            parts = f.split("-")
            if len(parts) > 1: # 至少要有 part 1
                
                # [修改點] 檔案裡的 part 1 也要洗乾淨才能跟 key1 比對
                raw_part_1 = parts[1]
                clean_part_1 = raw_part_1.split(".")[0]
                
                if key1 == "" or clean_part_1 == key1:
                    # 如果條件一吻合，且還有第三段，才收集 Filter 2
                    if len(parts) > 2:
                        raw_part_2 = parts[2]
                        clean_part_2 = raw_part_2.split(".")[0] # 之前教你的
                        tokens_2.add(clean_part_2)

        sorted_tokens_2 = sorted(list(tokens_2))
        self.filter_combo_2.addItem("")
        self.filter_combo_2.addItems(sorted_tokens_2)
        
        self.filter_combo_2.blockSignals(False)
        self.apply_final_filter()

    def apply_final_filter(self):
        """ 最終篩選 (比對邏輯更新) """
        key1 = self.filter_combo_1.currentText().strip()
        key2 = self.filter_combo_2.currentText().strip()
        
        self.target_file_combo.blockSignals(True)
        self.target_file_combo.clear()
        
        if not self.current_folder: return

        files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
        filtered_files = []
        
        for f in files:
            parts = f.split("-")
            
            # 只要長度 > 1，我們就有機會比對 Filter 1
            if len(parts) > 1:
                # 處理 Part 1
                raw_part_1 = parts[1]
                clean_part_1 = raw_part_1.split(".")[0]
                
                # 處理 Part 2 (如果有的話)
                clean_part_2 = ""
                if len(parts) > 2:
                    clean_part_2 = parts[2].split(".")[0]
                
                # 開始比對
                match_1 = (key1 == "" or clean_part_1 == key1)
                
                # 注意：如果使用者選了 key2，但檔案根本沒有 part 2 (例如 fep-batch.txt)，那就不算符合
                match_2 = True
                if key2 != "":
                    if clean_part_2 == "": 
                        match_2 = False # 沒東西可以比，失敗
                    else:
                        match_2 = (clean_part_2 == key2)
                
                if match_1 and match_2:
                    filtered_files.append(f)
        
        if not filtered_files:
            self.target_file_combo.addItem("(無符合檔案)")
        else:
            # 先塞一個「全選」選項在最上面
            batch_option = f"=== 💥 更新清單中所有 {len(filtered_files)} 個檔案 ==="
            self.target_file_combo.addItem(batch_option)
            
            # 然後再把個別檔案加進去
            self.target_file_combo.addItems(filtered_files)
            
            self.target_file_combo.setCurrentIndex(0) # 預設選這個「全選」選項
            
        self.target_file_combo.blockSignals(False)
        
        if filtered_files:
            self.preview_target_file()
        else:
            self.preview_area.clear()

    def preview_target_file(self):
        """ 讀取選定的檔案並顯示在預覽區 """
        filename = self.target_file_combo.currentText()
        if not filename or filename == "(無符合檔案)": 
            self.preview_area.clear()
            return
            
        full_path = os.path.join(self.current_folder, filename)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.preview_area.setText(content)
        except Exception:
            self.preview_area.setText("(無法讀取檔案內容)")
    
    def process_single_file(self, filename, version_str, new_content):
        """ 
        負責處理單一檔案的讀取、保留 Header、寫入。
        回傳: True (成功) / False (失敗)
        """
        full_path = os.path.join(self.current_folder, filename)
        
        try:
            # 1. 搶救 Header (# 開頭的行)
            header_lines = []
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("#"):
                            header_lines.append(line)
            
            # 2. 準備內容
            final_text_list = header_lines[:] 
            if final_text_list and not final_text_list[-1].endswith("\n"):
                final_text_list.append("\n")
            
            final_text_list.append(f"\n{version_str}\n")
            final_text_list.append(new_content + "\n")
            
            # 3. 寫入
            with open(full_path, "w", encoding="utf-8") as f:
                f.writelines(final_text_list)
            
            return True, "" # 成功，無錯誤訊息
            
        except Exception as e:
            return False, str(e) # 失敗，回傳錯誤原因

    def update_file_logic(self):
        # --- 1. 檢查基本環境 ---
        if not self.current_folder:
            QMessageBox.warning(self, "你累了嗎？", "請先到第一頁選擇資料夾！")
            return

        selection = self.target_file_combo.currentText()
        if not selection or selection.startswith("(無"):
            QMessageBox.warning(self, "目標錯誤", "請選擇一個有效的目標檔案！")
            return

        # --- 2. 檢查並組裝版號 ---
        # 格式: [階段].[流水號].[環境]
        stage = self.ver_stage.currentText() # 1 或 2
        seq = self.ver_seq.text().strip()    # 使用者填寫的流水號
        env = self.ver_env.currentText()     # D, T, P

        if not seq:
            QMessageBox.warning(self, "格式錯誤", "流水號 (Sequence) 不能空白！\n你是要發布空號嗎？")
            self.ver_seq.setFocus() # 把游標移過去提醒你
            return
            
        # 這裡可以加強邏輯：確保流水號是數字 (選做)
        # if not seq.isdigit(): ...

        # 組合後的字串，例如: "1.001.D"
        full_version_str = f"[{stage}].[{seq}].[{env}]"

        # --- 3. 檢查內容 ---
        new_content = self.content_input.toPlainText().strip()
        if not new_content:
            QMessageBox.warning(self, "缺漏", "更新內容沒填！你是要發布無字天書嗎？")
            return
        
        target_files_list = []
        # 檢查是否選中了我們剛剛加的那個 "=== ... (BATCH) ==="
        if selection.startswith("==="):
            # [核彈模式] 抓出下拉選單裡除了第一個(全選)以外的所有檔案
            count = self.target_file_combo.count()
            # 從 index 1 開始抓到最後
            target_files_list = [self.target_file_combo.itemText(i) for i in range(1, count)]
            
            # [絕對防呆] 跳出恐怖的警告視窗
            reply = QMessageBox.question(self, "高風險操作確認", 
                                         f"⚠️ 警告！你即將同時修改 {len(target_files_list)} 個檔案！\n\n"
                                         f"這些檔案的舊內容(除了#開頭)將會全部消失！\n"
                                         f"版號: {full_version_str}\n\n"
                                         "要繼續嗎？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return # 怕了就取消
        else:
            # [單體模式] 就只有選中的那一個
            target_files_list = [selection]

        # --- 4. 執行核心 I/O (讀取舊Header -> 寫入新檔) ---
        success_count = 0
        error_logs = []
        
        for fname in target_files_list:
            is_ok, err_msg = self.process_single_file(fname, full_version_str, new_content)
            if is_ok:
                success_count += 1
            else:
                error_logs.append(f"{fname}: {err_msg}")
        

        # --- 5. 收尾工作 ---
        if len(error_logs) == 0:
            QMessageBox.information(self, "大成功", 
                                    f"任務完成！\n成功更新 {success_count} 個檔案。")
        else:
            err_str = "\n".join(error_logs)
            QMessageBox.warning(self, "部分失敗", 
                                f"成功: {success_count}\n失敗: {len(error_logs)}\n\n錯誤詳情:\n{err_str}")
        
        # 重新整理介面，讓使用者看到最新的狀態
        self.load_files_to_table()      # 更新第一頁表格
        self.content_input.clear()      # 清空輸入框，避免重複送出
        self.preview_target_file()      # 更新當前的預覽區 (你會看到新的內容出現)
        self.ver_seq.clear()            # 清空流水號
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FepReleaseManager()
    window.show()
    sys.exit(app.exec())
