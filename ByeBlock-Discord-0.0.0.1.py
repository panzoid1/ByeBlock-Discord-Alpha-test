import sys
import os
import subprocess
import requests
import time
from PyQt5.QtCore import (
    QUrl, QSettings, QThread, pyqtSignal, Qt
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QAction, QMenu, 
    QMenuBar, QWidget, QDialog, QDialogButtonBox, QVBoxLayout, 
    QLabel, QSpinBox, QLineEdit, QComboBox, QCheckBox, 
    QPushButton, QTabWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtGui import QPalette, QColor, QDesktopServices
from PyQt5.QtNetwork import QNetworkProxy
import pyqtgraph as pg
from pyqtgraph import PlotWidget
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QIcon

class PingWorker(QThread):
    ping_signal = pyqtSignal(float)

    def __init__(self, get_proxy_info):
        super().__init__()
        self.get_proxy_info = get_proxy_info
        self.running = False

    def run(self):
        while self.running:
            ping = self.ping_site()
            self.ping_signal.emit(ping)
            time.sleep(1)

    def ping_site(self):
        proxy_info = self.get_proxy_info()
        if not proxy_info:
            return 0
        
        proxies = {
            "http": f"http://{proxy_info['host']}:{proxy_info['port']}",
            "https": f"http://{proxy_info['host']}:{proxy_info['port']}"
        }

        try:
            start_time = time.time()
            response = requests.get("http://discord.com/app", proxies=proxies, timeout=5)
            response.raise_for_status()
            return (time.time() - start_time) * 1000
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return 0

class ProxyPingGraph(QWidget):
    def __init__(self, get_proxy_info):
        super().__init__()
        self.get_proxy_info = get_proxy_info

        self.graphWidget = PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.graphWidget)
        self.setLayout(layout)

        self.graphWidget.setBackground('#202020')
        self.graphWidget.showGrid(x=False, y=False)
        self.graphWidget.setTitle("Proxy Ping", color="w", size="15pt")

        self.x = list(range(50))
        self.y = [0] * 50

        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pg.mkPen(color="r", width=3))

        self.worker = PingWorker(self.get_proxy_info)
        self.worker.ping_signal.connect(self.update_plot_data)

    def start_ping(self):
        self.worker.running = True
        self.worker.start()

    def stop_ping(self):
        self.worker.running = False
        self.worker.quit()
        self.worker.wait()

    def update_plot_data(self, ping):
        self.y = self.y[1:] + [ping]
        self.data_line.setData(self.x, self.y)

class DiscordBrowser(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.settings = QSettings("Settings.ini", QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)
        self.app = app

        # Set window icon
        self.setWindowIcon(QIcon("app.ico"))

        if self.settings.value("proxy/connect_automatically", False, type=bool):
            self.apply_proxy_from_settings()

        self.initUI()
        self.microphone_enabled = self.settings.value("Access/Microphone", False, type=bool)
        self.camera_enabled = self.settings.value("Access/Camera", False, type=bool)
        self.screen_share_enabled = self.settings.value("Access/Screen", False, type=bool)
        self.check_access()

    def initUI(self):
        self.setWindowTitle('ByeBlock-Discord-0.0.0.1')
        
        # Load saved window size
        width = self.settings.value("window/width", 800, type=int)
        height = self.settings.value("window/height", 600, type=int)
        self.resize(width, height)

        self.view = QWebEngineView()
        self.view.setPage(WebEnginePage(self))
        self.view.load(QUrl('https://discord.com/app'))

        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        # Developer tools shortcut
        dev_tools_action = QAction(self)
        dev_tools_action.setShortcut(QKeySequence("Alt+F12"))
        dev_tools_action.triggered.connect(self.show_dev_tools)
        self.addAction(dev_tools_action)

        self.setCentralWidget(self.view)
        self.set_dark_theme()
        self.create_menu()
        self.show()

    def show_dev_tools(self):
        self.view.page().setDevToolsPage(QWebEnginePage())  # Create a DevTools page if none exists
        self.view.page().devToolsPage().show()


    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.app.setPalette(palette)

    def create_menu(self):
        menubar = self.menuBar()
        main_menu = menubar.addMenu('Main')
        settings_menu = menubar.addMenu('Settings')
        help_menu = menubar.addMenu('Help')

        reload_action = QAction('Reload', self)
        reload_action.triggered.connect(self.view.reload)
        main_menu.addAction(reload_action)

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        main_menu.addAction(exit_action)

        resolution_action = QAction('Resolution', self)
        resolution_action.triggered.connect(self.show_resolution_dialog)
        settings_menu.addAction(resolution_action)

        proxy_action = QAction('Proxy Add', self)
        proxy_action.triggered.connect(self.show_proxy_dialog)
        settings_menu.addAction(proxy_action)

        all_action = QAction('All Settings', self)
        all_action.triggered.connect(self.open_all_settings)
        settings_menu.addAction(all_action)

        telegram_action = QAction('Telegram Support', self)
        telegram_action.triggered.connect(self.open_telegram)
        help_menu.addAction(telegram_action)

    def open_telegram(self):
        QDesktopServices.openUrl(QUrl("https://t.me/Mazkalawzey"))

    def open_all_settings(self):
        self.proxy_app = ProxyApp()
        self.proxy_app.show()

    def show_proxy_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Proxy Settings")
        layout = QVBoxLayout()

        name_label = QLabel("Proxy Name:")
        layout.addWidget(name_label)
        name_edit = QLineEdit()
        layout.addWidget(name_edit)

        proxy_type_label = QLabel("Proxy Type:")
        layout.addWidget(proxy_type_label)
        proxy_type_combobox = QComboBox()
        proxy_type_combobox.addItems(["HTTP", "SOCKS5"])
        layout.addWidget(proxy_type_combobox)

        proxy_host_label = QLabel("Proxy Host:")
        layout.addWidget(proxy_host_label)
        proxy_host_edit = QLineEdit()
        layout.addWidget(proxy_host_edit)

        proxy_port_label = QLabel("Proxy Port:")
        layout.addWidget(proxy_port_label)
        proxy_port_spinbox = QSpinBox()
        proxy_port_spinbox.setMaximum(65535)
        layout.addWidget(proxy_port_spinbox)

        auto_connect_checkbox = QCheckBox("Connect Automatically")
        layout.addWidget(auto_connect_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            proxy_name = name_edit.text()
            proxy_type = proxy_type_combobox.currentText()
            proxy_host = proxy_host_edit.text()
            proxy_port = proxy_port_spinbox.value()
            connect_automatically = auto_connect_checkbox.isChecked()

            self.settings.setValue("proxy/name", proxy_name)
            self.settings.setValue("proxy/type", proxy_type)
            self.settings.setValue("proxy/host", proxy_host)
            self.settings.setValue("proxy/port", proxy_port)
            self.settings.setValue("proxy/connect_automatically", connect_automatically)

            self.apply_proxy(proxy_type, proxy_host, proxy_port)

    def apply_proxy(self, proxy_type, host, port):
        proxy = QNetworkProxy()
        if proxy_type == "HTTP":
            proxy.setType(QNetworkProxy.HttpProxy)
        elif proxy_type == "SOCKS5":
            proxy.setType(QNetworkProxy.Socks5Proxy)

        proxy.setHostName(host)
        proxy.setPort(port)
        QNetworkProxy.setApplicationProxy(proxy)

    def apply_proxy_from_settings(self):
        proxy_type = self.settings.value("proxy/type", "")
        proxy_host = self.settings.value("proxy/host", "")
        proxy_port = self.settings.value("proxy/port", 0, type=int)

        if proxy_type and proxy_host and proxy_port:
            self.apply_proxy(proxy_type, proxy_host, proxy_port)

    def show_resolution_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Resolution Settings")
        layout = QVBoxLayout()

        width_label = QLabel("Width:")
        layout.addWidget(width_label)
        width_spinbox = QSpinBox()
        width_spinbox.setMinimum(640)
        width_spinbox.setMaximum(1920)
        width_spinbox.setValue(self.width())
        layout.addWidget(width_spinbox)

        height_label = QLabel("Height:")
        layout.addWidget(height_label)
        height_spinbox = QSpinBox()
        height_spinbox.setMinimum(480)
        height_spinbox.setMaximum(1080)
        height_spinbox.setValue(self.height())
        layout.addWidget(height_spinbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            new_width = width_spinbox.value()
            new_height = height_spinbox.value()
            self.resize(new_width, new_height)
            self.settings.setValue("window/width", new_width)
            self.settings.setValue("window/height", new_height)

    def restore_window_size(self):
        width = self.settings.value("window/width", 800, type=int)
        height = self.settings.value("window/height", 600, type=int)
        self.resize(width, height)

    def check_access(self):
        if not self.microphone_enabled:
            QMessageBox.warning(self, "Access Denied", "Microphone access is denied.")
        if not self.camera_enabled:
            QMessageBox.warning(self, "Access Denied", "Camera access is denied.")
        if not self.screen_share_enabled:
            QMessageBox.warning(self, "Access Denied", "Screen sharing access is denied.")

class WebEnginePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, _type, is_main_frame):
        if url.toString().startswith("https://discord.com"):
            return super().acceptNavigationRequest(url, _type, is_main_frame)
        else:
            return False

class ProxyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("All Settings - ByeBlock-Discord 0.0.0.1")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #0F110D; color: White;")
        
        self.settings = QSettings("Settings.ini", QSettings.IniFormat)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                background-color: #000000;  /* Цвет фона вкладок */
            }
            QTabBar::tab {
                background: #707070;  /* Цвет фона каждой вкладки */
                color: white;         /* Цвет текста вкладки */
                padding: 5px;       /* Отступы внутри вкладки */
            }
            QTabBar::tab:selected {
                background: #909090; /* Цвет фона активной вкладки */
            }
        """)
        self.setCentralWidget(self.tabs)

        self.proxy_tab = QWidget()
        self.proxy_layout = QVBoxLayout()

        self.ping_graph = ProxyPingGraph(self.get_proxy_info)
        self.proxy_layout.addWidget(self.ping_graph)

        self.proxy_combobox = QComboBox()
        self.load_proxies()
        self.proxy_combobox.currentTextChanged.connect(self.save_settings)
        self.proxy_layout.addWidget(self.proxy_combobox)

        self.proxy_status_label = QLabel("Proxy Status:\nPing: 0ms")
        self.proxy_layout.addWidget(self.proxy_status_label)

        self.start_button = QPushButton("Start Graph")
        self.start_button.clicked.connect(self.ping_graph.start_ping)
        self.proxy_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Graph")
        self.stop_button.clicked.connect(self.ping_graph.stop_ping)
        self.proxy_layout.addWidget(self.stop_button)

        self.host_input = QLineEdit(self)
        self.host_input.setPlaceholderText("Enter Proxy Host")
        self.proxy_layout.addWidget(self.host_input)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Enter Proxy Port")
        self.proxy_layout.addWidget(self.port_input)

        self.add_proxy_button = QPushButton("Add Proxy")
        self.add_proxy_button.clicked.connect(self.add_proxy)
        self.proxy_layout.addWidget(self.add_proxy_button)

        self.proxy_tab.setLayout(self.proxy_layout)
        self.tabs.addTab(self.proxy_tab, "Proxy Settings")

        self.access_tab = QWidget()
        self.access_layout = QVBoxLayout()

        self.mic_checkbox = QCheckBox("Microphone Access")
        self.mic_checkbox.setChecked(self.settings.value("Access/Microphone", False, type=bool))
        self.mic_checkbox.stateChanged.connect(self.save_settings)
        self.access_layout.addWidget(self.mic_checkbox)

        self.camera_checkbox = QCheckBox("Camera Access")
        self.camera_checkbox.setChecked(self.settings.value("Access/Camera", False, type=bool))
        self.camera_checkbox.stateChanged.connect(self.save_settings)
        self.access_layout.addWidget(self.camera_checkbox)

        self.screen_checkbox = QCheckBox("Share Screen Access")
        self.screen_checkbox.setChecked(self.settings.value("Access/Screen", False, type=bool))
        self.screen_checkbox.stateChanged.connect(self.save_settings)
        self.access_layout.addWidget(self.screen_checkbox)

        self.access_tab.setLayout(self.access_layout)
        self.tabs.addTab(self.access_tab, "Access Settings")

        self.connect_tab = QWidget()
        self.connect_layout = QVBoxLayout()

        self.connect_label = QLabel("Choose the way to connect to Discord:")
        self.connect_layout.addWidget(self.connect_label)

        self.connection_type = QComboBox()
        self.connection_type.addItems(["Proxy", "VPN"])
        self.connection_type.setCurrentText(self.settings.value("Connection/Type", "Proxy"))
        self.connection_type.currentTextChanged.connect(self.save_settings)
        self.connect_layout.addWidget(self.connection_type)

        self.connect_tab.setLayout(self.connect_layout)
        self.tabs.addTab(self.connect_tab, "Connection Settings")

        self.update_proxy_details()

    def load_proxies(self):
        self.proxy_combobox.clear()
        for key in self.settings.childKeys():
            if key.startswith("Proxy/") and "Host" in key:
                proxy_server = key.split('/')[1]
                self.proxy_combobox.addItem(proxy_server)

    def add_proxy(self):
        host = self.host_input.text()
        port = self.port_input.text()

        if not host or not port.isdigit():
            QMessageBox.warning(self, "Input Error", "Please enter valid Host and Port.")
            return
        
        proxy_key = f"Proxy/{host}"
        self.settings.setValue(f"{proxy_key}/Host", host)
        self.settings.setValue(f"{proxy_key}/Port", int(port))
        self.settings.sync()
        
        self.host_input.clear()
        self.port_input.clear()

        self.load_proxies()
        QMessageBox.information(self, "Success", "Proxy added successfully.")

    def save_settings(self):
        self.settings.setValue("Proxy/Server", self.proxy_combobox.currentText())
        self.settings.setValue("Access/Microphone", self.mic_checkbox.isChecked())
        self.settings.setValue("Access/Camera", self.camera_checkbox.isChecked())
        self.settings.setValue("Access/Screen", self.screen_checkbox.isChecked())
        self.settings.setValue("Connection/Type", self.connection_type.currentText())
        self.settings.sync()
        self.update_proxy_details()

    def update_proxy_details(self):
        proxy_server = self.proxy_combobox.currentText()
        host = self.settings.value(f"Proxy/{proxy_server}/Host", "None")
        port = self.settings.value(f"Proxy/{proxy_server}/Port", "None")
        self.proxy_status_label.setText(f"Proxy Status:\nHost: {host}, Port: {port}")

    def get_proxy_info(self):
        proxy_server = self.proxy_combobox.currentText()
        host = self.settings.value(f"Proxy/{proxy_server}/Host", "None")
        port = self.settings.value(f"Proxy/{proxy_server}/Port", "None")

        if host != "None" and port != "None":
            return {"host": host, "port": int(port)}
        return None

def main():
    app = QApplication(sys.argv)
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0F110D"))
    palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(palette)

    discord_browser = DiscordBrowser(app)
    discord_browser.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
