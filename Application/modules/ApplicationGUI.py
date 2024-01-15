import threading
from time import sleep
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QPushButton, QFileDialog, QProgressBar
from PyQt5.QtWidgets import QVBoxLayout, QFrame, QMessageBox, QDesktopWidget
from modules.AudiobookGenerator import AudiobookGenerator
from properties.languages import languages


class ApplicationGUI(QWidget):
    def __init__(self):
        # QWidget init
        super().__init__()

        # Audiobook Generator
        self.audiobook_generator = None

        # GUI Init
        self.file_label = QLabel('Input file:')
        self.file_combobox = self.create_combobox()

        self.folder_label = QLabel('Output folder:')
        self.folder_combobox = self.create_combobox()

        self.language_label = QLabel('Language:')
        self.language_combobox = QComboBox()
        self.language_combobox.addItems(languages.keys())
        self.language_combobox.setCurrentText("English")

        self.choose_file_button = self.create_button('Choose file...', self.choose_file)
        self.choose_folder_button = self.create_button('Choose folder...', self.choose_folder)
        self.start_button = self.create_button('Start', self.start_process, style="QPushButton { padding: 10px; }")

        self.progress_label = QLabel('Progress:')
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Layout setup
        layout = QVBoxLayout(self)
        layout.addWidget(self.file_label)
        layout.addWidget(self.choose_file_button)
        layout.addWidget(self.folder_label)
        layout.addWidget(self.choose_folder_button)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combobox)
        layout.addWidget(self.create_separator())
        layout.addWidget(self.start_button)
        layout.addWidget(self.create_separator())
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)

        self.setLayout(layout)
        self.setGeometry(0, 0, 450, 200)
        self.setWindowTitle('AI Audiobook Generator')
        self.move_to_center()
        self.show()

    @staticmethod
    def create_combobox():
        """
        Create a QComboBox with specific settings.
        """
        combobox = QComboBox()
        combobox.setEditable(True)
        combobox.setInsertPolicy(QComboBox.InsertAtTop)
        return combobox

    @staticmethod
    def create_button(label, callback, style=None):
        """
        Create a QPushButton with specific settings.
        """
        button = QPushButton(label)
        button.clicked.connect(callback)
        if style:
            button.setStyleSheet(style)
        return button

    @staticmethod
    def create_separator():
        """
        Create a QFrame as a separator line.
        """
        separator_line = QFrame()
        separator_line.setFrameShape(QFrame.HLine)
        separator_line.setFrameShadow(QFrame.Sunken)
        return separator_line

    def move_to_center(self):
        """
        Move the GUI window to the center of the screen.
        """
        frame_geometry = self.frameGeometry()
        desktop_center = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(desktop_center)
        self.move(frame_geometry.topLeft())

    def disable_buttons(self, value):
        """
        Disable or enable all buttons based on the provided value.
        """
        self.start_button.setDisabled(value)
        self.choose_folder_button.setDisabled(value)
        self.choose_file_button.setDisabled(value)
        self.language_combobox.setDisabled(value)

    def choose_file(self):
        """
        Open a file dialog to choose a file and update UI accordingly.
        """
        selected_file, _ = QFileDialog.getOpenFileName(self, 'Choose file', '', 'Text files (*.txt);;All files (*)')

        if selected_file:
            self.file_combobox.addItem(selected_file)
            self.file_combobox.setCurrentIndex(self.file_combobox.count() - 1)
            self.choose_file_button.setText(selected_file)

    def choose_folder(self):
        """
        Open a folder dialog to choose a folder and update UI accordingly.
        """
        selected_folder = QFileDialog.getExistingDirectory(self, 'Choose folder', '')

        if selected_folder:
            self.folder_combobox.addItem(selected_folder)
            self.folder_combobox.setCurrentIndex(self.folder_combobox.count() - 1)
            self.choose_folder_button.setText(selected_folder)

    def start_process(self):
        """
        Initiates the audiobook generation process in a separate thread.
        """
        selected_file = self.file_combobox.currentText()
        selected_folder = self.folder_combobox.currentText()
        selected_language = self.language_combobox.currentText()
        lang_code = languages[selected_language][-3:]

        # Validate input file and output folder
        if not selected_file:
            QMessageBox.warning(self, 'Error', 'No file selected.', QMessageBox.Ok)
            return

        if not selected_folder:
            QMessageBox.warning(self, 'Error', 'No folder selected.', QMessageBox.Ok)
            return

        # Disable UI buttons during the audiobook generation process
        self.disable_buttons(True)

        # Start a new thread to handle the entire process
        process_thread = threading.Thread(target=self.process_thread, args=(selected_file, selected_folder, lang_code))
        process_thread.start()

    def process_thread(self, selected_file, selected_folder, lang_code):
        """
        Thread to handle the audiobook generation process.
        """
        # Start a new thread for the AudiobookGenerator
        generator_thread = threading.Thread(
            target=self.generator_thread,
            args=(selected_file, selected_folder, lang_code)
        )
        generator_thread.start()

        # Update progress bar every 2 seconds until audiobook generation is finished
        while True:
            if self.audiobook_generator.finish:
                self.progress_bar.setValue(100)
                break
            self.progress_bar.setValue(self.audiobook_generator.progress())
            sleep(2)

        generator_thread.join()

        # Enable UI buttons after the audiobook generation process is finished
        self.disable_buttons(False)

        # Display appropriate message based on the process outcome
        if self.audiobook_generator.status == "Audiobook generated successfully":
            QMessageBox.information(self, 'Information', self.audiobook_generator.summary(), QMessageBox.Ok)
        else:
            QMessageBox.warning(self, 'Error', self.audiobook_generator.status, QMessageBox.Ok)

        self.close()

    def generator_thread(self, selected_file, selected_folder, lang_code):
        """
        Create a AudiobookGenerator instance and start the generation process.
        """
        self.audiobook_generator = AudiobookGenerator(selected_file, selected_folder, lang_code)
        self.audiobook_generator.start()
