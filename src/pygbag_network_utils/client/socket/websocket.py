import asyncio
import logging
import select
import socket
import struct


class WebSocketClient:
    """
    A simple WebSocket client for pygbag, using sockets directly for demonstration.
    This isn't a full WebSocket implementation; it's a simplified example for
    communicating with a basic echo server.

    Important: For real WebSocket communication, especially in production,
    use a proper WebSocket library like 'websockets' or 'aiohttp'.
    """

    def __init__(self, host, port, on_message_callback=None, socked_name="ws"):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.on_message_callback = on_message_callback
        self.receive_buffer = b""  # Accumulate received data
        self.socket_name = socked_name
        self.buffer = ""
        self.logger = logging.getLogger(f"WebSocketClient-{socked_name}")

    async def connect(self):
        """Connect to the server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)  # Non-blocking socket
        try:
            self.socket.connect((self.host, self.port))
        except BlockingIOError:
            pass

        self.running = True
        self.logger.debug(f"Connecting to {self.host}:{self.port}...")

    async def receive(self):
        self.logger.debug("Starting receive loop...")
        """Asynchronously receive data from the socket."""
        if self.socket is None:
            self.logger.error("Socket is not initialized.")
            return

        while self.running:
            # self.logger .debug("Receiving data...")
            try:
                ready_to_read, _, _ = select.select([self.socket], [], [], 0.1)
                if ready_to_read:
                    data = self.socket.recv(4096)  # Receive up to 4096 bytes
                    self.logger.debug(f"Received data: {data}")
                    if data:
                        decoded_message = data.decode("utf-8")
                        self.buffer += decoded_message
                        if decoded_message[-1] == "\n":
                            decoded_message = self.buffer
                            self.buffer = ""
                            decoded_message = decoded_message[:-1]
                        else:
                            continue

                        self.logger.debug(
                            f"Received message has ended with: {decoded_message[-1]}"
                        )
                        if self.on_message_callback:
                            self.on_message_callback(decoded_message, self.socket_name)
                        else:
                            self.logger.debug(f"Received message: {decoded_message}")
                    else:
                        # Socket closed
                        self.logger.debug("Server closed the connection.")
                        await self.close()
                        return
                await asyncio.sleep(0.01)  # Yield to the event loop

            except ConnectionResetError:
                self.logger.error("Connection reset by server.")
                await self.close()
                return
            except Exception as e:
                self.logger.error(f"Error receiving data: {e}")
                await self.close()
                return

    async def close(self):
        if self.socket:
            self.running = False
            try:
                # Send a close frame (simplified)
                self.socket.send(struct.pack("!BB", 0x88, 0x00))
                # Wait for close frame from server (simplified)
                self.socket.settimeout(2.0)
                self.socket.recv(1024)
            except Exception:
                pass  # Ignore errors during close
            finally:
                self.socket.close()
                self.socket = None
                self.logger.debug("Connection closed.")

    async def reconnect(self):
        await self.close()
        await asyncio.sleep(5)  # Wait before attempting to reconnect
        await self.connect()

    def send(self, message):
        if self.socket:
            try:
                self.socket.send((message + "\n").encode("utf-8"))
            except Exception as e:
                self.logger.error(f"Error sending data: {e}")
                asyncio.create_task(self.reconnect())

    def set_message_callback(self, callback):
        """Set the callback function for incoming messages."""
        self.on_message_callback = callback


async def socket_handler(ws_client):
    """Handle socket connection and messages."""
    await ws_client.connect()
    await asyncio.sleep(0.1)  # Wait for connection to establish
    await ws_client.receive()
