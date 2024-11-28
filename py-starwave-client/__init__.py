from .network import WebsocketNetwork
from .messages import UnencryptedSignedMessage, EncryptedSignedMessage
from .crypto import hash, string2encryption_key, encrypt_message, decrypt_message, random_bytes_string
import asyncio
from web3 import Web3
from datetime import datetime

class SWWSClient:
    def __init__(self, my_private_key):
        if not my_private_key:
            raise ValueError('private key required')

        self.my_private_key = my_private_key
        self.my_address = None
        self.protocol_messages = None
        self.wsn = None

    async def init(self):
        if not self.my_address:
            self.my_address = Web3().eth.account.privateKeyToAccount(self.my_private_key).address

        self.protocol_messages = ProtocolMessages(my_address=self.my_address, my_private_key=self.my_private_key)
        self.wsn = WebsocketNetwork(my_address=self.my_address, my_private_key=self.my_private_key)
        await self.wsn.init()
        self.wsn.on('message', self._handle_message)
        self.protocol_messages.on('message', self._handle_protocol_message)
        self.protocol_messages.on('error', self._handle_protocol_error)

    async def connect(self, address):
        await self.wsn.connect_peer(address)

    async def broadcast(self, message):
        await self.wsn.broadcast(message, {'exclude': [self.my_address]})

    async def send_message(self, address, message):
        msg_obj = UnencryptedSignedMessage(message=message, from_address=self.my_address, to_address=address)
        await msg_obj.sign(self.my_private_key)
        await self.broadcast(msg_obj.get_full_message())

    async def wait_connection(self, max_attempts=0):
        attempts = 0
        while True:
            if self.wsn.connected():
                return True
            await asyncio.sleep(0.1)
            if max_attempts > 0:
                attempts += 1
            if max_attempts > 0 and attempts >= max_attempts:
                return False

    def _handle_message(self, message, node_address):
        self.emit('message', {'message': message, 'node_address': node_address})

    def _handle_protocol_message(self, message, node_address):
        self.emit('message', {'message': message, 'node_address': node_address})

    def _handle_protocol_error(self, error, message):
        self.emit('error', {'error': error, 'message': message})

    @property
    def address(self):
        return self.my_address

    @property
    def private_key(self):
        return self.my_private_key

class ProtocolMessages:
    def __init__(self, my_address, my_private_key):
        self.my_address = my_address
        self.my_private_key = my_private_key

    async def process(self, message, options={'node_address': None}):
        from_address = message['from']
        to_address = message['to']
        node_address = options.get('node_address')

        if message['type'] == 'u':
            message_obj = UnencryptedSignedMessage.from_object(message)
        elif message['type'] == 'e':
            message_obj = EncryptedSignedMessage.from_object(message)

        if message_obj.is_expired():
            self.emit('error', {'error': 'EXPIRED', 'message': message_obj})
            return

        try:
            await message_obj.verify_signature()
        except Exception:
            self.emit('error', {'error': 'INVALID_SIGNATURE', 'message': message_obj})
            return

        if from_address == self.my_address:
            self.emit('error', {'error': 'LOOP', 'message': message_obj})
            return

        if to_address == self.my_address:
            self.emit('message', {'message': message_obj, 'node_address': node_address})
        else:
            next_hop = self.network_map.get_next_hop(to_address)
            if next_hop:
                message_obj.hops.append(self.my_address)
                self.emit('forward', {'message': message_obj, 'next_hop': next_hop})
            else:
                self.emit('error', {'error': 'NO_ROUTE', 'message': message_obj})
