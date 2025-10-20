import sys
import sqlite3
import time
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QTextEdit, QMessageBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QWidget, QAbstractItemView,
                             QCheckBox, QSplashScreen, QStyleFactory, 
                             QComboBox, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFont, QIcon, QKeySequence, QPixmap, QLinearGradient, QColor

class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or 'movies.db'
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()
    
    def create_table(self):
        """创建数据库表结构（如果不存在）"""
        query = """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            add_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            remark TEXT
        );
        """
        self.conn.execute(query)
        
        # 创建不区分大小写的唯一索引
        self.conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_name_unique 
        ON records (name COLLATE NOCASE)
        """)
        self.conn.commit()
    
    def add_record(self, name, add_date, remark=None):
        try:
            query = "INSERT INTO records (name, add_date, remark) VALUES (?, ?, ?)"
            self.conn.execute(query, (name.strip(), add_date, remark))
            self.conn.commit()
            return True, None
        except sqlite3.IntegrityError:
            # 捕获重复名称错误
            duplicate = self.find_duplicate(name)
            return False, duplicate
    
    def find_duplicate(self, name):
        """检查名称是否已存在，存在则返回记录详情，否则返回None"""
        query = "SELECT add_date, remark FROM records WHERE name = ? COLLATE NOCASE LIMIT 1"
        cursor = self.conn.execute(query, (name.strip(),))
        result = cursor.fetchone()
        return result if result else None
    
    def get_all_records(self):
        query = "SELECT id, name, add_date, remark FROM records ORDER BY add_date DESC"
        cursor = self.conn.execute(query)
        return cursor.fetchall()
    
    def search_records(self, name_query):
        query = """
        SELECT id, name, add_date, remark 
        FROM records 
        WHERE name LIKE ? COLLATE NOCASE 
        ORDER BY add_date DESC
        """
        cursor = self.conn.execute(query, (f'%{name_query}%',))
        return cursor.fetchall()
    
    def delete_records(self, record_ids):
        if not record_ids:
            return False
        
        placeholders = ', '.join('?' * len(record_ids))
        query = f"DELETE FROM records WHERE id IN ({placeholders})"
        
        try:
            self.conn.execute(query, record_ids)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"删除错误: {e}")
            return False
    
    def get_record_by_id(self, record_id):
        query = "SELECT id, name, add_date, remark FROM records WHERE id = ?"
        cursor = self.conn.execute(query, (record_id,))
        return cursor.fetchone()
    
    def update_record(self, record_id, name, add_date, remark=None):
        """更新记录"""
        try:
            query = "UPDATE records SET name = ?, add_date = ?, remark = ? WHERE id = ?"
            self.conn.execute(query, (name.strip(), add_date, remark, record_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 捕获重复名称错误
            return False
        except Exception as e:
            print(f"更新错误: {e}")
            return False

    def close(self):
        self.conn.close()

    def switch_database(self, new_db_path):
        """切换到新数据库"""
        self.close()  # 关闭当前连接
        self.db_path = new_db_path
        self.conn = sqlite3.connect(self.db_path)
        # 确保表结构存在
        self.create_table()
        
    @staticmethod
    def create_new_database(db_path):
        """创建新的空数据库"""
        try:
            # 创建数据库文件
            with open(db_path, 'w') as f:
                pass
            # 初始化数据库
            db = DatabaseManager(db_path)
            db.close()
            return True
        except Exception as e:
            print(f"创建数据库错误: {e}")
            return False

class CustomSplashScreen(QSplashScreen):
    def __init__(self):
        # 创建一张空的图片
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(500, 300)
        
        # 设计者信息
        self.designer_info = "github.com/shenmeshisanpao"
        self.app_title = "记录管理系统"
        self.loading_info = "正在初始化程序..."
        self.progress = 0  # 添加进度属性
    
    def drawContents(self, painter):
        """自定义绘制启动画面内容"""
        # 绘制背景（渐变效果）
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(59, 130, 246))  # 蓝色
        gradient.setColorAt(1, QColor(30, 58, 138))  # 深蓝色
        painter.fillRect(self.rect(), gradient)
        
        # 绘制应用标题
        painter.setPen(Qt.white)
        title_font = QFont("微软雅黑", 28, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.app_title)
        
        # 绘制加载文本 - 在标题下方
        painter.setPen(QColor(255, 255, 255, 200))  # 半透明白色
        info_font = QFont("微软雅黑", 12)
        painter.setFont(info_font)
        loading_rect = self.rect().adjusted(0, 60, 0, 0)  # 调整位置到标题下方
        painter.drawText(loading_rect, Qt.AlignHCenter | Qt.AlignCenter, self.loading_info)
        
        # 绘制进度条 - 在加载文本下方
        progress_rect = QRect(50, self.height() - 70, self.width() - 100, 20)
        painter.setPen(QColor(255, 255, 255, 100))
        painter.setBrush(QColor(255, 255, 255, 50))
        painter.drawRect(progress_rect)
        
        # 绘制进度
        if self.progress > 0:
            progress_width = int((progress_rect.width() * self.progress) / 100)
            progress_fill_rect = QRect(progress_rect.x(), progress_rect.y(), 
                                      progress_width, progress_rect.height())
            painter.setBrush(QColor(255, 255, 255, 200))
            painter.drawRect(progress_fill_rect)
        
        # 绘制进度文本
        painter.setPen(Qt.white)
        painter.drawText(progress_rect, Qt.AlignCenter, f"{self.progress}%")
        
        # 绘制设计者信息 - 在右下角
        painter.setPen(QColor(255, 255, 255, 230))
        designer_font = QFont("微软雅黑", 11, QFont.Bold)
        painter.setFont(designer_font)
        designer_rect = self.rect().adjusted(0, 0, -15, -15)
        painter.drawText(designer_rect, Qt.AlignBottom | Qt.AlignRight, self.designer_info)
        
        # 添加版权信息在左下角
        painter.setPen(QColor(255, 255, 255, 180))
        copyright_font = QFont("微软雅黑", 9)
        painter.setFont(copyright_font)
        copyright_rect = self.rect().adjusted(15, 0, 0, -15)
        painter.drawText(copyright_rect, Qt.AlignBottom | Qt.AlignLeft, "© 2025 记录管理系统 ver1.0.0")
        
        # 绘制logo
        painter.setPen(QColor(255, 255, 255, 120))
        icon_font = QFont("Arial", 48)
        painter.setFont(icon_font)
        painter.drawText(30, 80, "\U0001F4DD")  # 使用emoji图标

    def setProgress(self, value):
        """设置进度值（0-100）"""
        self.progress = value
        self.repaint()



class AddRecordDialog(QDialog):
    def __init__(self, parent=None, record_id=None):
        super().__init__(parent)
        self.record_id = record_id
        
        # 根据是否是编辑模式设置标题
        title = "编辑记录" if record_id else "单条添加"
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 名字输入
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("名字*"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入名称")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 添加时间
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("添加时间*"))
        self.date_input = QLineEdit()
        self.date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # 备注
        remark_layout = QVBoxLayout()
        remark_layout.addWidget(QLabel("备注"))
        self.remark_input = QTextEdit()
        self.remark_input.setMaximumHeight(80)
        self.remark_input.setPlaceholderText("可选备注信息...")
        remark_layout.addWidget(self.remark_input)
        layout.addLayout(remark_layout)
        
        # 按钮布局 - 添加在左、取消在右
        button_layout = QHBoxLayout()
        
        # 添加按钮在左侧
        self.submit_button = QPushButton("添加")
        self.submit_button.setShortcut(QKeySequence(Qt.Key_Return))  # 回车键快捷方式
        self.submit_button.clicked.connect(self.validate_and_accept)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.submit_button)
        
        # 弹簧使按钮居右
        button_layout.addStretch()
        
        # 取消按钮在右侧
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setShortcut(QKeySequence(Qt.Key_Escape))  # ESC键快捷方式
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def validate_and_accept(self):
        name = self.name_input.text().strip()
        date_str = self.date_input.text().strip()
        remark = self.remark_input.toPlainText().strip() or None
        
        # 验证必填项
        if not name:
            QMessageBox.warning(self, "输入错误", "名字不能为空！")
            self.name_input.setFocus()
            return
        
        if not date_str:
            QMessageBox.warning(self, "输入错误", "添加时间不能为空！")
            self.date_input.setFocus()
            return
        
        # 验证日期格式
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            QMessageBox.warning(self, "日期格式错误", "日期格式应为：YYYY-MM-DD HH:MM:SS")
            self.date_input.selectAll()
            self.date_input.setFocus()
            return
        
        self.name = name
        self.date = date_str
        self.remark = remark
        self.accept()
    
    def get_data(self):
        return self.name, self.date, self.remark

class BatchAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("快速批量添加")
        self.setMinimumSize(500, 400)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # 说明标签
        instruction_label = QLabel("请输入要添加的名字，每行一个：")
        instruction_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(instruction_label)
        
        # 文本输入区域
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("每行输入一个名字，空行将被忽略")
        self.text_input.setFont(QFont("微软雅黑", 11))
        layout.addWidget(self.text_input)
        
        # 选项区域
        options_layout = QHBoxLayout()
        
        # 添加时间选项
        time_group = QWidget()
        time_layout = QVBoxLayout(time_group)
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        time_label = QLabel("添加时间：")
        time_layout.addWidget(time_label)
        
        # 时间选择
        self.time_current = QCheckBox("使用当前时间")
        self.time_current.setChecked(True)
        self.time_current.toggled.connect(self.on_time_option_changed)
        time_layout.addWidget(self.time_current)
        
        self.time_custom = QCheckBox("使用自定义时间")
        self.time_custom.toggled.connect(self.on_time_option_changed)
        time_layout.addWidget(self.time_custom)
        
        # 自定义时间输入
        self.custom_time_input = QLineEdit()
        self.custom_time_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.custom_time_input.setEnabled(False)
        time_layout.addWidget(self.custom_time_input)
        
        options_layout.addWidget(time_group)
        
        # 备注选项
        remark_group = QWidget()
        remark_layout = QVBoxLayout(remark_group)
        remark_layout.setContentsMargins(0, 0, 0, 0)
        
        remark_label = QLabel("统一备注（可选）：")
        remark_layout.addWidget(remark_label)
        
        self.remark_input = QLineEdit()
        self.remark_input.setPlaceholderText("为所有记录添加相同的备注...")
        remark_layout.addWidget(self.remark_input)
        
        options_layout.addWidget(remark_group)
        
        layout.addLayout(options_layout)
        
        # 预览区域
        preview_label = QLabel("预览（显示前10条）：")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview_list = QTextEdit()
        self.preview_list.setMaximumHeight(100)
        self.preview_list.setReadOnly(True)
        self.preview_list.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd;")
        layout.addWidget(self.preview_list)
        
        # 连接文本变化事件
        self.text_input.textChanged.connect(self.update_preview)
        self.remark_input.textChanged.connect(self.update_preview)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 添加按钮
        self.add_button = QPushButton("批量添加")
        self.add_button.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return))
        self.add_button.clicked.connect(self.validate_and_accept)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.add_button)
        
        button_layout.addStretch()
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.setShortcut(QKeySequence(Qt.Key_Escape))
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 初始预览
        self.update_preview()
    
    def on_time_option_changed(self):
        """时间选项改变时的处理"""
        if self.sender() == self.time_current and self.time_current.isChecked():
            self.time_custom.setChecked(False)
            self.custom_time_input.setEnabled(False)
        elif self.sender() == self.time_custom and self.time_custom.isChecked():
            self.time_current.setChecked(False)
            self.custom_time_input.setEnabled(True)
            self.custom_time_input.setFocus()
        
        self.update_preview()
    
    def update_preview(self):
        """更新预览"""
        names = self.get_names_list()
        remark = self.remark_input.text().strip() or None
        
        if self.time_current.isChecked():
            time_str = "当前时间"
        else:
            time_str = self.custom_time_input.text().strip()
        
        preview_text = f"将添加 {len(names)} 条记录\n"
        preview_text += f"时间: {time_str}\n"
        preview_text += f"备注: {remark if remark else '无'}\n\n"
        
        # 显示前10个名字
        for i, name in enumerate(names[:10]):
            preview_text += f"{i+1}. {name}\n"
        
        if len(names) > 10:
            preview_text += f"... 还有 {len(names) - 10} 条记录"
        
        self.preview_list.setPlainText(preview_text)
        
        # 更新按钮状态
        self.add_button.setEnabled(len(names) > 0)
    
    def get_names_list(self):
        """获取名字列表"""
        text = self.text_input.toPlainText()
        names = []
        for line in text.split('\n'):
            line = line.strip()
            if line:  # 忽略空行
                names.append(line)
        return names
    
    def validate_and_accept(self):
        """验证并接受"""
        names = self.get_names_list()
        
        if not names:
            QMessageBox.warning(self, "输入错误", "请至少输入一个名字！")
            self.text_input.setFocus()
            return
        
        # 验证自定义时间格式
        if self.time_custom.isChecked():
            time_str = self.custom_time_input.text().strip()
            try:
                datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                QMessageBox.warning(self, "时间格式错误", "时间格式应为：YYYY-MM-DD HH:MM:SS")
                self.custom_time_input.selectAll()
                self.custom_time_input.setFocus()
                return
        
        self.accept()
    
    def get_data(self):
        """获取输入的数据"""
        names = self.get_names_list()
        remark = self.remark_input.text().strip() or None
        
        if self.time_current.isChecked():
            base_time = datetime.now()
        else:
            base_time = datetime.strptime(self.custom_time_input.text().strip(), "%Y-%m-%d %H:%M:%S")
        
        # 生成记录列表，每个记录间隔1秒（避免完全相同的时间）
        records = []
        for i, name in enumerate(names):
            # 每条记录时间递增1秒
            record_time = base_time + timedelta(seconds=i)
            time_str = record_time.strftime("%Y-%m-%d %H:%M:%S")
            records.append((name, time_str, remark))
        
        return records

class EditRecordDialog(QDialog):
    def __init__(self, parent=None, record=None):
        super().__init__(parent)
        self.record = record
        self.setWindowTitle("编辑记录")
        self.setMinimumWidth(450)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 名字输入
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("名字*"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入名称")
        if record:
            self.name_input.setText(record[1])  # name
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # 添加时间
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("添加时间*"))
        self.date_input = QLineEdit()
        if record:
            self.date_input.setText(record[2])  # add_date
        else:
            self.date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)
        
        # 备注
        remark_layout = QVBoxLayout()
        remark_layout.addWidget(QLabel("备注"))
        self.remark_input = QTextEdit()
        self.remark_input.setMaximumHeight(80)
        self.remark_input.setPlaceholderText("可选备注信息...")
        if record and record[3]:
            self.remark_input.setPlainText(record[3])  # remark
        remark_layout.addWidget(self.remark_input)
        layout.addLayout(remark_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 保存按钮
        self.save_button = QPushButton("保存")
        self.save_button.setShortcut(QKeySequence(Qt.Key_Return))
        self.save_button.clicked.connect(self.validate_and_accept)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setShortcut(QKeySequence(Qt.Key_Escape))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def validate_and_accept(self):
        name = self.name_input.text().strip()
        date_str = self.date_input.text().strip()
        remark = self.remark_input.toPlainText().strip() or None
        
        # 验证必填项
        if not name:
            QMessageBox.warning(self, "输入错误", "名字不能为空！")
            self.name_input.setFocus()
            return
        
        if not date_str:
            QMessageBox.warning(self, "输入错误", "添加时间不能为空！")
            self.date_input.setFocus()
            return
        
        # 验证日期格式
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            QMessageBox.warning(self, "日期格式错误", "日期格式应为：YYYY-MM-DD HH:MM:SS")
            self.date_input.selectAll()
            self.date_input.setFocus()
            return
        
        self.name = name
        self.date = date_str
        self.remark = remark
        self.accept()
    
    def get_data(self):
        return self.name, self.date, self.remark

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("记录管理系统")
        self.setGeometry(100, 100, 900, 700)
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager()
        
        # 创建UI
        self.create_ui()
        
        # 加载数据
        self.load_records()
        
        # 添加一个定时器用于延迟搜索
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)        
    
    def create_ui(self):
        """创建用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 搜索区域
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入名字进行搜索...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_btn)
        
        main_layout.addLayout(search_layout)
        
        # 选择操作区域
        select_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.setMaximumWidth(80)
        select_all_btn.clicked.connect(self.select_all_records)
        select_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.setMaximumWidth(80)
        deselect_all_btn.clicked.connect(self.deselect_all_records)
        select_layout.addWidget(deselect_all_btn)
        
        # 显示选中数量的标签
        self.selected_count_label = QLabel("已选中: 0 条")
        self.selected_count_label.setStyleSheet("color: #666; font-weight: bold;")
        select_layout.addWidget(self.selected_count_label)
        
        select_layout.addStretch()
        main_layout.addLayout(select_layout)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["选择", "ID", "名字", "添加日期", "备注"])
        
        # 获取水平表头
        header = self.table.horizontalHeader()
        
        # 设置列宽和调整模式
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 160)
        
        # 设置调整模式
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        # 设置表格选择行为
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        
        # 启用排序功能
        self.table.setSortingEnabled(True)
        
        main_layout.addWidget(self.table)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 添加按钮
        add_single_btn = QPushButton("单条添加")
        add_single_btn.clicked.connect(self.add_single_record)
        add_single_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(add_single_btn)
        
        batch_add_btn = QPushButton("批量添加")
        batch_add_btn.clicked.connect(self.batch_add_records)
        batch_add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(batch_add_btn)
        
        # 添加编辑按钮
        edit_btn = QPushButton("编辑记录")
        edit_btn.clicked.connect(self.edit_selected_record)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(edit_btn)
    
        button_layout.addStretch()
        
        # 删除按钮
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected_records)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(delete_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        
        # 禁止工具栏拖动
        toolbar.setMovable(False)
        
        # 数据库选择下拉菜单
        db_label = QLabel("数据库: ")
        toolbar.addWidget(db_label)
        
        self.db_combo = QComboBox()
        self.db_combo.setMinimumWidth(200)
        self.db_combo.setEditable(False)
        self.db_combo.currentTextChanged.connect(self.on_database_changed)
        toolbar.addWidget(self.db_combo)
        
        # 刷新数据库列表按钮
        refresh_db_btn = QPushButton("刷新列表")
        refresh_db_btn.setToolTip("刷新数据库文件列表")
        refresh_db_btn.clicked.connect(self.refresh_database_list)
        toolbar.addWidget(refresh_db_btn)
        
        toolbar.addSeparator()
        
        # 重新加载数据按钮
        reload_data_btn = QPushButton("重新加载数据")
        reload_data_btn.setToolTip("重新加载当前数据库中的所有记录")
        reload_data_btn.setShortcut(QKeySequence(Qt.Key_F5))  # F5快捷键
        reload_data_btn.clicked.connect(self.reload_data)
        reload_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        toolbar.addWidget(reload_data_btn)
        
        toolbar.addSeparator()
    
        # 新建数据库按钮
        new_db_btn = QPushButton("新建数据库")
        new_db_btn.clicked.connect(self.create_new_database)
        toolbar.addWidget(new_db_btn)
        
        # 打开数据库按钮
        open_db_btn = QPushButton("打开数据库")
        open_db_btn.clicked.connect(self.open_database)
        toolbar.addWidget(open_db_btn)
        
        # 初始化数据库列表
        self.refresh_database_list()

    def refresh_database_list(self):
        """刷新数据库列表"""
        # 暂时断开信号连接，避免触发切换
        self.db_combo.currentTextChanged.disconnect()
        
        self.db_combo.clear()
        
        # 获取当前目录下的所有.db文件
        current_dir = os.getcwd()
        db_files = [f for f in os.listdir(current_dir) if f.endswith('.db')]
        
        if db_files:
            self.db_combo.addItems(db_files)
            # 设置当前数据库为选中项
            current_db = os.path.basename(self.db_manager.db_path)
            index = self.db_combo.findText(current_db)
            if index >= 0:
                self.db_combo.setCurrentIndex(index)
        else:
            self.db_combo.addItem("未找到数据库文件")
        
        # 重新连接信号
        self.db_combo.currentTextChanged.connect(self.on_database_changed)

    def on_database_changed(self, db_name):
        """数据库选择改变时的处理"""
        if db_name and db_name != "未找到数据库文件":
            db_path = os.path.join(os.getcwd(), db_name)
            if os.path.exists(db_path) and db_path != self.db_manager.db_path:
                try:
                    # 先清空表格，确保没有旧数据残留
                    self.table.clearContents()
                    self.table.setRowCount(0)
                    
                    # 切换数据库
                    self.db_manager.switch_database(db_path)
                    
                    # 重新加载数据
                    self.load_records()
                    self.update_status(f"已切换到数据库: {db_name}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"切换数据库失败：{str(e)}")
                    self.refresh_database_list()  # 恢复列表
    
    def load_records(self):
        """加载并显示所有记录"""
        # 先清空表格内容
        self.table.clearContents()
        self.table.setRowCount(0)
        
        # 获取记录
        records = self.db_manager.get_all_records()
        
        # 设置行数
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            record_id, name, add_date, remark = record
            
            # 第0列：复选框
            checkbox = QCheckBox()
            checkbox.setStyleSheet("QCheckBox { margin-left: 15px; }")
            checkbox.stateChanged.connect(self.update_selected_count)
            self.table.setCellWidget(row, 0, checkbox)
            
            # 第1列：ID
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, record_id)
            self.table.setItem(row, 1, id_item)
            
            # 第2列：名字
            self.table.setItem(row, 2, QTableWidgetItem(name))
            
            # 第3列：添加日期
            date_item = QTableWidgetItem(add_date)
            try:
                date_obj = datetime.strptime(add_date, "%Y-%m-%d %H:%M:%S")
                date_item.setData(Qt.UserRole, date_obj.timestamp())
            except:
                date_item.setData(Qt.UserRole, 0)
            self.table.setItem(row, 3, date_item)
            
            # 第4列：备注
            remark_text = remark if remark else ""
            self.table.setItem(row, 4, QTableWidgetItem(remark_text))
            
            # 设置ID列不可编辑
            self.table.item(row, 1).setFlags(self.table.item(row, 1).flags() & ~Qt.ItemIsEditable)
        
        # 默认按添加日期降序排序（最新的在前）
        self.table.sortItems(3, Qt.DescendingOrder)
        
        # 更新状态栏和选中计数
        self.update_status(f"共 {len(records)} 条记录")
        self.update_selected_count()
    
    def search_records(self, query):
        """搜索记录"""
        # 先清空表格内容
        self.table.clearContents()
        self.table.setRowCount(0)
        
        if query.strip():
            records = self.db_manager.search_records(query)
            self.update_status(f"搜索到 {len(records)} 条记录")
        else:
            records = self.db_manager.get_all_records()
            self.update_status(f"共 {len(records)} 条记录")
        
        # 设置行数
        self.table.setRowCount(len(records))
        
        for row, record in enumerate(records):
            record_id, name, add_date, remark = record
            
            # 第0列：复选框
            checkbox = QCheckBox()
            checkbox.setStyleSheet("QCheckBox { margin-left: 15px; }")
            checkbox.stateChanged.connect(self.update_selected_count)
            self.table.setCellWidget(row, 0, checkbox)
            
            # 第1列：ID
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, record_id)
            self.table.setItem(row, 1, id_item)
            
            # 第2列：名字
            self.table.setItem(row, 2, QTableWidgetItem(name))
            
            # 第3列：添加日期
            date_item = QTableWidgetItem(add_date)
            try:
                date_obj = datetime.strptime(add_date, "%Y-%m-%d %H:%M:%S")
                date_item.setData(Qt.UserRole, date_obj.timestamp())
            except:
                date_item.setData(Qt.UserRole, 0)
            self.table.setItem(row, 3, date_item)
            
            # 第4列：备注
            remark_text = remark if remark else ""
            self.table.setItem(row, 4, QTableWidgetItem(remark_text))
            
            # 设置ID列不可编辑
            self.table.item(row, 1).setFlags(self.table.item(row, 1).flags() & ~Qt.ItemIsEditable)
        
        # 默认按添加日期降序排序
        self.table.sortItems(3, Qt.DescendingOrder)
        
        self.update_selected_count()

    
    def edit_selected_record(self):
        """编辑选中的记录"""
        # 获取当前选中的行
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "提示", "请先选择要编辑的记录！")
            return
        
        # 获取记录ID
        id_item = self.table.item(current_row, 1)
        if not id_item:
            QMessageBox.warning(self, "错误", "无法获取记录ID！")
            return
        
        record_id = int(id_item.text())
        
        # 获取记录详情
        record = self.db_manager.get_record_by_id(record_id)
        if not record:
            QMessageBox.warning(self, "错误", "记录不存在！")
            return
        
        # 创建编辑对话框
        dialog = EditRecordDialog(self, record)
        if dialog.exec_() == QDialog.Accepted:
            name, date, remark = dialog.get_data()
            success = self.db_manager.update_record(record_id, name, date, remark)
            
            if success:
                QMessageBox.information(self, "成功", "记录更新成功！")
                self.load_records()
            else:
                QMessageBox.critical(self, "错误", "更新记录失败！可能是名称重复。")

    def get_selected_record_ids(self):
        """获取选中的记录ID列表"""
        selected_ids = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                id_item = self.table.item(row, 1)
                if id_item:
                    selected_ids.append(int(id_item.text()))
        return selected_ids
    
    def get_selected_count(self):
        """获取选中的记录数量"""
        count = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                count += 1
        return count
    
    def update_selected_count(self):
        """更新选中数量显示"""
        count = self.get_selected_count()
        self.selected_count_label.setText(f"已选中: {count} 条")
    
    def select_all_records(self):
        """全选所有记录"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all_records(self):
        """取消全选所有记录"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def delete_selected_records(self):
        """删除选中的记录"""
        selected_ids = self.get_selected_record_ids()
        
        if not selected_ids:
            QMessageBox.information(self, "提示", "请先选择要删除的记录！")
            return
        
        # 确认删除
        count = len(selected_ids)
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {count} 条记录吗？\n\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db_manager.delete_records(selected_ids)
            if success:
                QMessageBox.information(self, "成功", f"已删除 {count} 条记录！")
                self.load_records()
            else:
                QMessageBox.critical(self, "错误", "删除记录时发生错误！")
    
    def add_single_record(self):
        """添加单条记录"""
        dialog = AddRecordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, date, remark = dialog.get_data()
            success, duplicate = self.db_manager.add_record(name, date, remark)
            
            if success:
                QMessageBox.information(self, "成功", "记录添加成功！")
                self.load_records()
            else:
                if duplicate:
                    existing_date, existing_remark = duplicate
                    msg = f"名字 '{name}' 已存在！\n\n"
                    msg += f"现有记录信息：\n"
                    msg += f"添加时间：{existing_date}\n"
                    msg += f"备注：{existing_remark if existing_remark else '无'}"
                    QMessageBox.warning(self, "重复记录", msg)
                else:
                    QMessageBox.critical(self, "错误", "添加记录失败！")
    
    def batch_add_records(self):
        """批量添加记录"""
        dialog = BatchAddDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            records = dialog.get_data()
            
            success_count = 0
            failed_records = []
            
            for name, date, remark in records:
                success, duplicate = self.db_manager.add_record(name, date, remark)
                if success:
                    success_count += 1
                else:
                    failed_records.append(name)
            
            # 显示结果
            if success_count > 0:
                self.load_records()
            
            if failed_records:
                failed_names = "、".join(failed_records[:999])
                if len(failed_records) > 999:
                    failed_names += f" 等{len(failed_records)}个"
                
                msg = f"成功添加 {success_count} 条记录\n"
                msg += f"失败 {len(failed_records)} 条记录（重复名字）：{failed_names}"
                QMessageBox.warning(self, "批量添加结果", msg)
            else:
                QMessageBox.information(self, "成功", f"批量添加成功！共添加 {success_count} 条记录。")
    
    def on_search_changed(self, text):
        """搜索框文本变化时触发"""

        # 重置定时器，300毫秒后执行搜索
        self.search_timer.stop()
        self.search_timer.start(100)
    
    def perform_search(self):
        """执行搜索"""
        query = self.search_input.text()
        self.search_records(query)
    
    def clear_search(self):
        """清空搜索"""
        self.search_input.clear()
        self.load_records()
    
    def create_new_database(self):
        """创建新数据库"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "创建新数据库", "", "数据库文件 (*.db)"
        )
        
        if file_path:
            if DatabaseManager.create_new_database(file_path):
                self.db_manager.switch_database(file_path)
                self.refresh_database_list()
                self.load_records()
                QMessageBox.information(self, "成功", f"数据库 '{os.path.basename(file_path)}' 创建成功！")
            else:
                QMessageBox.critical(self, "错误", "创建数据库失败！")
    
    def open_database(self):
        """打开数据库"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开数据库", "", "数据库文件 (*.db)"
        )
        
        if file_path:
            try:
                self.db_manager.switch_database(file_path)
                self.refresh_database_list()
                self.load_records()
                QMessageBox.information(self, "成功", f"数据库 '{os.path.basename(file_path)}' 打开成功！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"打开数据库失败：{str(e)}")
    
    def update_status(self, message):
        """更新状态栏"""
        self.statusBar().showMessage(message)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.db_manager.close()
        event.accept()
        
    def reload_data(self):
        """重新加载数据"""
        try:
            # 记录当前选中的记录ID（如果有的话）
            current_row = self.table.currentRow()
            selected_id = None
            if current_row >= 0:
                id_item = self.table.item(current_row, 1)
                if id_item:
                    selected_id = int(id_item.text())
            
            # 清空搜索框
            self.search_input.clear()
            
            # 重新加载所有记录
            self.load_records()
            
            # 尝试恢复之前选中的记录
            if selected_id is not None:
                self.restore_selection(selected_id)
            
            # 显示成功消息
            record_count = self.table.rowCount()
            self.update_status(f"数据重新加载完成 - 共 {record_count} 条记录")
            
            # 在状态栏显示临时消息
            self.statusBar().showMessage("✓ 数据重新加载完成", 3000)  # 3秒后消失
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重新加载数据失败：{str(e)}")
            self.update_status("数据加载失败")

    def restore_selection(self, target_id):
        """恢复指定ID的记录选中状态"""
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 1)
            if id_item and int(id_item.text()) == target_id:
                self.table.selectRow(row)
                self.table.scrollToItem(id_item)
                break
        

# 主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置美观的样式
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 设置应用程序图标
    if os.path.exists("logo.ico"):
        app.setWindowIcon(QIcon("logo.ico"))
            
    # 设置全局字体
    font = QFont("微软雅黑", 10)
    app.setFont(font)
    
    # 创建启动画面
    splash = CustomSplashScreen()
    splash.show()
    app.processEvents()
    
    # 初始化过程的各个步骤
    initialization_steps = [
        "正在加载系统组件...",
        "正在初始化数据库连接...",
        "正在准备用户界面...",
        "正在加载记录数据...",
        "即将完成..."
    ]
    
    # 创建主窗口但不显示
    window = MainWindow()
    
    # 显示实际的初始化进度
    total_steps = len(initialization_steps)
    for i, step_message in enumerate(initialization_steps):
        # 计算进度百分比
        progress = int((i / total_steps) * 100)
        
        # 更新启动画面上的消息和进度
        splash.loading_info = step_message
        splash.setProgress(progress)
        
        # 处理事件，确保界面更新
        app.processEvents()
        
        # 执行实际的初始化任务...
        
        # 如果有必要，添加很小的延迟确保用户能看到进度
        time.sleep(0.1)
    
    # 设置100%进度
    splash.setProgress(100)
    splash.loading_info = "加载完成！"
    app.processEvents()
    time.sleep(0.2)  # 短暂显示完成状态
    
    # 关闭启动画面并显示主窗口
    splash.finish(window)
    window.show()
    
    sys.exit(app.exec_())