# Starwave 2 javascript+websocket client library

This library provides a simple interface for interacting with the Starwave 2 network using WebSockets.

## Installation

```bash
npm install @starwave/js-starwave-client
```

## Usage

```javascript
import SWWSClient from '@starwave/js-starwave-client';

let swClient = new SWWSClient({
    myPrivateKey: '0x082195f7d68ced30b6b33dd2a58c4e6b039d48837a91ec2899d3f14ec8e9a649'
});

await swClient.init();

console.log('Address', swClient.address);

swClient.on('message', (message) => {
    console.log('Received message:', message);
});

swClient.on('error', (error) => {
    console.error('Error:', error);
});

await swClient.connect('ws://localhost:8080');

await swClient.waitConnection();

await swClient.sendMessage('0x015f57EB2Ae50c72fEc2E488b5343069f36acFA1', {message: 'Hello from client'});
```

## Protocol schema
See [PROTOCOL_OVERVIEW.md](./docs/PROTOCOL_OVERVIEW.md) for the protocol schema.
