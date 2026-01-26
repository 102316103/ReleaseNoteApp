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
        self.setWindowTitle("FEP Release Manager v4.0 - Smart Search Edition")
        self.resize(1000, 750)
        
        # 使用 QSettings 來記憶設定 (Organization Name, Application Name)
        # 取得目前程式所在的資料夾路徑
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ini_path = os.path.join(base_dir, "config.ini")

        # 強制指定使用 IniFormat，並存到該路徑
        self.settings = QSettings(ini_path, QSettings.Format.IniFormat)
        self.current_folder = ""
        
        self.setup_ui()
        
        # 程式啟動時，自動讀取上次的路徑
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tab_read = QWidget()
        self.tab_update = QWidget()
        
        self.tabs.addTab(self.tab_read, "📂 1. 讀取與設定")
        self.tabs.addTab(self.tab_update, "📝 2. 搜尋與更新")
        
        self.setup_read_tab()
        self.setup_update_tab()
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==========================
    # 分頁 1: 讀取
    # ==========================
    def setup_read_tab(self):
        layout = QVBoxLayout()
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("路徑會自動記憶，不用每次都選...")
        self.path_input.setReadOnly(True)
        
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
        layout = QVBoxLayout()
        
        # --- 1. 搜尋過濾區 (Filter Area) ---
        filter_group = QFormLayout()
        
        # 搜尋條件 1 & 2
        filter_hbox = QHBoxLayout()
        self.filter_combo_1 = QComboBox()
        self.filter_combo_1.setPlaceholderText("關鍵字 A")
        self.filter_combo_1.setEditable(True) # 允許手動打字，不只下拉
        self.filter_combo_1.currentTextChanged.connect(self.apply_filters) # 當文字改變時觸發

        self.filter_combo_2 = QComboBox()
        self.filter_combo_2.setPlaceholderText("關鍵字 B")
        self.filter_combo_2.setEditable(True)
        self.filter_combo_2.currentTextChanged.connect(self.apply_filters)
        
        filter_hbox.addWidget(QLabel("搜尋條件:"))
        filter_hbox.addWidget(self.filter_combo_1)
        filter_hbox.addWidget(self.filter_combo_2)
        
        # 目標檔案下拉 (這是結果)
        self.target_file_combo = QComboBox()
        self.target_file_combo.setPlaceholderText("請先選擇條件，或直接選擇檔案...")
        self.target_file_combo.currentIndexChanged.connect(self.preview_target_file) # 選了檔案就預覽

        filter_group.addRow(filter_hbox)
        filter_group.addRow("👉 目標檔案:", self.target_file_combo)
        
        layout.addLayout(filter_group)
        
        # --- 2. 預覽與輸入區 (Splitter 用來左右拉動) ---
        splitter = QSplitter(Qt.Horizontal)
        
        # 左邊：原檔案內容預覽 (Read Only)
        self.preview_area = QTextEdit()
        self.preview_area.setPlaceholderText("這裡會顯示原檔案的內容...")
        self.preview_area.setReadOnly(True)
        self.preview_area.setStyleSheet("background-color: #f0f0f0; color: #555;") # 灰色背景代表不可編輯
        
        # 右邊：更新輸入區
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 版號輸入
        ver_layout = QHBoxLayout()
        self.ver_stage = QComboBox()
        self.ver_stage.addItems(["1", "2"])
        self.ver_stage.setFixedWidth(50)
        self.ver_seq = QLineEdit()
        self.ver_seq.setPlaceholderText("001")
        self.ver_seq.setMaxLength(5)
        self.ver_seq.setFixedWidth(80)
        self.ver_env = QComboBox()
        self.ver_env.addItems(["D", "T", "P"])
        self.ver_env.setFixedWidth(50)
        
        ver_layout.addWidget(QLabel("["))
        ver_layout.addWidget(self.ver_stage)
        ver_layout.addWidget(QLabel("] . ["))
        ver_layout.addWidget(self.ver_seq)
        ver_layout.addWidget(QLabel("] . ["))
        ver_layout.addWidget(self.ver_env)
        ver_layout.addWidget(QLabel("]"))
        ver_layout.addStretch()
        
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("輸入新的更新內容...")
        
        self.update_btn = QPushButton("執行更新")
        self.update_btn.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
        self.update_btn.clicked.connect(self.update_file_logic)
        
        right_layout.addLayout(ver_layout)
        right_layout.addWidget(self.content_input)
        right_layout.addWidget(self.update_btn)
        
        splitter.addWidget(self.preview_area)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 500]) # 設定左右初始寬度比例
        
        layout.addWidget(splitter)
        self.tab_update.setLayout(layout)

    # ==========================
    # 核心邏輯
    # ==========================
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            self.current_folder = folder
            self.path_input.setText(folder)
            
            # 儲存設定！
            self.settings.setValue("last_folder", folder)
            
            self.load_files_to_table()
            self.init_search_filters() # 初始化搜尋條件

    def load_settings(self):
        # 從設定檔讀取路徑
        saved_folder = self.settings.value("last_folder")
        if saved_folder and os.path.exists(saved_folder):
            self.current_folder = saved_folder
            self.path_input.setText(saved_folder)
            self.load_files_to_table()
            self.init_search_filters()
            print(f"諾亞記憶: 已自動載入 {saved_folder}")

    def load_files_to_table(self):
        self.file_table.setRowCount(0)
        if not self.current_folder: return
        
        try:
            files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
            for f_name in files:
                full_path = os.path.join(self.current_folder, f_name)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read(500) # 預覽只讀前500字避免卡死
                except: content = "Error"
                
                row = self.file_table.rowCount()
                self.file_table.insertRow(row)
                self.file_table.setItem(row, 0, QTableWidgetItem(f_name))
                self.file_table.setItem(row, 1, QTableWidgetItem(content))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def init_search_filters(self):
        """ 智能分析檔名，將常用的關鍵字填入搜尋下拉選單 """
        self.filter_combo_1.clear()
        self.filter_combo_2.clear()
        self.target_file_combo.clear()
        
        if not self.current_folder: return
        
        files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
        
        # 分析檔名 tokens (假設以 - 分隔)
        tokens = set()
        for f in files:
            parts = f.replace(".txt", "").split("-")
            for p in parts:
                if len(p) > 1: # 忽略太短的字
                    tokens.add(p)
        
        sorted_tokens = sorted(list(tokens))
        
        # 填入選項，並允許空值 (代表不篩選)
        self.filter_combo_1.addItem("") 
        self.filter_combo_1.addItems(sorted_tokens)
        
        self.filter_combo_2.addItem("")
        self.filter_combo_2.addItems(sorted_tokens)
        
        # 初始載入所有檔案到目標清單
        self.target_file_combo.addItems(files)

    def apply_filters(self):
        """ 當 Filter 1 或 2 改變時，動態更新 Target Combo """
        if not self.current_folder: return
        
        key1 = self.filter_combo_1.currentText().strip()
        key2 = self.filter_combo_2.currentText().strip()
        
        self.target_file_combo.blockSignals(True) # 暫停訊號，避免清空時觸發 indexChanged
        self.target_file_combo.clear()
        
        files = [f for f in os.listdir(self.current_folder) if f.endswith(".txt")]
        
        filtered_files = []
        for f in files:
            # 這裡用的是簡單的字串包含邏輯 (AND)
            if (key1 == "" or key1 in f) and (key2 == "" or key2 in f):
                filtered_files.append(f)
        
        if not filtered_files:
            self.target_file_combo.addItem("(無符合檔案)")
        else:
            self.target_file_combo.addItems(filtered_files)
            
        self.target_file_combo.blockSignals(False)
        
        # 自動選擇第一個並預覽
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

    def update_file_logic(self):
        # ... (這裡的邏輯跟上一版一樣，省略以節省篇幅) ...
        # ... 記得要用 self.target_file_combo.currentText() ...
        # ... 更新成功後，可以呼叫 self.preview_target_file() 來刷新預覽 ...
        QMessageBox.information(self, "完成", "更新功能請參考上一版代碼，記得整合進來喔！")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FepReleaseManager()
    window.show()
    sys.exit(app.exec())