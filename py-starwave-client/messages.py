from web3 import Web3
import hashlib
import json
from datetime import datetime, timedelta
from .crypto import Crypto

MESSAGE_TYPES = {
    'UNENCRYPTED': 'u',
    'ENCRYPTED': 'e'
}

class UnencryptedSignedMessage:
    def __init__(self, message, signature, from_address, to_address, protocol_version=1, timestamp=None, expected_route=None):
        if not from_address or not to_address:
            raise ValueError('Invalid message')

        if not isinstance(protocol_version, int):
            raise ValueError('Invalid protocol version')

        if timestamp is None:
            timestamp = datetime.utcnow()

        self.message = message
        self.signature = signature
        self.from_address = from_address
        self.to_address = to_address
        self.protocol_version = protocol_version
        self.timestamp = timestamp
        self.type = MESSAGE_TYPES['UNENCRYPTED']
        self.hops = []
        self.expected_route = expected_route or []

    def add_hop(self, hop):
        if len(self.hops) >= int(os.getenv('MAX_HOPS', 10)):
            raise ValueError('Max hops reached')

        if self.has_hop(hop):
            raise ValueError('Hop already exists')

        self.hops.append(hop)

    def is_expired(self):
        expiry_time = self.timestamp + timedelta(seconds=int(os.getenv('MESSAGE_EXPIRY', 3600)))
        return datetime.utcnow() > expiry_time

    def has_hop(self, hop):
        return hop in self.hops

    def has_expected_route(self, route):
        return route in self.expected_route

    def clear_expected_route(self):
        self.expected_route = []

    def update_expected_route(self, route):
        self.expected_route = route

    def next_expected_route(self, current):
        try:
            return self.expected_route[self.expected_route.index(current) + 1]
        except (ValueError, IndexError):
            return None

    def _format_hash_string(self):
        return f"{json.dumps(self.message)}-{self.from_address}-{self.to_address}-{self.protocol_version}-{self.timestamp}"

    @property
    def hash(self):
        return hashlib.sha256(self._format_hash_string().encode()).hexdigest()

    @classmethod
    def from_object(cls, obj):
        message = cls(
            message=obj['message'],
            signature=obj['signature'],
            from_address=obj['from'],
            to_address=obj['to'],
            protocol_version=obj.get('protocolVersion', 1),
            timestamp=obj.get('timestamp', datetime.utcnow()),
            expected_route=obj.get('expectedRoute', [])
        )
        message.hops = obj.get('hops', [])
        return message

    def verify_signature(self):
        web3 = Web3()
        try:
            recovered_address = web3.eth.account.recover_message(
                self.hash,
                signature=self.signature
            )
            if recovered_address.lower() != self.from_address.lower():
                raise ValueError('Invalid signature')
        except Exception as e:
            raise ValueError('Invalid signature') from e

    def sign(self, private_key):
        web3 = Web3()
        signed_message = web3.eth.account.sign_message(
            self.hash,
            private_key=private_key
        )
        self.signature = signed_message.signature.hex()

    def get_full_message(self):
        return {
            'message': self.message,
            'signature': self.signature,
            'from': self.from_address,
            'to': self.to_address,
            'protocolVersion': self.protocol_version,
            'timestamp': self.timestamp,
            'type': self.type,
            'hops': self.hops,
            'expectedRoute': self.expected_route
        }

class EncryptedSignedMessage(UnencryptedSignedMessage):
    def __init__(self, message, signature, from_address, to_address, protocol_version=1, timestamp=None):
        super().__init__(message, signature, from_address, to_address, protocol_version, timestamp)
        self.type = MESSAGE_TYPES['ENCRYPTED']

    async def get_body(self, encryption_key):
        decrypted_message = await Crypto.decrypt_message(
            self.message['d'],
            self.message['iv'],
            Crypto.string2encryption_key(encryption_key)
        )
        return json.loads(decrypted_message)

    async def set_body(self, body, encryption_key):
        encrypted_message = await Crypto.encrypt_message(
            json.dumps(body),
            Crypto.string2encryption_key(encryption_key)
        )
        self.message = encrypted_message
        return self

    @classmethod
    def from_object(cls, obj):
        message = cls(
            message=obj['message'],
            signature=obj['signature'],
            from_address=obj['from'],
            to_address=obj['to'],
            protocol_version=obj.get('protocolVersion', 1),
            timestamp=obj.get('timestamp', datetime.utcnow())
        )
        message.hops = obj.get('hops', [])
        return message

    @staticmethod
    def is_encrypted_signed_message(obj):
        return obj['type'] == MESSAGE_TYPES['ENCRYPTED']
