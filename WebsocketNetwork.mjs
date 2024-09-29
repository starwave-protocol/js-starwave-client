
import {WebSocketServer, WebSocket} from "ws";
import Crypto from "./Crypto.mjs";
import Web3Utils from "./Web3Utils.mjs";
import {EventEmitter} from "events";

const PING_SOCKET_TIMEOUT = 10000;
const WS_HEARTBEAT_INTERVAL = 60000;

export const WS_SERVICE_MESSAGE_TYPES = {
    PING: 'ping',
    PONG: 'pong',
    HANDSHAKE: 'handshake',
    HANDSHAKE_RESPONSE: 'handshake_response',
    STARWAVE_MESSAGE: 'sw'
    //TODO: Peer exchange
};

const Logger = {
    log: console.log,
    error: console.error
}

class WSMessage {
    constructor({type, data}) {
        this.type = type;
        this.data = data;
    }

    json() {
        return JSON.stringify(this);
    }

    static fromJson(json) {
        return new WSMessage(JSON.parse(json));
    }

    static createPing() {
        return new WSMessage({type: WS_SERVICE_MESSAGE_TYPES.PING, data: {}});
    }

    static createPong() {
        return new WSMessage({type: WS_SERVICE_MESSAGE_TYPES.PONG, data: {}});
    }

    static createHandshake(address, message) {
        return new WSMessage({type: WS_SERVICE_MESSAGE_TYPES.HANDSHAKE, data: {address, message}});
    }

    static createHandshakeResponse(address, sign) {
        return new WSMessage({type: WS_SERVICE_MESSAGE_TYPES.HANDSHAKE_RESPONSE, data: {address, sign}});
    }

    static createStarwaveMessage(message) {
        return new WSMessage({type: WS_SERVICE_MESSAGE_TYPES.STARWAVE_MESSAGE, data: message});
    }
}

export default class WebsocketNetwork  extends EventEmitter {
    constructor({myAddress, myPrivateKey}) {
        super();
        this.myAddress = myAddress;
        this.myPrivateKey = myPrivateKey;

        this.validationMessage = Crypto.randomBytesString(32);

        this.addressMap = {};
        this.connectionsSockets = [];
        this.wss = null;
        this.peers = [];


    }

    async init() {

        for (let peer of this.peers) {
            await this.connectPeer(peer);
        }

        setInterval(() => {
            this.#heartbeat();

        }, WS_HEARTBEAT_INTERVAL);

    }

    connectionsCount(){
        return this.connectionsSockets.length;
    }

    connected(){
        return this.connectionsSockets.length > 0;
    }

    async connectPeer(address) {
        if (this.peers.indexOf(address) === -1) {
            this.peers.push(address);
        }

        let ws = new WebSocket(address);
        ws.on('message', (message) => {
            this.#socketMessage(message, ws);
        });
        ws.on('open', () => {
            setTimeout(() => {
                this.#socketOpen(ws);
            }, 1000);
        });
        ws.on('close', () => {
            this.#socketClose(ws);
        });
        ws.on('error', (e) => {
            Logger.error('WS: connection error', e);
            this.#socketClose(ws);
        });
    }

    async #socketMessage(message, ws, server) {
        message = WSMessage.fromJson(message);
        switch (message.type) {
            case WS_SERVICE_MESSAGE_TYPES.PING:
                ws.send(WSMessage.createPong().json());
                break;
            case WS_SERVICE_MESSAGE_TYPES.PONG:
                break;
            case WS_SERVICE_MESSAGE_TYPES.HANDSHAKE:

                if(message.data.address === this.myAddress){
                    Logger.error('WS: Connection to myself. Closing connection');
                    ws.close();
                    return;
                }

                let messageForSign = message.data.message;
                let sign = await Web3Utils.signMessage({message: messageForSign, privateKey: this.myPrivateKey});
                ws.send(WSMessage.createHandshakeResponse(this.myAddress, String(sign.signature).replace('0x', '')).json());

                if(server){
                    ws.send(WSMessage.createHandshake(this.myAddress, this.validationMessage).json());
                }

                break;
            case WS_SERVICE_MESSAGE_TYPES.HANDSHAKE_RESPONSE:

                try {
                    await Web3Utils.verifySignature({
                        address: message.data.address,
                        message: this.validationMessage,
                        signature: message.data.sign
                    });
                    this.addressMap[message.data.address] = ws;
                    this.connectionsSockets.push(ws);
                    Logger.log(`WS: Connected to ${message.data.address}`);
                } catch (e) {
                    Logger.error('WS: Error on handshake response', e);
                }


                break;

            case WS_SERVICE_MESSAGE_TYPES.STARWAVE_MESSAGE:
                if(this.connectionsSockets.indexOf(ws) === -1){
                    Logger.error('WS: Message from not authorized peer. Ignoring', message);
                    return;
                }
                let socketAddress = Object.keys(this.addressMap).find(key => this.addressMap[key] === ws);
                //console.log('!Message from', socketAddress);
               // await this.processMessage(message.data, {nodeAddress: socketAddress});
                this.emit('message', {message: message.data, nodeAddress: socketAddress})
                break;

            default:
                Logger.log('WS: Unknown message. Ignoring', message);
        }

    }

    async #socketOpen(ws) {
        Logger.log('WS: socket open');
        ws.send(WSMessage.createHandshake(this.myAddress, this.validationMessage).json());
    }

    async #socketClose(ws) {
        //TODO: Peer reconnect
        Logger.log('WS: socket close');
        this.connectionsSockets = this.connectionsSockets.filter(socket => socket !== ws);
        this.addressMap = Object.keys(this.addressMap).reduce((acc, key) => {
            if (this.addressMap[key] !== ws) {
                acc[key] = this.addressMap[key];
            }
            return acc;
        }, {});
    }

    async #heartbeat() {
        //TODO: Hang up connections that are not responding
        for (let ws of this.connectionsSockets) {
            ws.send(WSMessage.createPing().json());
        }
    }

    async broadcast(message, options = {exclude: []}) {
        let excludedSockets = options.exclude.map(address => this.addressMap[address]);
        //console.log('Broadcast message excluded', options.exclude);
        for (let ws of this.connectionsSockets) {

            if (excludedSockets.indexOf(ws) !== -1) {
                continue;
            }

            ws.send(WSMessage.createStarwaveMessage(message).json());
        }
    }

    async send(address, message) {
        let ws = this.addressMap[address];
        if (ws) {
            ws.send(WSMessage.createStarwaveMessage(message).json());
        }
    }

    async hasConnection(address) {
        return this.addressMap[address] !== undefined;
    }
}
