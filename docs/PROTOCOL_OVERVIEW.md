# Starwave 2 Websocket Protocol Overview

## Overview

This protocol is implemented over WebSocket and designed to facilitate message exchange between network nodes. It supports two main message types: encrypted and unencrypted, as well as a signature verification mechanism to confirm the authenticity of the sender.

Each connection begins with authentication through a handshake, after which clients can exchange messages.

### Key Components:

1. **WebsocketNetwork**: Manages WebSocket network connections and message sending.
2. **UnencryptedSignedMessage**: A class representing unencrypted signed messages.
3. **EncryptedSignedMessage**: A class representing encrypted signed messages.

---

## Message Types

### Service Messages

There are several message types that support connection establishment and network maintenance.

| Type                | Description                                                             |
|---------------------|-------------------------------------------------------------------------|
| `PING`              | Used to check the connection status (Heartbeat).                        |
| `PONG`              | A response to the `PING` message.                                       |
| `HANDSHAKE`         | Initial handshake message exchanged between clients.                    |
| `HANDSHAKE_RESPONSE`| Response to the handshake containing a signature to confirm authenticity.|
| `STARWAVE_MESSAGE`  | The main protocol message carrying data between clients.                |

### Message Structure Example:

All messages are transmitted in JSON format and contain two main fields:

```json
{
  "type": "message_type",
  "data": {
    "key1": "value1",
    "key2": "value2"
  }
}
```

- **type**: The message type (`ping`, `pong`, `handshake`, `handshake_response`, `sw`).
- **data**: The message payload containing additional information, such as the address, message content, signature, etc.

### `data` Fields for `HANDSHAKE` and `HANDSHAKE_RESPONSE` Messages

#### HANDSHAKE:

```json
{
  "type": "handshake",
  "data": {
    "address": "0x12345",
    "message": "random_challenge"
  }
}
```

- **address**: The sender's address.
- **message**: A random string used for authenticity verification.

#### HANDSHAKE_RESPONSE:

```json
{
  "type": "handshake_response",
  "data": {
    "address": "0x12345",
    "sign": "signature_of_challenge"
  }
}
```

- **address**: The sender's address.
- **sign**: The sender's signature verifying the challenge string.

---

## Authentication

### Handshake Process

1. **Initiator (Client 1)**: Upon establishing a connection, the client sends a `HANDSHAKE` message containing its address and a random string.
2. **Response (Client 2)**: The receiving client signs the random string with its private key and sends back a `HANDSHAKE_RESPONSE` containing the signature.
3. **Verification (Client 1)**: The initiator verifies the signature and, upon successful verification, completes the handshake.

### Handshake Example:

1. Client 1 sends:

```json
{
  "type": "handshake",
  "data": {
    "address": "0xabc123",
    "message": "random_string"
  }
}
```

2. Client 2 responds:

```json
{
  "type": "handshake_response",
  "data": {
    "address": "0xdef456",
    "sign": "signature_of_random_string"
  }
}
```

3. Client 1 verifies the signature using Client 2's public key.

---

## Messages

### Unencrypted Messages (UnencryptedSignedMessage)

Unencrypted messages contain the message payload and a signature that confirms the sender's authenticity.

#### Message Structure:

```json
{
  "message": "Your message here",
  "signature": "hex_signature",
  "from": "0xabc123",
  "to": "0xdef456",
  "protocolVersion": 1,
  "timestamp": 1695548400000,
  "type": "u",
  "hops": [],
  "expectedRoute": []
}
```

- **message**: The actual message being sent from one client to another.
- **signature**: A signature verifying the authenticity of the sender.
- **from**: The sender's address.
- **to**: The recipient's address.
- **protocolVersion**: Protocol version (defaults to 1).
- **timestamp**: The time the message was sent (Unix timestamp).
- **type**: Message type, here `"u"` for unencrypted.
- **hops**: A list of nodes the message has traversed.
- **expectedRoute**: The expected route the message should follow.

### Encrypted Messages (EncryptedSignedMessage)

Encrypted messages work similarly to unencrypted ones but their payload is encrypted using symmetric encryption (AES-256).

#### Message Structure:

```json
{
  "message": {
    "d": "encrypted_message",
    "iv": "initialization_vector"
  },
  "signature": "hex_signature",
  "from": "0xabc123",
  "to": "0xdef456",
  "protocolVersion": 1,
  "timestamp": 1695548400000,
  "type": "e",
  "hops": [],
  "expectedRoute": []
}
```

- **message**: The encrypted message payload containing the actual data.
    - **d**: The encrypted data.
    - **iv**: The initialization vector used for encryption.
- Other fields are similar to those in unencrypted messages.

---

## Client library API

### Sending Messages

Clients can send messages using the `sendMessage(address, message)` method.

Example:

```python
await swClient.sendMessage('0x015f57EB2Ae50c72fEc2E488b5343069f36acFA1', {"message": "Hello, World!"})
```

### Connecting to the Network

Clients can connect to the WebSocket network using the `connect` method:

```python
await swClient.connect('ws://localhost:8080')
```

### Waiting for Connection

The client can wait for the connection to be fully established using the `waitConnection` method:

```python
await swClient.waitConnection()
```

---

## Protocol Schema

Here is the schematic representation of the data exchange process in the form of a table:

| Step           | Sender       | Receiver         | Message                  | Description                                                                                     |
|----------------|--------------|------------------|--------------------------|-------------------------------------------------------------------------------------------------|
| 1              | Client 1     | Server → Client 2 | `HANDSHAKE`               | Client 1 initiates the handshake by sending its address and a random challenge string.           |
| 2              | Client 2     | Server → Client 1 | `HANDSHAKE_RESPONSE`      | Client 2 responds by signing the random challenge and sending the signature back to Client 1.    |
| 3              | Client 1     | -                | Signature Verification    | Client 1 verifies the signature from Client 2 to complete the authentication process.            |
| 4 (optional)   | Client 1     | Server → Client 2 | `STARWAVE_MESSAGE (u/e)`  | After a successful handshake, Client 1 sends an unencrypted or encrypted message to Client 2.    |
| 5 (optional)   | Client 2     | Server → Client 1 | `STARWAVE_MESSAGE (u/e)`  | Client 2 responds by sending a message (encrypted or unencrypted) back to Client 1.              |
| 6 (optional)   | Server       | Client 1 and 2    | `PING` / `PONG`           | Periodic connection check between the server and clients to maintain connection (heartbeat).     |

### Field Descriptions:

- **Step**: The sequential step in the communication process.
- **Sender**: The party initiating the message transmission.
- **Receiver**: The target recipient of the message (either the server or another client).
- **Message**: The type of message (`HANDSHAKE`, `HANDSHAKE_RESPONSE`, `STARWAVE_MESSAGE`, `PING`, `PONG`).
- **Description**: A brief explanation of what happens at each step of the data exchange.

### Notes:
- **`STARWAVE_MESSAGE (u/e)`**: This is the primary protocol message, where "u" stands for an unencrypted message and "e" stands for an encrypted message.
- **`PING`/`PONG`**: These are heartbeat messages used to check the connection status between the server and clients.
