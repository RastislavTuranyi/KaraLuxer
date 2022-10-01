# GUI for KaraLuxer

from typing import List

import re
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QMessageBox, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
                             QDialog, QFileDialog, QCheckBox, QVBoxLayout)

import ass
import ass.line


class OverlapSelectionWindow(QDialog):
    """Window used to choose between overlapping lines."""

    def _line_select_callback(self, line_index: int) -> None:
        """Callback function used by the buttons to set the line to discard and close the window.

        The selected line can then be retrieved from the `selected_line` attribute.

        Args:
            line_index (int): The index of the line to discard.
        """

        self.selected_line = line_index
        self.close()

    def __init__(self, overlapping_lines: List[ass.line._Event]) -> None:
        """Constructor for the OverlapSelectionWindow.

        Args:
            overlapping_lines (List[ass.line._Event]): The lines to choose between.
        """

        super().__init__()

        # Window settings and flags
        self.setWindowTitle('Choose a line to discard')
        self.setGeometry(20, 20, 600, 200)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        # Window layout
        window_layout = QGridLayout()
        self.setLayout(window_layout)

        # Information
        window_layout.addWidget(QLabel('The following lines overlap, please select one to DISCARD.'), 0, 0)

        # Line selection buttons
        for i in range(0, len(overlapping_lines)):
            current_line = overlapping_lines[i]
            clean_line = re.sub(r'\{(.*?)\}', '', str(overlapping_lines[i].text))
            button_string = 'Time = {0} to {1} | Style = \"{2}\" | Text = {3}'.format(
                current_line.start,
                current_line.end,
                current_line.style,
                clean_line
            )
            line_button = QPushButton(button_string)
            line_button.clicked.connect(lambda: self._line_select_callback(i))
            window_layout.addWidget(line_button)


class KaraLuxerWindow(QDialog):
    """Main window for the script interface."""

    def _get_file_path(self, target: QLineEdit, filter: str) -> None:
        """Method to get the path to a file and update a target to hold the filepath.

        Args:
            target (QLineEdit): The target widget to update.
            filter (str): The filter to use for the file picker.
        """

        file_dialogue = QFileDialog()
        file_dialogue.setFileMode(QFileDialog.ExistingFile)
        file_dialogue.setNameFilter(filter)

        if file_dialogue.exec_() == QDialog.Accepted:
            target.setText(file_dialogue.selectedFiles()[0])

    def __init__(self) -> None:
        """Constructor for the KaraLuxer window."""

        super().__init__()

        self.process_thread = None

        # Window settings and flags
        self.setWindowTitle('KaraLuxer')
        self.setGeometry(20, 20, 700, 800)

        # Subtitle source group
        sub_source_group = QGroupBox('Subtitle Source')
        sub_source_layout = QGridLayout()

        sub_source_layout.addWidget(QLabel('Please specify one and only one of the following.'), 0, 0, 1, 3)

        self.kara_url_input = QLineEdit()
        sub_source_layout.addWidget(QLabel('Kara.moe URL:'), 1, 0)
        sub_source_layout.addWidget(self.kara_url_input, 1, 1)

        self.sub_file_input = QLineEdit()
        sub_source_layout.addWidget(QLabel('Subtitle File:'), 2, 0)
        sub_source_layout.addWidget(self.sub_file_input, 2, 1)

        sub_file_button = QPushButton('Browse')
        sub_file_button.clicked.connect(
            lambda: self._get_file_path(self.sub_file_input, "Subtitles (*.ass)")
        )
        sub_source_layout.addWidget(sub_file_button, 2, 2)

        sub_source_group.setLayout(sub_source_layout)

        # Essential arguments group
        essential_args_group = QGroupBox('Essential Arguments')
        essential_args_layout = QGridLayout()

        self.cover_input = QLineEdit()
        essential_args_layout.addWidget(QLabel('Cover Image:'), 0, 0)
        essential_args_layout.addWidget(self.cover_input, 0, 1)
        cover_button = QPushButton('Browse')
        cover_button.clicked.connect(lambda: self._get_file_path(self.cover_input, "Image files (*.jpg *.jpeg *.png)"))
        essential_args_layout.addWidget(cover_button, 0, 2)

        essential_args_group.setLayout(essential_args_layout)

        # Optional arguments group
        optional_args_group = QGroupBox('Optional Arguments')
        optional_args_layout = QGridLayout()
        optional_args_layout.setColumnStretch(0, 1)
        optional_args_layout.setColumnStretch(1, 2)
        optional_args_layout.setColumnStretch(2, 1)

        self.bg_input = QLineEdit()
        optional_args_layout.addWidget(QLabel('Background Image:'), 0, 0)
        optional_args_layout.addWidget(self.bg_input, 0, 1)
        bg_button = QPushButton('Browse')
        bg_button.clicked.connect(lambda: self._get_file_path(self.bg_input, "Image files (*.jpg *.jpeg *.png)"))
        optional_args_layout.addWidget(bg_button, 0, 2)

        self.bgv_input = QLineEdit()
        self.bgv_input.setPlaceholderText('Will override the Kara.moe video.')
        optional_args_layout.addWidget(QLabel('Background Video:'), 1, 0)
        optional_args_layout.addWidget(self.bgv_input, 1, 1)
        bgv_button = QPushButton('Browse')
        bgv_button.clicked.connect(lambda: self._get_file_path(self.bgv_input, "Video files (*.mp4)"))
        optional_args_layout.addWidget(bgv_button, 1, 2)

        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText('Will override the Kara.moe audio.')
        optional_args_layout.addWidget(QLabel('Audio:'), 2, 0)
        optional_args_layout.addWidget(self.audio_input, 2, 1)
        audio_button = QPushButton('Browse')
        audio_button.clicked.connect(lambda: self._get_file_path(self.audio_input, "Audio files (*.mp3)"))
        optional_args_layout.addWidget(audio_button, 2, 2)

        self.tv_checkbox = QCheckBox()
        optional_args_layout.addWidget(QLabel('TV Sized:'), 3, 0)
        optional_args_layout.addWidget(self.tv_checkbox, 3, 1)
        optional_args_layout.addWidget(QLabel('Appends "(TV)" to the song title'), 3, 2)

        optional_args_group.setLayout(optional_args_layout)

        # Advanced arguments group
        advanced_args_group = QGroupBox('Advanced Arguments')
        advanced_args_layout = QGridLayout()
        advanced_args_layout.setColumnStretch(0, 1)
        advanced_args_layout.setColumnStretch(1, 2)
        advanced_args_layout.setColumnStretch(2, 1)

        self.ignore_overlaps_checkbox = QCheckBox()
        advanced_args_layout.addWidget(QLabel('Ignore Overlaps:'), 0, 0)
        advanced_args_layout.addWidget(self.ignore_overlaps_checkbox, 0, 1)
        advanced_args_layout.addWidget(
            QLabel('Ignore overlapping lines (Will potentially require manual editing)'), 0, 2)

        self.force_dialogue_checkbox = QCheckBox()
        advanced_args_layout.addWidget(QLabel('Force Dialogue:'), 1, 0)
        advanced_args_layout.addWidget(self.force_dialogue_checkbox, 1, 1)
        advanced_args_layout.addWidget(
            QLabel('Forces the script to use lines marked "Dialogue" (Not recommended for Kara.moe maps)'), 1, 2)

        self.autopitch_checkbox = QCheckBox()
        advanced_args_layout.addWidget(QLabel('Generate pitches:'), 2, 0)
        advanced_args_layout.addWidget(self.autopitch_checkbox, 2, 1)
        advanced_args_layout.addWidget(QLabel('Will pitch the file using "ultrastar_pitch"'), 2, 2)

        advanced_args_group.setLayout(advanced_args_layout)

        # Run button
        run_button = QPushButton('Run')
        # run_button.clicked.connect()

        # Window layout
        window_layout = QVBoxLayout()
        window_layout.addWidget(sub_source_group)
        window_layout.addWidget(essential_args_group)
        window_layout.addWidget(optional_args_group)
        window_layout.addWidget(advanced_args_group)
        window_layout.addWidget(run_button)

        window_layout.addStretch(3)

        self.setLayout(window_layout)


if __name__ == '__main__':
    app = QApplication([])
    window = KaraLuxerWindow()
    window.show()
    sys.exit(app.exec_())
