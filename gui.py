import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QListWidget, QMessageBox, QPushButton, QDialog, QFileDialog, QHBoxLayout, QTextEdit, QListWidgetItem
import xml_orm, re

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.xml_list = QListWidget()
        layout.addWidget(self.xml_list)

        self.load_xml_roots()

        button1 = QPushButton("Nowy XML")
        button2 = QPushButton("Wybierz plik")
        button3 = QPushButton("Wczytaj XML")
        button4 = QPushButton("Usuń")
        button5 = QPushButton("Zmodyfikuj węzeł")
        button6 = QPushButton("Dodaj węzeł")
        button7 = QPushButton("Zmień kolejność węzłów")
        button8 = QPushButton("Znajdź wartość")

        button1.clicked.connect(self.new_xml)
        button2.clicked.connect(self.load_file)
        button3.clicked.connect(self.load_xml)
        button4.clicked.connect(self.delete_xml)
        button5.clicked.connect(self.modify_xml)
        button6.clicked.connect(self.add_node)
        button7.clicked.connect(self.change_order)
        button8.clicked.connect(self.find_value)

        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(button3)
        layout.addWidget(button4)
        layout.addWidget(button5)
        layout.addWidget(button6)
        layout.addWidget(button7)
        layout.addWidget(button8)

        self.setLayout(layout)
        self.setWindowTitle("XML Editor")
        self.show()
    
    def load_xml_roots(self):
        self.xml_list.clear()

        self.xml_list.addItem("Wybierz nazwę XML")
        for i, roots in xml_orm.available_xml():
            item = QListWidgetItem(roots)
            item.setWhatsThis(str(i))
            self.xml_list.addItem(item)
        self.xml_list.setCurrentRow(0)
    
    def new_xml(self):
        dialog = XMLEditorInterface("", [('Zapisz', 'save')],self)
        dialog.exec()
        self.load_xml_roots()

    def load_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("XML files (*.xml)")
        file_dialog.exec()
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            file_path = selected_files[0]
        else:
            file_path = None

        if file_path:
            with open(file_path, "r") as file:
                xml_content = file.read()
            dialog = XMLEditorInterface(xml_content, [('Zapisz', 'save')], self)
            dialog.exec()
            self.load_xml_roots()


    def load_xml(self):
        selected_value = self.xml_list.currentRow()
        if selected_value:
            dialog = XMLTextEditor(xml_orm.load_xml(int(self.xml_list.currentItem().whatsThis())), self)
            dialog.exec()

    def delete_xml(self):
        selected_value = self.xml_list.currentRow()
        if selected_value:
            xml_orm.delete_xml(int(self.xml_list.currentItem().whatsThis()))
            self.load_xml_roots()

    def modify_xml(self):
        selected_value = self.xml_list.currentRow()
        if selected_value:
            dialog = XMLModifyInterface(int(self.xml_list.currentItem().whatsThis()), xml_orm.update_node_value,
                'Wpisz klucz=nowa wartość, aby zmienić wartość w zaznczonej lini.\nW celu zmiany tekstu wpisz jako klucz - __text__', 'Zamień', self)
            dialog.exec()

    def add_node(self):
        selected_value = self.xml_list.currentRow()
        if selected_value:
            dialog = XMLModifyInterface(int(self.xml_list.currentItem().whatsThis()), xml_orm.add_sub_xml,
                'Dodaj nowy węzeł lub strukture węzłów', 'Wstaw', self)
            dialog.exec()

    def change_order(self):
        selected_value = self.xml_list.currentRow()
        if selected_value:
            dialog = XMLModifyInterface(int(self.xml_list.currentItem().whatsThis()), xml_orm.change_node_order,
                'Wpisz numer pozycji, na której ma się znależć wybrany węzeł.', 'Zamień kolejność', self)
            dialog.exec()

    def find_value(self):
        selected_value = self.xml_list.currentRow()
        if selected_value:
            dialog = XMLSearchingInterface(int(self.xml_list.currentItem().whatsThis()), self)
            dialog.exec()


class XMLTextEditor(QDialog):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("XML Text Editor")
        self.setGeometry(100, 100, 300, 200)
        self.layout = QVBoxLayout()

        self.xml_text_edit = QTextEdit(self)
        self.layout.addWidget(self.xml_text_edit)
        self.xml_text_edit.setPlainText(text)

        self.setLayout(self.layout)

class XMLEditorInterface(XMLTextEditor):
    def __init__(self, text, create_buttons, parent=None):
        super().__init__(text, parent)
        buttons = []
        for i, button in enumerate(create_buttons):
            buttons.append(QPushButton(button[0]))
            buttons[i].clicked.connect(getattr(self, button[1]))
            self.layout.addWidget(buttons[i])
        self.setLayout(self.layout)
        
    def save(self, flag):
        try:
            xml_orm.save_xml(self.xml_text_edit.toPlainText())
            self.xml_text_edit.setPlainText('')
        except xml_orm.ElementTree.ParseError:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Validation")
            dlg.setText("Xml validation has failed")
            button = dlg.exec()


class XMLModifyInterface(XMLTextEditor):
    def __init__(self, id, func, info, text_button, parent=None):
        super().__init__('', parent)
        self.setGeometry(100, 100, 400, 500)
        self.root_id = id
        self.func = func
        self.xml_text_edit.setFixedHeight(100)

        self.xml_list = QListWidget()
        self.load_xml_doc()
        self.layout.insertWidget(0, self.xml_list)

        info = QLabel(info)
        self.layout.insertWidget(1, info)

        self.button1 = QPushButton(text_button)
        self.button1.clicked.connect(self.on_click)
        self.layout.addWidget(self.button1)

    def load_xml_doc(self):
        text = xml_orm.load_xml(self.root_id)

        self.xml_list.clear()
        self.xml_list.addItem("Wybierz węzeł")
        lines_of_xml = re.sub(r">\n<(?!/)", ">><<", text[text.find('\n')+1:]).split('><')
        for line in lines_of_xml:
            self.xml_list.addItem(line)
        self.xml_list.setCurrentRow(0)

    def on_click(self):
        selected = self.xml_list.currentRow()
        if selected:
            try:
                self.func(self.root_id, selected, self.xml_text_edit.toPlainText())
                self.xml_text_edit.clear()
                self.load_xml_doc()
            except:
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Walidacja")
                dlg.setText("Pole tekstowe jest błędnie uzupełnione.")
                button = dlg.exec()

class XMLSearchingInterface(XMLTextEditor):
    def __init__(self, id, parent=None):
        super().__init__('', parent)
        self.setGeometry(100, 100, 300, 400)
        self.root_id = id

        info = QLabel('Wprowadź szukaną wartość.')
        self.layout.insertWidget(0, info)

        self.found = QLabel('')
        self.found.hide()
        self.layout.addWidget(self.found)

        self.button1 = QPushButton('Znajdź')
        self.button1.clicked.connect(self.find_value)
        self.layout.addWidget(self.button1)
    
    def find_value(self):
        if nodes := xml_orm.find_node_with_value(self.root_id, self.xml_text_edit.toPlainText()):
            self.found.setText('\nZnalezionio wartości:\n'+"\n".join(nodes))
            self.found.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec())
