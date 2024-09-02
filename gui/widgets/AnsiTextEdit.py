import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QFontDatabase
from PyQt6.QtWidgets import QTextEdit, QMessageBox


class AnsiTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.setMonospaceFont()

    def setMonospaceFont(self):
        preferred_fonts = ['DejaVu Sans Mono', 'Liberation Mono', 'Courier New', 'Monospace']
        font_set = False

        for i, font_name in enumerate(preferred_fonts):
            if font_name in QFontDatabase.families():
                monospace_font = QFont(font_name)
                monospace_font.setStyleHint(QFont.StyleHint.TypeWriter)
                self.setFont(monospace_font)
                font_set = True

                # Warn if the first preferred font is not available
                if i > 0:
                    QMessageBox.warning(self, "Font Warning",
                                        f"Preferred font '{preferred_fonts[0]}' not found."
                                        f"Falling back to '{font_name}'."
                                        f"This might cause alignment issues within the displayed layout.")
                break

        if not font_set:
            QMessageBox.critical(self, "Font Error",
                                 "No suitable monospace font found. Please install a monospace font, "
                                 "preferably 'DejaVu Sans Mono', and restart the application.")
            sys.exit(1)

    def setAnsiText(self, ansi_text):
        self.clear()  # Clear any existing text
        cursor = self.textCursor()
        char_format = QTextCharFormat()

        # Regular expression to match ANSI escape sequences
        ansi_escape = re.compile(r'\x1b\[([0-9;]*?)m')

        # Split the text by ANSI escape sequences
        parts = ansi_escape.split(ansi_text)

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # This is normal text; apply the current format
                cursor.insertText(part, char_format)
            else:
                # This is an ANSI escape sequence; update the format
                codes = part.split(';')
                for code in codes:
                    if code == '0':
                        # Reset formatting
                        char_format = QTextCharFormat()
                    elif code.startswith('38') and '2' in codes:
                        # 24-bit color (True color) for foreground
                        try:
                            index = codes.index('38')
                            if codes[index + 1] == '2':
                                rgb = list(map(int, codes[index + 2:index + 5]))
                                char_format.setForeground(QColor(*rgb))
                        except (ValueError, IndexError):
                            pass
                    elif code.startswith('48') and '2' in codes:
                        # 24-bit color (True color) for background
                        try:
                            index = codes.index('48')
                            if codes[index + 1] == '2':
                                rgb = list(map(int, codes[index + 2:index + 5]))
                                char_format.setBackground(QColor(*rgb))
                        except (ValueError, IndexError):
                            pass
                    elif code == '1':
                        # Bold text
                        char_format.setFontWeight(QFont.Weight.Bold)

        self.setTextCursor(cursor)
