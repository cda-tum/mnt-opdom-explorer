"""Welcome widget for the Operational Domain Explorer.

Provides a drag-and-drop area and a browse button for loading SQD files.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mnt.ode.utils import IconLoader

from ..utils import is_dark_mode
from .theme import (
    BUTTON_BG_COLOR,
    BUTTON_TEXT_COLOR,
    PROGRESS_BAR_CHUNK_COLOR,
    get_theme_colors,
)

logger = logging.getLogger(__name__)


# TODO(marcel): welcome viewmodel
class Welcome(QWidget):  # type: ignore[misc]
    """Initial widget displayed to the user, prompting for SQD file input.

    Features a drag-and-drop area and a browse button.
    Emits a signal when a file is selected.
    """

    file_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initializes the Welcome widget.

        Args:
            parent: The parent widget, if any.
        """
        super().__init__(parent)
        self._icon_loader = IconLoader()
        self._loading: bool = False
        self._is_dark_mode = is_dark_mode()

        self._init_ui()
        self._apply_styles()

    def _init_ui(self) -> None:
        """Initializes the user interface components."""
        self.setAcceptDrops(True)

        main_layout = QVBoxLayout(self)
        # Overall padding for the Welcome widget content
        main_layout.setContentsMargins(30, 30, 30, 30)

        # --- Drop Area ---
        self.drop_area_frame = QFrame(self)
        self.drop_area_frame.setObjectName("dropAreaFrame")
        self.drop_area_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        drop_layout = QVBoxLayout(self.drop_area_frame)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(20)

        # Icon
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_icon = self._icon_loader.load_file_upload_icon()
        self.icon_label.setPixmap(upload_icon.pixmap(128, 128))
        drop_layout.addWidget(self.icon_label)

        # Instructional Text
        self.drop_text_label = QLabel("Drag & Drop an SQD File Here", self)
        font = self.drop_text_label.font()
        font.setPointSize(18)
        font.setWeight(QFont.Weight.Bold)
        self.drop_text_label.setFont(font)
        self.drop_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_text_label)

        self.or_text_label = QLabel("or", self)
        font_or = self.or_text_label.font()
        font_or.setPointSize(14)
        self.or_text_label.setFont(font_or)
        self.or_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.or_text_label)

        # Browse Button
        self.browse_button = QPushButton(self)
        browse_icon = self._icon_loader.load_folder_open_icon()
        self.browse_button.setIcon(browse_icon)
        self.browse_button.setText("Browse Files...")
        self.browse_button.clicked.connect(self._open_file_dialog)
        self.browse_button.setObjectName("browseButton")
        self.browse_button.setMinimumHeight(45)
        self.browse_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.browse_button.setMinimumWidth(200)
        drop_layout.addWidget(self.browse_button, 0, Qt.AlignmentFlag.AlignCenter)

        # Make drop_area_frame the primary expanding widget
        main_layout.addWidget(self.drop_area_frame, 1)

        # --- Container for Loading Indicators ---
        self.loading_indicators_container = QWidget(self)
        loading_indicators_layout = QVBoxLayout(self.loading_indicators_container)
        loading_indicators_layout.setContentsMargins(0, 20, 0, 10)
        loading_indicators_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_indicators_layout.setSpacing(8)

        self.loading_label = QLabel("Loading...", self)
        font_loading = self.loading_label.font()
        font_loading.setPointSize(12)
        self.loading_label.setFont(font_loading)
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_indicators_layout.addWidget(self.loading_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(12)
        self.progress_bar.setMinimumWidth(400)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        loading_indicators_layout.addWidget(self.progress_bar)

        self.loading_indicators_container.setLayout(loading_indicators_layout)

        label_height = self.loading_label.fontMetrics().height()
        progress_bar_height = self.progress_bar.maximumHeight()
        container_spacing = loading_indicators_layout.spacing()
        margins = loading_indicators_layout.contentsMargins()
        min_container_height = label_height + progress_bar_height + container_spacing + margins.top() + margins.bottom()
        self.loading_indicators_container.setMinimumHeight(min_container_height)
        self.loading_indicators_container.setMaximumHeight(min_container_height + 10)
        # Allow loading container to expand horizontally
        self.loading_indicators_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.loading_label.setVisible(False)
        self.progress_bar.setVisible(False)

        # Add a loading container with no stretch, so it takes its fixed vertical size
        main_layout.addWidget(self.loading_indicators_container, 0)

        self.setLayout(main_layout)

    def _apply_styles(self) -> None:
        """Applies stylesheets for a consistent look using theme constants."""
        theme_colors = get_theme_colors()

        bg_color = theme_colors["background_primary"].name()
        border_color = theme_colors["border_primary"].name()
        text_color = theme_colors["text_primary"].name()
        drop_area_bg_color = theme_colors["background_secondary"].name()
        drop_area_accept_bg_color = (
            QColor(drop_area_bg_color).lighter(105).name()
            if not self._is_dark_mode
            else QColor(drop_area_bg_color).darker(105).name()
        )

        button_bg_color_name = BUTTON_BG_COLOR.name()
        button_text_color_name = BUTTON_TEXT_COLOR.name()
        progress_bar_bg_color_name = theme_colors["background_tertiary"].name()
        progress_bar_chunk_color_name = PROGRESS_BAR_CHUNK_COLOR.name()

        self.setStyleSheet(f"""
            Welcome {{
                background-color: {bg_color};
            }}
            #dropAreaFrame {{
                border: 2px dashed {border_color};
                border-radius: 15px;
                background-color: {drop_area_bg_color};
            }}
            #dropAreaFrameAccept {{
                border: 2px solid {button_bg_color_name};
                border-radius: 15px;
                background-color: {drop_area_accept_bg_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            QPushButton#browseButton {{
                background-color: {button_bg_color_name};
                color: {button_text_color_name};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton#browseButton:hover {{
                background-color: {BUTTON_BG_COLOR.lighter(120).name()};
            }}
            QPushButton#browseButton:pressed {{
                background-color: {BUTTON_BG_COLOR.darker(120).name()};
            }}
            QProgressBar {{
                border: 1px solid {border_color};
                border-radius: 5px;
                background-color: {progress_bar_bg_color_name};
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {progress_bar_chunk_color_name};
                border-radius: 4px;
            }}
        """)

    @pyqtSlot()  # type: ignore[misc]
    def _open_file_dialog(self) -> None:
        """Opens a file dialog to select an SQD file."""
        if self._loading:
            logger.info("File dialog opening prevented: A file is already being processed.")
            return

        file_path_str, _ = QFileDialog.getOpenFileName(self, "Open SiDB Layout File", "", "SQD Files (*.sqd)")
        if file_path_str:
            logger.info("File selected via dialog: %s", file_path_str)
            self._process_file(Path(file_path_str))

    def _process_file(self, file_path: Path) -> None:
        """Handles the selected file path and emits the signal.

        Args:
            file_path: The path to the selected SQD file.
        """
        self.set_loading_state(loading=True, message=f"Processing {file_path.name}...")
        self.file_selected.emit(str(file_path))

    def set_loading_state(self, *, loading: bool, message: str | None = None, progress: int | None = None) -> None:
        """Updates the UI to reflect the loading state.

        Args:
            loading: Whether the widget is in a loading state.
            message: Optional message to display during loading.
            progress: Optional progress value (0-100) to show in the progress bar.
        """
        self._loading = loading
        self.browse_button.setEnabled(not loading)
        self.setAcceptDrops(not loading)

        if loading:
            self.loading_label.setText(message or "Loading...")
            self.loading_label.setVisible(True)
            self.progress_bar.setVisible(True)
            if progress is not None:
                self.progress_bar.setRange(0, 100)
                self.progress_bar.setValue(progress)
            else:
                self.progress_bar.setRange(0, 0)
        else:
            self.loading_label.setVisible(False)
            self.progress_bar.setVisible(False)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - camelCase is required by PyQt6
        """Handles drag enter events. Updates style. Accepts the event if it contains URLs.

        Args:
            event: The drag enter event.
        """
        if self._loading:
            event.ignore()
            return

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() == ".sqd":
                        event.acceptProposedAction()
                        self.drop_area_frame.setObjectName("dropAreaFrameAccept")
                        self._update_frame_style()
                        return
            event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:  # noqa: N802 - camelCase is required by PyQt6
        """Handles drag leave events. Resets style.

        Args:
            event: The drag leave event.
        """
        self.drop_area_frame.setObjectName("dropAreaFrame")
        self._update_frame_style()
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - camelCase is required by PyQt6
        """Handles drop events. Processes the first valid SQD file dropped.

        Args:
            event: The drop event.
        """
        self.drop_area_frame.setObjectName("dropAreaFrame")
        self._update_frame_style()

        if self._loading:
            event.ignore()
            return

        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() == ".sqd":
                        logger.info("File dropped: %s", file_path)
                        self._process_file(file_path)
                        return
            logger.warning("Drop event contained URLs, but no valid .sqd file found.")
        else:
            event.ignore()

    def _update_frame_style(self) -> None:
        """Helper to re-apply stylesheet to the frame for dynamic changes."""
        self.drop_area_frame.style().unpolish(self.drop_area_frame)
        self.drop_area_frame.style().polish(self.drop_area_frame)
        self.drop_area_frame.update()
