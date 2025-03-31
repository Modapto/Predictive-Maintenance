import sys
import json
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QTextEdit, QHBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
from algorithm.algorithm import genetic_algorithm, GENOME_LENGTH, POPULATION_SIZE, GENERATIONS, p_c_min, p_c_max, p_m_min, p_m_max
from algorithm.algorithm import calculate_info, t_begin, t_end
from algorithm.algorithm import plot_replacement_times  # Import the function to display the graph
from algorithm.algorithm import plot_replacement_times_both_plans

class GeneticAlgorithmWorker(QThread):
    result_signal = pyqtSignal(object, float, dict, dict)
    error_signal = pyqtSignal(str)

    def __init__(self, C_s, C_d, m):
        super().__init__()
        self.C_s = C_s
        self.C_d = C_d
        self.m = m

    def run(self):
        try:
            best_individual, best_fitness = genetic_algorithm(GENOME_LENGTH, self.m, POPULATION_SIZE, GENERATIONS, p_c_min, p_c_max, p_m_min, p_m_max, self.C_s, self.C_d)
            individual_plan, estimate_plan = calculate_info(best_individual)
            print("individual_plan: ", individual_plan)
            print("estimate_plan: ", estimate_plan)
            self.result_signal.emit(best_individual, best_fitness, individual_plan, estimate_plan)
        except Exception as e:
            self.error_signal.emit(str(e))

class GeneticAlgorithmGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("GUI")
        self.setGeometry(100, 100, 600, 700)
        self.setStyleSheet("background-color: #0f0f0f;")

        layout = QVBoxLayout()

        # Input section
        self.cs_label = QLabel("C_s (Setup Cost):")
        self.cs_entry = QLineEdit()
        self.cs_entry.setStyleSheet("background-color: #ffffff; color: black; padding: 5px;")
        layout.addWidget(self.cs_label)
        layout.addWidget(self.cs_entry)

        self.cd_label = QLabel("C_d (Downtime Cost Rate):")
        self.cd_entry = QLineEdit()
        self.cd_entry.setStyleSheet("background-color: #ffffff; color: black; padding: 5px;")
        layout.addWidget(self.cd_label)
        layout.addWidget(self.cd_entry)

        self.m_label = QLabel("m (Number of Repairmen):")
        self.m_entry = QLineEdit()
        self.m_entry.setStyleSheet("background-color: #ffffff; color: black; padding: 5px;")
        layout.addWidget(self.m_label)
        layout.addWidget(self.m_entry)

        # Run button
        self.run_button = QPushButton("Run Algorithm")
        self.run_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        self.run_button.clicked.connect(self.run_genetic_algorithm)
        layout.addWidget(self.run_button)

        self.loading_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)

        self.result_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("color: #333; font-weight: bold;")
        layout.addWidget(self.result_label)

        # Component buttons section
        self.component_buttons_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.component_buttons_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setStyleSheet("background-color: #e0e0e0; padding: 5px;")
        layout.addWidget(self.scroll_area)

        # Details display
        self.details_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet("background-color: #ffebcd; color: black; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.details_label)

        # Graph button
        self.plot_button = QPushButton("Show Graph")
        self.plot_button.setEnabled(False)  # Disable until we get results
        self.plot_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 5px;")
        self.plot_button.clicked.connect(self.show_graph)
        layout.addWidget(self.plot_button)

        self.setLayout(layout)

    def run_genetic_algorithm(self):
        try:
            C_s = float(self.cs_entry.text())
            C_d = float(self.cd_entry.text())
            m = int(self.m_entry.text())

            self.loading_label.setText("Running... Please wait")
            self.worker = GeneticAlgorithmWorker(C_s, C_d, m)
            self.worker.result_signal.connect(self.display_result)
            self.worker.error_signal.connect(self.display_error)
            self.worker.start()
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Please enter valid numerical values for C_s, C_d, and m")

    def display_result(self, best_individual, best_fitness, individual_plan, estimate_plan):
        self.loading_label.setText("")
        self.result_label.setText(f"Maintenance Time Window: from {t_begin} to {t_end} (hours)\nCost Saving: {best_fitness}")
        self.result_label.setStyleSheet("color: white; font-weight: bold; padding: 5px;")


        for i in reversed(range(self.component_buttons_layout.count())):
            self.component_buttons_layout.itemAt(i).widget().setParent(None)
        
        self.component_data = estimate_plan  # Store component data for use
        for component in estimate_plan.keys():
            button = QPushButton(component)
            button.setStyleSheet("background-color: #ff5722; color: white; font-weight: bold; padding: 5px;")
            button.clicked.connect(lambda checked, comp=component: self.show_component_details(comp))
            self.component_buttons_layout.addWidget(button)

        self.plot_button.setEnabled(True)  # Enable the button to display the graph
        self.individual_plan = individual_plan
        self.estimate_plan = estimate_plan  # Store the variable

    def display_error(self, error_message):
        self.loading_label.setText("")
        QMessageBox.critical(self, "Error", error_message)

    def show_graph(self):
        if hasattr(self, 'individual_plan') and hasattr(self, 'estimate_plan'):
            plot_replacement_times_both_plans(self.individual_plan, self.estimate_plan)  # Call the function to display the graph

    def show_component_details(self, component):
        details = self.component_data.get(component, {})
        duration = details.get("duration", [])
        replacement_time = details.get("replacement_time", [])
        self.details_label.setText(f"{component}\nDuration: {duration}\nReplacement Time: {replacement_time}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GeneticAlgorithmGUI()
    gui.show()
    sys.exit(app.exec())
