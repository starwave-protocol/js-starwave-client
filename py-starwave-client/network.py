import asyncio
import websockets
import json
import os
from .crypto import random_bytes_string
from .messages import UnencryptedSignedMessage, EncryptedSignedMessage
from web3 import Web3

PING_SOCKET_TIMEOUT = 10
WS_HEARTBEAT_INTERVAL = 60

WS_SERVICE_MESSAGE_TYPES = {
    'PING': 'ping',
    'PONG': 'pong',
    'HANDSHAKE': 'handshake',
    'HANDSHAKE_RESPONSE': 'handshake_response',
    'STARWAVE_MESSAGE': 'sw'
}

class WSMessage:
    def __init__(self, type, data):
        self.type = type
        self.data = data

    def json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return WSMessage(data['type'], data['data'])

    @staticmethod
    def create_ping():
        return WSMessage(WS_SERVICE_MESSAGE_TYPES['PING'], {})

    @staticmethod
    def create_pong():
        return WSMessage(WS_SERVICE_MESSAGE_TYPES['PONG'], {})

    @staticmethod
    def create_handshake(address, message):
        return WSMessage(WS_SERVICE_MESSAGE_TYPES['HANDSHAKE'], {'address': address, 'message': message})

    @staticmethod
    def create_handshake_response(address, sign):
        return WSMessage(WS_SERVICE_MESSAGE_TYPES['HANDSHAKE_RESPONSE'], {'address': address, 'sign'})

    @staticmethod
    def create_starwave_message(message):
        return WSMessage(WS_SERVICE_MESSAGE_TYPES['STARWAVE_MESSAGE'], message)

class WebsocketNetwork:
    def __init__(self, my_address, my_private_key):
        self.my_address = my_address
        self.my_private_key = my_private_key
        self.validation_message = random_bytes_string(32)
        self.address_map = {}
        self.connections_sockets = []
        self.peers = []

    async def init(self):
        for peer in self.peers:
            await self.connect_peer(peer)
        asyncio.create_task(self.heartbeat())

    def connections_count(self):
        return len(self.connections_sockets)

    def connected(self):
        return len(self.connections_sockets) > 0

    async def connect_peer(self, address):
        if address not in self.peers:
            self.peers.append(address)
        async with websockets.connect(address) as ws:
            await self.socket_open(ws)
            async for message in ws:
                await self.socket_message(message, ws)

    async def socket_message(self, message, ws, server=False):
        message = WSMessage.from_json(message)
        if message.type == WS_SERVICE_MESSAGE_TYPES['PING']:
            await ws.send(WSMessage.create_pong().json())
        elif message.type == WS_SERVICE_MESSAGE_TYPES['PONG']:
            pass
        elif message.type == WS_SERVICE_MESSAGE_TYPES['HANDSHAKE']:
            if message.data['address'] == self.my_address:
                await ws.close()
                return
            sign = Web3().eth.account.sign_message(message.data['message'], self.my_private_key)
            await ws.send(WSMessage.create_handshake_response(self.my_address, sign.signature.hex()).json())
            if server:
                await ws.send(WSMessage.create_handshake(self.my_address, self.validation_message).json())
        elif message.type == WS_SERVICE_MESSAGE_TYPES['HANDSHAKE_RESPONSE']:
            try:
                Web3().eth.account.recover_message(self.validation_message, signature=message.data['sign'])
                self.address_map[message.data['address']] = ws
                self.connections_sockets.append(ws)
            except Exception as e:
                pass
        elif message.type == WS_SERVICE_MESSAGE_TYPES['STARWAVE_MESSAGE']:
            if ws not in self.connections_sockets:
                return
            socket_address = next(key for key, value in self.address_map.items() if value == ws)
            await self.process_message(message.data, {'node_address': socket_address})

    async def socket_open(self, ws):
        await ws.send(WSMessage.create_handshake(self.my_address, self.validation_message).json())

    async def socket_close(self, ws):
        self.connections_sockets = [socket for socket in self.connections_sockets if socket != ws]
        self.address_map = {key: value for key, value in self.address_map.items() if value != ws}

    async def heartbeat(self):
        while True:
            await asyncio.sleep(WS_HEARTBEAT_INTERVAL)
            for ws in self.connections_sockets:
                await ws.send(WSMessage.create_ping().json())

    async def broadcast(self, message, options={'exclude': []}):
        excluded_sockets = [self.address_map[address] for address in options['exclude']]
        for ws in self.connections_sockets:
            if ws not in excluded_sockets:
                await ws.send(WSMessage.create_starwave_message(message).json())

    async def send(self, address, message):
        ws = self.address_map.get(address)
        if ws:
            await ws.send(WSMessage.create_starwave_message(message).json())

    async def has_connection(self, address):
        return address in self.address_map

    async def process_message(self, message, options):
        node_address = options.get('node_address')
        message_object = None
        if message['type'] == MESSAGE_TYPES['UNENCRYPTED']:
            message_object = UnencryptedSignedMessage.from_object(message)
        elif message['type'] == MESSAGE_TYPES['ENCRYPTED']:
            message_object = EncryptedSignedMessage.from_object(message)
        if message_object.is_expired():
            return
        try:
            await message_object.verify_signature()
        except Exception as e:
            return
        if message_object.from_address == self.my_address:
            return
        if message_object.to_address == self.my_address:
            # Emit message event
            pass
        else:
            # Forward message
            pass
