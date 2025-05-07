import sys
import csv
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTableWidget, QTableWidgetItem, QMessageBox, 
                            QSpinBox, QDoubleSpinBox, QDialog, QFormLayout,
                            QComboBox, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

class AddStudentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Student")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        # Student basic info
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.attendance_input = QSpinBox()
        self.attendance_input.setRange(0, 365)

        layout.addRow("Name:", self.name_input)
        layout.addRow("ID:", self.id_input)
        layout.addRow("Attendance:", self.attendance_input)

        # Subjects and grades
        self.subjects_layout = QVBoxLayout()
        self.subjects = []
        self.add_subject_button = QPushButton("Add Subject")
        self.add_subject_button.clicked.connect(self.add_subject_field)
        
        layout.addRow(self.subjects_layout)
        layout.addRow(self.add_subject_button)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)
        self.add_subject_field()

    def add_subject_field(self):
        subject_widget = QWidget()
        subject_layout = QHBoxLayout()
        
        subject_name = QLineEdit()
        subject_grade = QDoubleSpinBox()
        subject_grade.setRange(0, 100)
        subject_grade.setDecimals(2)
        
        subject_layout.addWidget(subject_name)
        subject_layout.addWidget(subject_grade)
        
        subject_widget.setLayout(subject_layout)
        self.subjects_layout.addWidget(subject_widget)
        self.subjects.append((subject_name, subject_grade))

    def get_student_data(self):
        grades = {}
        for subject_name, subject_grade in self.subjects:
            name = subject_name.text().strip()
            if name:
                grades[name] = subject_grade.value()

        return {
            "name": self.name_input.text().strip(),
            "id": self.id_input.text().strip(),
            "grades": grades,
            "attendance": self.attendance_input.value()
        }

class StudentManagementSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Management System")
        self.setMinimumSize(1000, 600)
        self.setup_ui()
        self.load_students()

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create header
        header = QLabel("Student Management System")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Create buttons
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Add Student")
        self.search_button = QPushButton("Search")
        self.delete_button = QPushButton("Delete")
        self.modify_button = QPushButton("Modify")
        
        self.add_button.clicked.connect(self.add_student)
        self.search_button.clicked.connect(self.search_student)
        self.delete_button.clicked.connect(self.delete_student)
        self.modify_button.clicked.connect(self.modify_student)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.modify_button)
        
        layout.addLayout(button_layout)

        # Create search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by ID or Name...")
        self.search_input.textChanged.connect(self.filter_students)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Name", "ID", "Subjects", "Grades", "Attendance", 
            "Attendance Status", "Average", "Final Grade"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)

    def load_students(self):
        try:
            with open("students.csv", mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                self.table.setRowCount(0)
                
                for row in reader:
                    self.add_row_to_table(row)
        except FileNotFoundError:
            pass

    def add_row_to_table(self, row_data):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        for col, data in enumerate(row_data):
            item = QTableWidgetItem(str(data))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row_position, col, item)

    def add_student(self):
        dialog = AddStudentDialog(self)
        if dialog.exec():
            student_data = dialog.get_student_data()
            
            # Validate data
            if not student_data["name"] or not student_data["id"]:
                QMessageBox.warning(self, "Error", "Name and ID are required!")
                return
            
            if not student_data["grades"]:
                QMessageBox.warning(self, "Error", "At least one subject is required!")
                return
            
            # Calculate average and grade
            avg = sum(student_data["grades"].values()) / len(student_data["grades"])
            grade = self.assign_grade(avg)
            attendance_status = self.get_attendance_status(student_data["attendance"])
            
            # Save to CSV
            self.save_student_to_csv(student_data, avg, grade, attendance_status)
            
            # Update table
            row_data = [
                student_data["name"],
                student_data["id"],
                ", ".join(student_data["grades"].keys()),
                ", ".join(str(g) for g in student_data["grades"].values()),
                str(student_data["attendance"]),
                attendance_status,
                f"{avg:.2f}",
                grade
            ]
            self.add_row_to_table(row_data)
            
            QMessageBox.information(self, "Success", "Student added successfully!")

    def search_student(self):
        search_text = self.search_input.text().strip().lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().lower()
            student_id = self.table.item(row, 1).text().lower()
            
            if search_text in name or search_text in student_id:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def filter_students(self):
        self.search_student()

    def delete_student(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            student_id = self.table.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete student {student_id}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.table.removeRow(current_row)
                self.save_table_to_csv()
                QMessageBox.information(self, "Success", "Student deleted successfully!")

    def modify_student(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            dialog = AddStudentDialog(self)
            
            # Fill current data
            dialog.name_input.setText(self.table.item(current_row, 0).text())
            dialog.id_input.setText(self.table.item(current_row, 1).text())
            dialog.attendance_input.setValue(int(self.table.item(current_row, 4).text()))
            
            # Clear existing subject fields
            for i in reversed(range(dialog.subjects_layout.count())):
                dialog.subjects_layout.itemAt(i).widget().deleteLater()
            dialog.subjects.clear()
            
            # Add current subjects and grades
            subjects = self.table.item(current_row, 2).text().split(", ")
            grades = self.table.item(current_row, 3).text().split(", ")
            
            for subject, grade in zip(subjects, grades):
                dialog.add_subject_field()
                dialog.subjects[-1][0].setText(subject)
                dialog.subjects[-1][1].setValue(float(grade))
            
            if dialog.exec():
                student_data = dialog.get_student_data()
                
                # Update table
                avg = sum(student_data["grades"].values()) / len(student_data["grades"])
                grade = self.assign_grade(avg)
                attendance_status = self.get_attendance_status(student_data["attendance"])
                
                row_data = [
                    student_data["name"],
                    student_data["id"],
                    ", ".join(student_data["grades"].keys()),
                    ", ".join(str(g) for g in student_data["grades"].values()),
                    str(student_data["attendance"]),
                    attendance_status,
                    f"{avg:.2f}",
                    grade
                ]
                
                for col, data in enumerate(row_data):
                    self.table.setItem(current_row, col, QTableWidgetItem(str(data)))
                
                self.save_table_to_csv()
                QMessageBox.information(self, "Success", "Student modified successfully!")

    def save_table_to_csv(self):
        with open("students.csv", mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Name", "ID", "Subjects", "Grades", "Attendance",
                "Attendance Status", "Average", "Final Grade"
            ])
            
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    row_data.append(self.table.item(row, col).text())
                writer.writerow(row_data)

    def save_student_to_csv(self, student, avg, grade, attendance_status):
        with open("students.csv", mode='a', newline='') as file:
            writer = csv.writer(file)
            
            if file.tell() == 0:
                writer.writerow([
                    "Name", "ID", "Subjects", "Grades", "Attendance",
                    "Attendance Status", "Average", "Final Grade"
                ])
            
            writer.writerow([
                student["name"],
                student["id"],
                ", ".join(student["grades"].keys()),
                ", ".join(str(g) for g in student["grades"].values()),
                student["attendance"],
                attendance_status,
                f"{avg:.2f}",
                grade
            ])

    def assign_grade(self, avg):
        if avg >= 90:
            return "A"
        elif avg >= 80:
            return "B"
        elif avg >= 70:
            return "C"
        elif avg >= 60:
            return "D"
        else:
            return "F"

    def get_attendance_status(self, attendance):
        if attendance >= 90:
            return "Excellent"
        elif attendance >= 75:
            return "Good"
        elif attendance >= 60:
            return "Fair"
        else:
            return "Poor"

def main():
    app = QApplication(sys.argv)
    window = StudentManagementSystem()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 