from __future__ import annotations

import getpass
import hashlib
import os
from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from .paths import CONFIG_DIR, ensure_directories


def _user_server_name() -> str:
    try:
        identity = f"{os.getuid()}:{CONFIG_DIR}"
    except AttributeError:
        identity = f"{getpass.getuser()}:{CONFIG_DIR}"
    digest = hashlib.sha256(identity.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"com.rahmiapps.LocalVoice.control.v1.{digest}"


SERVER_NAME = _user_server_name()
ALLOWED_COMMANDS = frozenset({"show", "start", "stop", "toggle", "cancel", "choose-language"})


class SingleInstanceGuard:
    def __init__(self) -> None:
        ensure_directories()
        self._lock = QLockFile(str(CONFIG_DIR / "localvoice.instance.lock"))
        self._lock.setStaleLockTime(30_000)
        self.acquired = self._lock.tryLock(250)

    def release(self) -> None:
        if self.acquired:
            self._lock.unlock()
            self.acquired = False

    @staticmethod
    def send_command(command: str, timeout_ms: int = 1500) -> bool:
        command = str(command).strip().lower()
        if command not in ALLOWED_COMMANDS:
            return False
        socket = QLocalSocket()
        socket.connectToServer(SERVER_NAME)
        if not socket.waitForConnected(max(100, min(int(timeout_ms), 5000))):
            return False
        payload = (command + "\n").encode("ascii")
        if socket.write(payload) != len(payload):
            socket.abort()
            return False
        success = socket.waitForBytesWritten(max(100, min(int(timeout_ms), 5000)))
        socket.disconnectFromServer()
        return bool(success)


class InstanceCommandServer(QObject):
    command_received = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.server = QLocalServer(self)
        self._sockets: set[QLocalSocket] = set()
        self.server.newConnection.connect(self._accept_connections)

    def start(self) -> bool:
        # Only the process holding the single-instance lock calls this. Removing
        # a stale endpoint cannot disconnect another valid LocalVoice process.
        QLocalServer.removeServer(SERVER_NAME)
        socket_option = getattr(QLocalServer, "UserAccessOption", None)
        if socket_option is None:
            enum = getattr(QLocalServer, "SocketOption", None)
            socket_option = getattr(enum, "UserAccessOption", None) if enum is not None else None
        if socket_option is not None:
            self.server.setSocketOptions(socket_option)
        return self.server.listen(SERVER_NAME)

    def close(self) -> None:
        for socket in list(self._sockets):
            socket.abort()
        self._sockets.clear()
        self.server.close()
        QLocalServer.removeServer(SERVER_NAME)

    def _accept_connections(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            self._sockets.add(socket)
            socket.readyRead.connect(lambda current=socket: self._read(current))
            socket.disconnected.connect(lambda current=socket: self._discard(current))
            if socket.bytesAvailable():
                self._read(socket)

    def _read(self, socket: QLocalSocket) -> None:
        payload = bytes(socket.readAll())[:128]
        for line in payload.decode("ascii", errors="ignore").splitlines():
            command = line.strip().lower()
            if command in ALLOWED_COMMANDS:
                self.command_received.emit(command)
        socket.disconnectFromServer()

    def _discard(self, socket: QLocalSocket) -> None:
        self._sockets.discard(socket)
        socket.deleteLater()
