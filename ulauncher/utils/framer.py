import logging
import pickle
from struct import pack, unpack_from
from collections import deque
from gi.repository import GLib, Gio, GObject

INTSZ = 4

log = logging.getLogger()


class InvalidStateError(RuntimeError):
    """
    Raised if a method is called when the framer is in an invalid state for the request.
    """


class PickleFramer(GObject.GObject):
    """
    The PickleFramer frames objects serialized using Pickle into and out of a Gio based
    SocketConnection instances.

    The binary data resulting from Pickle serialization has no inherent boundaries, so this class
    uses a typical "bytes to follow" word to indicate the size of each frame worth of data. This
    way the receiver, which is expected to be another instance of PickleFramer, can correctly
    extract the right number of bytes to deserialize back into the original object. This class
    handles all of the async API of the Gio stream interface as well as some of the edge cases such
    as short reads and error states.
    """

    __gsignals__ = {
        "closed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "message_parsed": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    READ_SIZE = 65000

    def __init__(self):
        GObject.GObject.__init__(self)
        self._conn = None
        self._canceller = Gio.Cancellable.new()
        self._inbound = None
        self._outbound = deque()
        self._inprogress = None
        self._partial_reads = 0

    def set_connection(self, conn: Gio.SocketConnection):
        if self._conn:
            raise InvalidStateError("Socket already associated with this framer, please create a new instance.")
        self._conn = conn
        self._read_data()

    def is_closing(self):
        # The only async action that happens on the connection level (vs the individual in/out
        # streams) is close, so use the existing flag to detect if close is in progress.
        return self._conn.has_pending()

    def close(self):
        if self.is_closing():
            log.debug("Connection %s already closing", self)
        elif self._conn.get_input_stream().has_pending() or self._conn.get_output_stream().has_pending():
            self._canceller.cancel()
        else:
            log.debug("Starting to close connection %s", self)
            self._conn.close_async(GLib.PRIORITY_DEFAULT, None, self._close_ready, None)

    def send(self, obj: object):
        objp = pickle.dumps(obj)
        msg = pack("I", len(objp)) + objp
        self._outbound.append(msg)
        self._write_next()

    # pylint: disable=unused-argument
    def _close_ready(self, source, result, user):
        ret = self._conn.close_finish(result)
        if ret:
            log.debug("Connection (%s) closed", self)
        else:
            log.warning("Error closing connection %s", self)
        self.emit("closed")

    def _read_data(self):
        self._conn.get_input_stream().read_bytes_async(
            self.READ_SIZE, GLib.PRIORITY_DEFAULT, self._canceller, self._read_ready, None
        )

    # pylint: disable=unused-argument
    def _read_ready(self, source, result, user):
        bytesbuf = self._conn.get_input_stream().read_bytes_finish(result)
        if not bytesbuf or bytesbuf.get_size() == 0:
            self.close()
            return
        self._ingest_data(bytesbuf.get_data())
        self._read_data()

    def _ingest_data(self, data: bytes):
        log.debug("Received data of %d bytes", len(data))

        # The given connection is a stream, so this method must handle reads which don't have the
        # full message yet, as well as reads that have multiple messages. For local unix sockets,
        # this will generally be one message per read, since there are not all of the over-network
        # real world issues that can delay messages over the Internet.
        self._inbound = self._inbound + data if self._inbound else data

        ptr = 0
        while ptr < len(self._inbound):
            msgsize = unpack_from("I", self._inbound, ptr)[0]
            bytesleft = len(self._inbound) - ptr - INTSZ
            if msgsize > bytesleft:
                log.debug("Waiting for %d bytes of %d bytes.", msgsize - bytesleft, msgsize)
                break
            ptr += INTSZ
            objp = self._inbound[ptr : ptr + msgsize]
            obj = pickle.loads(objp)
            log.debug("Received message %s", obj)
            self.emit("message_parsed", obj)
            ptr += msgsize

        if ptr == len(self._inbound):
            self._inbound = None
        elif ptr:
            self._inbound = self._inbound[ptr:]

        if self._inbound:
            self._partial_reads += 1

    def _write_next(self):
        if self._inprogress or not self._outbound:
            return

        self._inprogress = self._outbound.popleft()
        self._conn.get_output_stream().write_all_async(
            self._inprogress, GLib.PRIORITY_DEFAULT, self._canceller, self._write_done, None
        )

    # pylint: disable=unused-argument
    def _write_done(self, source, result, user):
        done, written = self._conn.get_output_stream().write_all_finish(result)
        if not done and self._canceller.is_cancelled():
            log.debug("Write canceled, closing connection.")
            self.close()
        elif not done:
            log.error("Error writing message of length %d", len(self._inprogress))
        elif written != len(self._inprogress):
            log.error("Bytes written %d doesn't match expected bytes %d", written, len(self._inprogress))
        else:
            log.debug("Sent %d bytes", written)
        self._inprogress = None
        self._write_next()
