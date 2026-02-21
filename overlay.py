import signal
import sys

from PyQt5.QtCore import QTimer, Qt, QRect
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter
from PyQt5.QtNetwork import QLocalServer
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget

# -----------------------------
# Caption Content Configuration
# -----------------------------
INITIAL_CAPTION_TEXT = "INITIALIZED / WAITING..."

# -----------------------------
# Overlay Window Configuration
# -----------------------------
OVERLAY_HEIGHT_PX = 130
OVERLAY_POSITION_FROM_BOTTOM_PX = 0

# -----------------------------
# Caption Box Configuration
# -----------------------------
CAPTION_BOX_WIDTH_RATIO = 0.50
CAPTION_BOX_HEIGHT_PX = 50
CAPTION_BOX_CORNER_RADIUS_PX = 20
CAPTION_BOX_COLOR_RGB = (0, 0, 0)
CAPTION_BOX_OPACITY_ALPHA = 100

# -----------------------------
# Caption Text Configuration
# -----------------------------
CAPTION_FONT_FAMILY = "Segoe UI"
CAPTION_FONT_WEIGHT = QFont.DemiBold
CAPTION_MAX_FONT_SIZE_PT = 34
CAPTION_MIN_FONT_SIZE_PT = 12
CAPTION_TEXT_COLOR_RGB = (255, 255, 255)
CAPTION_TEXT_HORIZONTAL_PADDING_PX = 16
CAPTION_TEXT_VERTICAL_PADDING_PX = 12
CAPTION_TEXT_ALIGNMENT = Qt.AlignCenter | Qt.TextWordWrap

# -----------------------------
# Status Text Configuration
# -----------------------------
STATUS_FONT_FAMILY = "Segoe UI"
STATUS_FONT_SIZE_PT = 10
STATUS_FONT_WEIGHT = QFont.Normal
STATUS_TEXT_COLOR_RGB = (200, 255, 200)
STATUS_TEXT_MARGIN_LEFT_PX = 14
STATUS_TEXT_MARGIN_BOTTOM_PX = 8

# -----------------------------
# Close Button Configuration
# -----------------------------
CLOSE_BUTTON_TEXT = "\u00d7"
CLOSE_BUTTON_SIZE_PX = 28
CLOSE_BUTTON_OFFSET_RIGHT_PX = 12
CLOSE_BUTTON_OFFSET_TOP_PX = 10
CLOSE_BUTTON_FONT_FAMILY = "Segoe UI"
CLOSE_BUTTON_FONT_SIZE_PT = 18
CLOSE_BUTTON_FONT_WEIGHT = 700
CLOSE_BUTTON_STYLESHEET = (
    "QPushButton {"
    "color: white;"
    "background-color: rgba(255, 255, 255, 32);"
    "border: 1px solid rgba(255, 255, 255, 80);"
    "border-radius: 14px;"
    f"font: {CLOSE_BUTTON_FONT_WEIGHT} {CLOSE_BUTTON_FONT_SIZE_PT}px '{CLOSE_BUTTON_FONT_FAMILY}';"
    "padding-bottom: 1px;"
    "}"
    "QPushButton:hover {"
    "background-color: rgba(175, 0, 0, 120);"
    "}"
)

# -----------------------------
# IPC Configuration
# -----------------------------
CAPTION_IPC_SERVER_NAME = "signflow_overlay_ipc_v2"
CAPTION_MESSAGE_DELIMITER = "\n"

# -----------------------------
# App Runtime Configuration
# -----------------------------
APP_KEEP_ALIVE_TICK_MS = 250


class CaptionOverlay(QWidget):
    def __init__(self):
        super().__init__()

        self.current_caption = INITIAL_CAPTION_TEXT
        self.total_messages_received = 0

        self._client_buffers = {}
        self._client_sockets = []

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)

        self.close_button = QPushButton(CLOSE_BUTTON_TEXT, self)
        self.close_button.setFixedSize(CLOSE_BUTTON_SIZE_PX, CLOSE_BUTTON_SIZE_PX)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet(CLOSE_BUTTON_STYLESHEET)
        self.close_button.clicked.connect(QApplication.instance().quit)

        self.reposition_to_primary_screen()

        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is not None:
            primary_screen.geometryChanged.connect(self.reposition_to_primary_screen)

        app = QApplication.instance()
        if app is not None:
            app.screenAdded.connect(lambda _screen: self.reposition_to_primary_screen())
            app.screenRemoved.connect(lambda _screen: self.reposition_to_primary_screen())

        self.caption_server = QLocalServer(self)
        self.caption_server.newConnection.connect(self.handle_new_caption_connections)
        QLocalServer.removeServer(CAPTION_IPC_SERVER_NAME)
        self.caption_server.listen(CAPTION_IPC_SERVER_NAME)

        self.update()

    def reposition_to_primary_screen(self):
        primary_screen = QGuiApplication.primaryScreen()
        if primary_screen is None:
            return

        screen_geometry = primary_screen.geometry()
        overlay_top_y = (
            screen_geometry.y()
            + screen_geometry.height()
            - OVERLAY_HEIGHT_PX
            - OVERLAY_POSITION_FROM_BOTTOM_PX
        )

        self.setGeometry(
            screen_geometry.x(),
            overlay_top_y,
            screen_geometry.width(),
            OVERLAY_HEIGHT_PX,
        )
        self.update_close_button_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_close_button_position()

    def closeEvent(self, event):
        for socket in list(self._client_sockets):
            socket.disconnectFromServer()
            socket.deleteLater()
        self._client_sockets.clear()
        self._client_buffers.clear()

        if self.caption_server.isListening():
            self.caption_server.close()
        QLocalServer.removeServer(CAPTION_IPC_SERVER_NAME)

        super().closeEvent(event)

    def caption_box_rect(self):
        box_width_px = int(self.width() * CAPTION_BOX_WIDTH_RATIO)
        box_left_x = (self.width() - box_width_px) // 2
        box_top_y = (self.height() - CAPTION_BOX_HEIGHT_PX) // 2
        return QRect(box_left_x, box_top_y, box_width_px, CAPTION_BOX_HEIGHT_PX)

    def update_close_button_position(self):
        box_rect = self.caption_box_rect()
        close_button_x = box_rect.right() - self.close_button.width() - CLOSE_BUTTON_OFFSET_RIGHT_PX
        close_button_y = box_rect.top() + CLOSE_BUTTON_OFFSET_TOP_PX
        self.close_button.move(close_button_x, close_button_y)

    def calculate_fitting_caption_font(self, text_rect):
        for point_size in range(CAPTION_MAX_FONT_SIZE_PT, CAPTION_MIN_FONT_SIZE_PT - 1, -1):
            test_font = QFont(CAPTION_FONT_FAMILY, point_size, CAPTION_FONT_WEIGHT)
            test_metrics = QFontMetrics(test_font)
            text_bounds = test_metrics.boundingRect(text_rect, CAPTION_TEXT_ALIGNMENT, self.current_caption)
            if text_bounds.width() <= text_rect.width() and text_bounds.height() <= text_rect.height():
                return test_font

        return QFont(CAPTION_FONT_FAMILY, CAPTION_MIN_FONT_SIZE_PT, CAPTION_FONT_WEIGHT)

    def handle_new_caption_connections(self):
        while self.caption_server.hasPendingConnections():
            client_socket = self.caption_server.nextPendingConnection()
            self._client_sockets.append(client_socket)
            self._client_buffers[client_socket] = ""
            client_socket.readyRead.connect(
                lambda socket=client_socket: self.handle_caption_socket_ready_read(socket)
            )
            client_socket.disconnected.connect(
                lambda socket=client_socket: self.handle_caption_socket_disconnected(socket)
            )
        self.update()

    def handle_caption_socket_ready_read(self, socket):
        if socket not in self._client_buffers:
            return

        chunk = bytes(socket.readAll()).decode("utf-8", errors="ignore")
        buffer_text = self._client_buffers.get(socket, "") + chunk

        while CAPTION_MESSAGE_DELIMITER in buffer_text:
            message, remainder = buffer_text.split(CAPTION_MESSAGE_DELIMITER, 1)
            buffer_text = remainder
            message = message.strip()
            if message:
                self.set_external_caption(message)
        self._client_buffers[socket] = buffer_text

    def handle_caption_socket_disconnected(self, socket):
        # Flush any trailing buffered text that may arrive with a fast disconnect.
        self.handle_caption_socket_ready_read(socket)
        if socket in self._client_buffers:
            trailing_message = self._client_buffers[socket].strip()
            if trailing_message:
                self.set_external_caption(trailing_message)
        if socket in self._client_buffers:
            del self._client_buffers[socket]
        if socket in self._client_sockets:
            self._client_sockets.remove(socket)
        socket.deleteLater()
        self.update()

    def set_external_caption(self, caption_text):
        self.current_caption = caption_text
        self.total_messages_received += 1
        self.update()

    def current_status_text(self):
        server_state = "LISTENING" if self.caption_server.isListening() else "OFFLINE"
        client_count = len(self._client_sockets)
        return (
            f"STATUS: {server_state} | SOCKET: {CAPTION_IPC_SERVER_NAME} "
            f"| CLIENTS: {client_count} | MSGS: {self.total_messages_received}"
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        box_rect = self.caption_box_rect()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(*CAPTION_BOX_COLOR_RGB, CAPTION_BOX_OPACITY_ALPHA))
        painter.drawRoundedRect(box_rect, CAPTION_BOX_CORNER_RADIUS_PX, CAPTION_BOX_CORNER_RADIUS_PX)

        text_rect = box_rect.adjusted(
            CAPTION_TEXT_HORIZONTAL_PADDING_PX,
            CAPTION_TEXT_VERTICAL_PADDING_PX,
            -CAPTION_TEXT_HORIZONTAL_PADDING_PX,
            -CAPTION_TEXT_VERTICAL_PADDING_PX,
        )
        painter.setFont(self.calculate_fitting_caption_font(text_rect))
        painter.setPen(QColor(*CAPTION_TEXT_COLOR_RGB))
        painter.drawText(text_rect, CAPTION_TEXT_ALIGNMENT, self.current_caption)

        painter.setFont(QFont(STATUS_FONT_FAMILY, STATUS_FONT_SIZE_PT, STATUS_FONT_WEIGHT))
        painter.setPen(QColor(*STATUS_TEXT_COLOR_RGB))
        status_rect = self.rect().adjusted(
            STATUS_TEXT_MARGIN_LEFT_PX,
            0,
            -STATUS_TEXT_MARGIN_LEFT_PX,
            -STATUS_TEXT_MARGIN_BOTTOM_PX,
        )
        painter.drawText(status_rect, Qt.AlignLeft | Qt.AlignBottom, self.current_status_text())


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    overlay = CaptionOverlay()
    overlay.show()
    overlay.raise_()

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    keep_alive_timer = QTimer()
    keep_alive_timer.timeout.connect(lambda: None)
    keep_alive_timer.start(APP_KEEP_ALIVE_TICK_MS)

    app.aboutToQuit.connect(overlay.close)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
