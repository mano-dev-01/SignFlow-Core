import sys

from PyQt5.QtNetwork import QLocalSocket

IPC_SERVER_NAME = "signflow_overlay_ipc_v2"
CONNECT_TIMEOUT_MS = 500
WRITE_TIMEOUT_MS = 500
DISCONNECT_TIMEOUT_MS = 200
MESSAGE_DELIMITER = "\n"
EXIT_COMMANDS = {"/exit", "/q"}


def send_caption(caption_text):
    socket = QLocalSocket()
    socket.connectToServer(IPC_SERVER_NAME)

    if not socket.waitForConnected(CONNECT_TIMEOUT_MS):
        return False, "Overlay not reachable. Start caption_overlay.py first."

    payload = (caption_text + MESSAGE_DELIMITER).encode("utf-8")
    bytes_queued = socket.write(payload)
    if bytes_queued < 0:
        return False, "Failed to queue caption for sending."

    if not socket.waitForBytesWritten(WRITE_TIMEOUT_MS):
        return False, "Timed out while sending caption."

    socket.disconnectFromServer()
    if socket.state() != QLocalSocket.UnconnectedState:
        socket.waitForDisconnected(DISCONNECT_TIMEOUT_MS)

    return True, None


def main():
    print("Caption sender started. Type text and press Enter to update overlay.")
    print("Type /exit or /q to stop.")
    print(f"Using IPC socket: {IPC_SERVER_NAME}")

    while True:
        try:
            user_input = input("caption> ")
        except (EOFError, KeyboardInterrupt):
            print("\nSender stopped.")
            return

        command = user_input.strip().lower()
        if command in EXIT_COMMANDS:
            print("Sender stopped.")
            return

        if not user_input.strip():
            continue

        ok, error_message = send_caption(user_input)
        if not ok:
            print(f"Send failed: {error_message}")


if __name__ == "__main__":
    sys.exit(main())
