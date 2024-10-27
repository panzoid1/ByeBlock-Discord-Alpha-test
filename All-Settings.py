import sys
import requests
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QComboBox, QPushButton, QCheckBox, QGroupBox, QLineEdit, QMessageBox, QTabWidget
)
from PyQt5.QtCore import QThread, pyqtSignal, QSettings, Qt  # Correctly imported Qt
from PyQt5.QtGui import QColor, QPalette
import pyqtgraph as pg
from pyqtgraph import PlotWidget


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
            time.sleep(1)  # Update every second

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
            response = requests.get("http://gimnazium25.ru/", proxies=proxies, timeout=5)
            response.raise_for_status()
            return (time.time() - start_time) * 1000  # Convert to milliseconds
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return 0


class ProxyPingGraph(QWidget):
    def __init__(self, get_proxy_info):
        super().__init__()
        self.get_proxy_info = get_proxy_info

        # Create a graph widget
        self.graphWidget = PlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.graphWidget)
        self.setLayout(layout)

        # Graph settings
        self.graphWidget.setBackground('#202020')  # Dark background
        self.graphWidget.showGrid(x=False, y=False)
        self.graphWidget.setTitle("Proxy Ping", color="w", size="15pt")

        # Initialize data
        self.x = list(range(50))  # Display the last 50 points
        self.y = [0] * 50  # Initial ping values

        # Plot line
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pg.mkPen(color="r", width=3))

        # Worker for handling pinging in a separate thread
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
        self.y = self.y[1:] + [ping]  # Shift data and add new value
        self.data_line.setData(self.x, self.y)  # Update plot line


class ProxyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy & VPN Settings")
        self.setGeometry(200, 200, 600, 400)
        self.setStyleSheet("background-color: #0F110D; color: white;")
        
        # Load settings
        self.settings = QSettings("Settings.ini", QSettings.IniFormat)

        # Create Tab Widget for organizing settings
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create Proxy Settings Tab
        self.proxy_tab = QWidget()
        self.proxy_layout = QVBoxLayout()

        # Adding the graph to the Proxy settings
        self.ping_graph = ProxyPingGraph(self.get_proxy_info)
        self.proxy_layout.addWidget(self.ping_graph)

        # Proxy dropdown for server selection
        self.proxy_combobox = QComboBox()
        self.load_proxies()  # Load proxies from settings
        self.proxy_combobox.currentTextChanged.connect(self.save_settings)
        self.proxy_layout.addWidget(self.proxy_combobox)

        # Proxy Status display
        self.proxy_status_label = QLabel("Proxy Status:\nPing: 0ms")
        self.proxy_layout.addWidget(self.proxy_status_label)

        # Buttons for controlling graph
        self.start_button = QPushButton("Start Graph")
        self.start_button.clicked.connect(self.ping_graph.start_ping)
        self.proxy_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Graph")
        self.stop_button.clicked.connect(self.ping_graph.stop_ping)
        self.proxy_layout.addWidget(self.stop_button)

        # Button to add proxy
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

        # Create Access Tab
        self.access_tab = QWidget()
        self.access_layout = QVBoxLayout()

        # Access checkboxes
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

        # Create Connect Tab
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

        # Update proxy details label
        self.update_proxy_details()

    def load_proxies(self):
        # Load proxies from settings into the combo box
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
        
        # Save the new proxy to settings
        proxy_key = f"Proxy/{host}"
        self.settings.setValue(f"{proxy_key}/Host", host)
        self.settings.setValue(f"{proxy_key}/Port", int(port))
        self.settings.sync()
        
        # Clear input fields
        self.host_input.clear()
        self.port_input.clear()

        # Reload proxies
        self.load_proxies()
        QMessageBox.information(self, "Success", "Proxy added successfully.")

    def save_settings(self):
        # Save settings to Settings.ini
        self.settings.setValue("Proxy/Server", self.proxy_combobox.currentText())
        self.settings.setValue("Access/Microphone", self.mic_checkbox.isChecked())
        self.settings.setValue("Access/Camera", self.camera_checkbox.isChecked())
        self.settings.setValue("Access/Screen", self.screen_checkbox.isChecked())
        self.settings.setValue("Connection/Type", self.connection_type.currentText())
        self.settings.sync()

        # Update proxy details when saving settings
        self.update_proxy_details()

    def update_proxy_details(self):
        # Retrieve proxy host and port from settings
        proxy_server = self.proxy_combobox.currentText()
        host = self.settings.value(f"Proxy/{proxy_server}/Host", "None")
        port = self.settings.value(f"Proxy/{proxy_server}/Port", "None")
        self.proxy_status_label.setText(f"Proxy Status:\nHost: {host}, Port: {port}")

    def get_proxy_info(self):
        # Return the selected proxy info as a dictionary
        proxy_server = self.proxy_combobox.currentText()
        host = self.settings.value(f"Proxy/{proxy_server}/Host", "None")
        port = self.settings.value(f"Proxy/{proxy_server}/Port", "None")

        if host != "None" and port != "None":
            return {"host": host, "port": int(port)}
        return None


def main():
    app = QApplication(sys.argv)
    
    # Set the app's color palette to a dark theme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0F110D"))
    palette.setColor(QPalette.WindowText, Qt.white)  # Ensure Qt is defined
    app.setPalette(palette)
    
    window = ProxyApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
