import sys
import os
import subprocess

from PyQt5.QtCore import QUrl, QSettings
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QAction,
    QMenu,
    QMenuBar,
    QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QSpinBox, QLineEdit, QComboBox, QCheckBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtGui import QPalette, QColor, QDesktopServices  # Import QDesktopServices
from PyQt5.QtNetwork import QNetworkProxy

class DiscordBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load Settings.ini file
        self.settings = QSettings("Settings.ini", QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)  # Only use Settings.ini

        # Apply proxy settings on startup if 'connect_automatically' is enabled
        if self.settings.value("proxy/connect_automatically", False, type=bool):
            self.apply_proxy_from_settings()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('ByeBlock-Discord-0.0.0.1')

        # Create WebEngineView
        self.view = QWebEngineView()
        self.view.setPage(WebEnginePage(self))

        # Load Discord
        self.view.load(QUrl('https://discord.com/app'))

        # Enable media playback
        settings = self.view.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)

        # Set central widget
        self.setCentralWidget(self.view)

        # Set dark theme for the application
        self.set_dark_theme()

        # Create menu
        self.create_menu()

        # Restore window size from settings or Settings.ini
        self.restore_window_size()

        self.show()

    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        app.setPalette(palette)

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
        all_action.triggered.connect(self.open_all_settings_script)
        settings_menu.addAction(all_action)

        # Add Help action to open Telegram
        telegram_action = QAction('Telegram Support', self)
        telegram_action.triggered.connect(self.open_telegram)
        help_menu.addAction(telegram_action)

    def open_telegram(self):
        QDesktopServices.openUrl(QUrl("https://t.me/Mazkalawzey"))  # Open the Telegram link

    def open_all_settings_script(self):
        script_path = os.path.join(os.path.dirname(__file__), 'Settings', 'all-settings.py')
        if os.path.exists(script_path):
            subprocess.Popen(['python', script_path])
        else:
            QMessageBox.warning(self, "Error", "all-settings.py not found in /Settings/")

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

            # Save proxy settings in Settings.ini
            self.settings.setValue("proxy/name", proxy_name)
            self.settings.setValue("proxy/type", proxy_type)
            self.settings.setValue("proxy/host", proxy_host)
            self.settings.setValue("proxy/port", proxy_port)
            self.settings.setValue("proxy/connect_automatically", connect_automatically)

            # Apply proxy settings
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
            width = width_spinbox.value()
            height = height_spinbox.value()
            self.resize(width, height)
            self.settings.setValue("window_width", width)
            self.settings.setValue("window_height", height)

    def restore_window_size(self):
        width = self.settings.value("window_width", 800, type=int)
        height = self.settings.value("window_height", 600, type=int)
        self.resize(width, height)

    def closeEvent(self, event):
        self.settings.setValue("window_width", self.width())
        self.settings.setValue("window_height", self.height())
        super().closeEvent(event)

class WebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

    def onFeaturePermissionRequested(self, url, feature):
        if feature in (
            QWebEnginePage.MediaAudioCapture, 
            QWebEnginePage.MediaVideoCapture,
            QWebEnginePage.MediaAudioVideoCapture,
            QWebEnginePage.DesktopVideoCapture
        ):
            print("Granting permission for media capture.")
            self.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    browser = DiscordBrowser()
    sys.exit(app.exec_())
