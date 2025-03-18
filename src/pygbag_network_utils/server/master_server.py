import asyncio
import json
import ssl
import threading
import websockets
import random
import logging
import argparse
from . import EchoServer


class MainServer:
    def __init__(
        self,
        host="localhost",
        port=8765,
        ssl_context=None,
        game_server_class=EchoServer,
    ):
        self.host = host
        self.port = port
        self.echo_servers: dict[int, tuple[EchoServer, threading.Thread]] = {}
        self.next_server_id = 0
        self.lock = threading.Lock()
        self.ssl_context = ssl_context
        self.logger = logging.getLogger("MainServer")
        self.game_server_class = game_server_class

    async def handle_client(self, websocket):
        try:
            while True:
                try:
                    message = await websocket.recv()
                    self.logger.debug(f"Received message: {message}")
                    data = json.loads(message)
                    command = data.get("command")

                    if command == "list":
                        await self.list_echo_servers(websocket)
                    elif command == "create":
                        address = await self.create_echo_server()
                        await websocket.send(
                            json.dumps(
                                {"message": f"Created Echo Server", "address": address}
                            )
                            + "\n"
                        )
                    elif command == "join":
                        await self.join_echo_server(websocket, data.get("server_id"))
                    elif command == "message":
                        self.logger.info(f"Received message: {data.get('message')}")
                        await websocket.send(
                            json.dumps({"message": "Message received"}) + "\n"
                        )
                    elif command == "nuke":
                        self.logger.info(f"Nuking server")
                        await websocket.send(
                            json.dumps({"message": "Nuking server"}) + "\n"
                        )
                        for server_id, server_data in self.echo_servers.items():
                            server, thread = server_data
                            # server.broadcast()
                            server.running = False
                            # thread.join()
                            self.logger.info(f"Stopped server {server_id}")
                        self.echo_servers.clear()
                        await websocket.send(
                            json.dumps({"message": "All servers nuked"}) + "\n"
                        )
                        self.logger.info(f"All servers nuked")
                    else:
                        await websocket.send(
                            json.dumps({"error": "Invalid command"}) + "\n"
                        )
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSONDecodeError: {e}")
                    await websocket.send(
                        json.dumps({"error": "Invalid JSON format"}) + "\n"
                    )
                except KeyError as e:
                    self.logger.error(f"KeyError: {e}")
                    await websocket.send(
                        json.dumps({"error": f"Missing key: {e}"}) + "\n"
                    )
                except Exception as e:
                    self.logger.exception(
                        f"Unexpected error processing command from {websocket.remote_address}|{e}|"
                    )
                    break

        except websockets.exceptions.ConnectionClosedError:
            self.logger.info(f"Client disconnected from main server")
        except Exception as e:
            self.logger.exception(f"Error handling client: {e}")

    async def list_echo_servers(self, websocket):
        server_list = []
        with self.lock:
            for id, server_data in self.echo_servers.items():
                server, _ = server_data
                server_list.append(
                    {
                        "id": id,
                        "address": f"ws://{self.host}:{server.port}",
                        "clients": server.get_client_count(),
                    }
                )  # Include client count
        await websocket.send(json.dumps({"servers": server_list}) + "\n")

    async def create_echo_server(self):
        echo_port = self.next_server_id + 9000
        # echo_port = random.randint(9000, 9999)
        echo_server = self.game_server_class(self.host, echo_port)
        thread = threading.Thread(target=asyncio.run, args=(echo_server.start(),))
        thread.daemon = (
            True  # Allow main program to exit even if thread is still running
        )
        thread.start()
        with self.lock:
            self.echo_servers[self.next_server_id] = (echo_server, thread)
            server_id = self.next_server_id
            self.next_server_id += 1
        return f"ws://{self.host}:{echo_port}"

    async def join_echo_server(self, websocket, server_id):
        with self.lock:
            if server_id in self.echo_servers:
                server, _ = self.echo_servers[server_id]
                address = f"ws://{self.host}:{server.port}"
                await websocket.send(
                    json.dumps(
                        {
                            "message": f"Joined Echo Server {server_id}",
                            "address": address,
                            "host": self.host,
                            "port": server.port,
                            "server_id": server_id,
                        }
                    )
                    + "\n"
                )
            else:
                await websocket.send(json.dumps({"error": "Server not found"}) + "\n")

    async def start(self):
        try:
            server = await websockets.serve(
                self.handle_client, self.host, self.port, ssl=self.ssl_context
            )
            self.logger.info(f"Main server started on ws://{self.host}:{self.port}")
            await server.wait_closed()
        except Exception as e:
            self.logger.error(f"Error starting main server: {e}")


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Main Server for managing Echo Servers"
    )
    parser.add_argument(
        "--host", type=str, default="localhost", help="Host for the main server"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Port for the main server"
    )
    parser.add_argument(
        "--cert", type=int, default=None, help="Path to Cert file"
    )
    parser.add_argument(
        "--key", type=int, default=None, help="Path to Key file"
    )

    args = parser.parse_args()

    ssl_context=None
    if args.key and args.cert:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            ssl_context.load_cert_chain(certfile=args.cert, keyfile=args.key)
            logging.info("SSL context loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load SSL context: {str(e)}")
            logging.info("example will run withou ssl context")
            ssl_context=None


    main_server = MainServer(host=args.host, port=args.port, ssl_context=ssl_context)
    asyncio.run(main_server.start())


if __name__ == "__main__":
    main()
