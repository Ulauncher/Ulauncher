from __future__ import annotations

import json
import socket
from typing import Any
from unittest.mock import Mock

import pytest
from gi.repository import GLib

from ulauncher.utils.socket_msg_controller import SocketMsgController


def receive_msg(sock: socket.socket) -> str:
    return sock.recv(1024).decode()


def process_pending_events(iterations: int = 10) -> None:
    """Process pending GLib events."""
    context = GLib.MainContext.default()
    for _ in range(iterations):
        while context.pending():
            context.iteration(False)
        GLib.usleep(1000)  # 1ms


@pytest.fixture
def socket_pair() -> tuple[socket.socket, socket.socket]:
    return socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)


@pytest.fixture
def controller_pair(socket_pair: tuple[socket.socket, socket.socket]) -> tuple[SocketMsgController, socket.socket]:
    parent, child = socket_pair
    controller = SocketMsgController(parent.fileno())
    return controller, child


class TestSocketMsgController:
    def test_send_message(self, controller_pair: tuple[SocketMsgController, socket.socket]) -> None:
        """Test sending a message from controller."""
        controller, peer = controller_pair
        controller.send({"hello": "world", "number": 123})
        assert receive_msg(peer) == '{"hello": "world", "number": 123}\n'

    def test_receive_message(self, controller_pair: tuple[SocketMsgController, socket.socket]) -> None:
        """Test receiving a message."""
        controller, peer = controller_pair
        received: list[dict[str, Any]] = []
        controller.listen(received.append)
        peer.sendall(b'{"type": "test", "value": 42}\n')
        process_pending_events()
        assert received == [{"type": "test", "value": 42}]

    def test_non_serializable_data_ignored(self, controller_pair: tuple[SocketMsgController, socket.socket]) -> None:
        """Test that non-serializable data is ignored."""
        controller, peer = controller_pair
        controller.send({"func": lambda: None})
        peer.settimeout(0.1)
        with pytest.raises(socket.timeout):
            receive_msg(peer)

    def test_peer_close_calls_controller_close(
        self, controller_pair: tuple[SocketMsgController, socket.socket]
    ) -> None:
        """Test that closing the peer calls the controller on_close callback."""
        controller, peer = controller_pair
        on_close = Mock()
        controller._on_close = on_close
        controller.listen(lambda _on_msg: None)
        peer.close()
        process_pending_events()
        assert on_close.called

    def test_on_close_called_once(self, socket_pair: tuple[socket.socket, socket.socket]) -> None:
        """Test on_close is only called once."""
        parent, child = socket_pair
        on_close = Mock()
        controller = SocketMsgController(parent.fileno(), on_close=on_close)
        controller.listen(lambda _on_msg: None)
        child.close()
        process_pending_events()
        assert on_close.call_count == 1

    def test_close_method(self, socket_pair: tuple[socket.socket, socket.socket]) -> None:
        """Test that close can be called multiple times but only trigger on_close once."""
        parent, _child = socket_pair
        on_close = Mock()
        controller = SocketMsgController(parent.fileno(), on_close=on_close)
        controller.close()
        controller.close()
        controller.close()
        assert on_close.call_count == 1

    def test_send_after_close_triggers_on_close(self, socket_pair: tuple[socket.socket, socket.socket]) -> None:
        """Test that sending after close triggers on_close."""
        parent, child = socket_pair
        on_close = Mock()
        controller = SocketMsgController(parent.fileno(), on_close=on_close)

        child.close()
        controller.send({"test": "data"})

        assert on_close.called

    def test_two_way_communication(self, controller_pair: tuple[SocketMsgController, socket.socket]) -> None:
        """Test sending and receiving in both directions."""
        controller, peer = controller_pair
        received: list[dict[str, Any]] = []
        controller.listen(received.append)

        # Send from controller to peer
        controller.send({"from": "controller"})
        assert json.loads(receive_msg(peer)) == {"from": "controller"}

        # Send from peer to controller
        peer.sendall(b'{"from": "peer"}\n')
        process_pending_events()
        assert received == [{"from": "peer"}]
