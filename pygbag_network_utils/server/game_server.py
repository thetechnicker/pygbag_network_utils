import asyncio
import json
import logging
import threading
import websockets


class BaseServer:
    def __init__(self, host, port, ssl_context=None):
        self.host = host
        self.port = port
        self.clients = set()
        self.lock = threading.Lock()
        self.running = True
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ssl_context = ssl_context

    async def handle_client_message(self, websocket, message):
        """
        Override this method in a subclass to define custom behavior for handling client messages.
        """
        raise NotImplementedError(
            "You must implement handle_client_message in your subclass!"
        )

    async def game_loop(self):
        """
        Override this method in a subclass to define custom game loop behavior.
        """
        raise NotImplementedError("You must implement game_loop in your subclass!")

    async def handle_client(self, websocket):
        with self.lock:
            self.clients.add(websocket)
            self.logger.info(
                f"Client connected to server at {self.host}:{self.port}. Total clients: {len(self.clients)}"
            )
        try:
            async for message in websocket:
                if not self.running:
                    self.logger.info("Server stopped. Closing connection.")
                    break
                try:
                    await self.handle_client_message(websocket, message)
                except Exception as e:
                    self.logger.exception(
                        f"Unexpected error processing message from {websocket.remote_address}: {e}"
                    )
        except websockets.exceptions.ConnectionClosedError:
            self.logger.info(
                f"Client disconnected from server at {self.host}:{self.port}"
            )
        except Exception as e:
            self.logger.exception(f"Error handling client: {e}")
        finally:
            with self.lock:
                self.clients.remove(websocket)
                self.logger.info(
                    f"Client disconnected from server at {self.host}:{self.port}. Total clients: {len(self.clients)}"
                )

    async def broadcast(self, message):
        disconnected_clients = []
        for client in self.clients:
            try:
                await client.send(message + "\n")  # Append newline character here
            except websockets.exceptions.ConnectionClosedError:
                self.logger.info("Client disconnected during broadcast.")
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.error(f"Error sending message to client: {e}")
                disconnected_clients.append(client)

        # Remove disconnected clients after iteration to avoid modifying set during iteration
        with self.lock:
            for client in disconnected_clients:
                self.clients.remove(client)

    async def start(self):
        try:
            self.server = await websockets.serve(
                self.handle_client, self.host, self.port, ssl=self.ssl_context
            )
            self.logger.info(f"Server started on ws://{self.host}:{self.port}")
            # Start the game loop task
            self.game_loop_task = asyncio.create_task(self.game_loop())
            await self.server.wait_closed()
            await self.game_loop_task
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")

    def get_client_count(self):
        with self.lock:
            return len(self.clients)


# Example of a subclass inheriting from BaseServer
class EchoServer(BaseServer):
    async def handle_client_message(self, websocket, message):
        """
        Custom behavior for handling client messages.
        """
        try:
            data = json.loads(message)
            data["echo"] = data["message"]
            del data["message"]
            response = json.dumps(data)
            await websocket.send(response + "\n")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSONDecodeError: {e}")
            await websocket.send(json.dumps({"error": "Invalid JSON format"}) + "\n")
        except KeyError as e:
            self.logger.error(f"KeyError: {e}")
            await websocket.send(json.dumps({"error": f"Missing key: {e}"}) + "\n")

    async def game_loop(self):
        """
        Custom game loop behavior.
        """
        while self.running:
            await asyncio.sleep(1)  # Simulate some periodic task
            await self.broadcast(json.dumps({"echo": "Game loop"}))


# Example usage
if __name__ == "__main__":
    import ssl

    logging.basicConfig(level=logging.INFO)

    # SSL context can be optional (set to None if not needed)
    ssl_context = None  # For example purposes; configure if needed

    echo_server = EchoServer(host="localhost", port=12345, ssl_context=ssl_context)

    try:
        asyncio.run(echo_server.start())
    except KeyboardInterrupt:
        echo_server.running = False
