import {EventEmitter} from 'events';
import UnencryptedSignedMessage from "./messages/UnencryptedSignedMessage.mjs";
import EncryptedSignedMessage from "./messages/EncryptedSignedMessage.mjs";
import Web3Utils from "./Web3Utils.mjs";
import WebsocketNetwork from "./WebsocketNetwork.mjs";

export const MESSAGE_TYPES = {
    UNENCRYPTED: 'u',
    ENCRYPTED: 'e'
};

export const ERRORS = {
    'EXPIRED': 'EXPIRED',
    'DROP': 'DROP',
    'INVALID_SIGNATURE': 'INVALID_SIGNATURE',
    'LOOP': 'LOOP',
    'NO_ROUTE': 'NO_ROUTE'
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export class ProtocolMessages extends EventEmitter {
    constructor({myAddress, myPrivateKey}) {
        super();
        this.myAddress = myAddress;
        this.myPrivateKey = myPrivateKey;
    }

    async process(message, options = {nodeAddress: null}) {
        let from = message.from;
        let to = message.to;

        let nodeAddress = options.nodeAddress || null;

        let messageObject;
        switch (message.type) {
            case MESSAGE_TYPES.UNENCRYPTED:
                messageObject = UnencryptedSignedMessage.fromObject(message);
                break;
            case MESSAGE_TYPES.ENCRYPTED:
                messageObject = EncryptedSignedMessage.fromObject(message);
                break;
        }

        if (messageObject.isExpired()) {
            this.emit('error', {error: ERRORS.EXPIRED, message: messageObject});
            return;
        }

        try {
            await messageObject.verifySignature();
        } catch (e) {
            this.emit('error', {error: ERRORS.INVALID_SIGNATURE, message: messageObject});
            return;
        }

        if (from === this.myAddress) {
            this.emit('error', {error: ERRORS.LOOP, message: messageObject});
            return;
        }

        if (to === this.myAddress) {
            this.emit('message', {message: messageObject, nodeAddress});
        } /*else {
            let nextHop = this.networkMap.getNextHop(to);
            if (nextHop) {
                messageObject.hops.push(this.myAddress);
                this.emit('forward', {message: messageObject, nextHop});
            } else {
                this.emit('error', {error: ERRORS.NO_ROUTE, message: messageObject});
            }
        }*/
    }
}


export default class SWWSClient extends EventEmitter {
    constructor({myAddress, myPrivateKey}) {
        super();

        if (!myPrivateKey) {
            throw new Error('private key required');
        }

        this.myAddress = myAddress;
        this.myPrivateKey = myPrivateKey
    }

    async init() {
        if (!this.myAddress) {
            this.myAddress = await Web3Utils.privateKeyToAddress(this.myPrivateKey)
        }

        this.protocolMessages = new ProtocolMessages({myAddress: this.myAddress, myPrivateKey: this.myPrivateKey});
        this.wsn = new WebsocketNetwork({myAddress: this.myAddress, myPrivateKey: this.myPrivateKey});
        await this.wsn.init();
        this.wsn.on('message', async ({message, nodeAddress}) => {
            try {
                await this.protocolMessages.process(message, {nodeAddress});
            }catch (e) {
                this.emit('error', {error: e, message});
            }
        });

        this.protocolMessages.on('message', ({message, nodeAddress}) => {
            this.emit('message', {message, nodeAddress});
        });

        this.protocolMessages.on('error', ({error, message}) => {
            this.emit('error', {error, message});
        });

    }

    async connect(address) {
        await this.wsn.connectPeer(address);
    }

    async broadcast(message) {
        await this.wsn.broadcast(message, {exclude: [this.myAddress]});
    }

    async sendMessage(address, message) {
        let msgObj = new UnencryptedSignedMessage({from: this.myAddress, to: address, ...message});

        await msgObj.sign(this.myPrivateKey);

        await this.broadcast(msgObj.getFullMessage());
    }

    async waitConnection(maxAttempts = 0) {

        let attempts = 0;
        while (true) {
            if (this.wsn.connected()) {
                return true;
            }
            await sleep(100);
            if (maxAttempts > 0) {
                attempts++;
            }

            if(maxAttempts > 0 && attempts >= maxAttempts){
                return false;
            }
        }

        return false;

    }

    get address() {
        return this.myAddress;
    }

    get privateKey() {
        return this.myPrivateKey;
    }

}
