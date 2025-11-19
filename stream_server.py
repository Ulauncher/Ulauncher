#!/usr/bin/env python3

"""Simple HTTP server that streams MJPEG from GStreamer pipeline."""

import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# Default configuration constants
DEFAULT_DISPLAY = ":99"
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_FRAMERATE = 5
DEFAULT_JPEG_QUALITY = 85
DEFAULT_PORT = 8080

# Argument index constants
ARG_DISPLAY = 1
ARG_WIDTH = 2
ARG_HEIGHT = 3
ARG_FRAMERATE = 4
ARG_JPEG_QUALITY = 5
ARG_PORT = 6


class MJPEGStreamHandler(BaseHTTPRequestHandler):
    gst_process = None

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()

            try:
                # Read from GStreamer stdout and forward to client
                for chunk in iter(lambda: MJPEGStreamHandler.gst_process.stdout.read(4096), b""):
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass  # Suppress default logging


def start_gstreamer(display, width, height, framerate, jpeg_quality):
    """Start GStreamer pipeline that outputs MJPEG to stdout."""
    cmd = [
        "gst-launch-1.0",
        "-q",
        "ximagesrc",
        f"display-name={display}",
        "use-damage=0",
        "show-pointer=true",
        "!",
        f"video/x-raw,framerate={framerate}/1",
        "!",
        "videoscale",
        "!",
        f"video/x-raw,width={width},height={height}",
        "!",
        "videoconvert",
        "!",
        "jpegenc",
        f"quality={jpeg_quality}",
        "!",
        "multipartmux",
        "boundary=frame",
        "!",
        "fdsink",
        "fd=1",
    ]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Separate stderr from stdout
    )


def main(display, width, height, framerate, jpeg_quality, port):
    sys.stdout.write(f"Starting GStreamer pipeline on display {display}...\n")
    MJPEGStreamHandler.gst_process = start_gstreamer(display, width, height, framerate, jpeg_quality)

    sys.stdout.write(f"Starting HTTP server on port {port}...\n")
    server = HTTPServer(("0.0.0.0", port), MJPEGStreamHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        MJPEGStreamHandler.gst_process.terminate()
        MJPEGStreamHandler.gst_process.wait()


if __name__ == "__main__":
    display = sys.argv[ARG_DISPLAY] if len(sys.argv) > ARG_DISPLAY else DEFAULT_DISPLAY
    width = int(sys.argv[ARG_WIDTH]) if len(sys.argv) > ARG_WIDTH else DEFAULT_WIDTH
    height = int(sys.argv[ARG_HEIGHT]) if len(sys.argv) > ARG_HEIGHT else DEFAULT_HEIGHT
    framerate = int(sys.argv[ARG_FRAMERATE]) if len(sys.argv) > ARG_FRAMERATE else DEFAULT_FRAMERATE
    jpeg_quality = int(sys.argv[ARG_JPEG_QUALITY]) if len(sys.argv) > ARG_JPEG_QUALITY else DEFAULT_JPEG_QUALITY
    port = int(sys.argv[ARG_PORT]) if len(sys.argv) > ARG_PORT else DEFAULT_PORT

    main(display, width, height, framerate, jpeg_quality, port)
