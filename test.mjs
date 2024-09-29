import SWWSClient from "./index.mjs";

let swClient = new SWWSClient({
    myPrivateKey: '0x082195f7d68ced30b6b33dd2a58c4e6b039d48837a91ec2899d3f14ec8e9a649'
});

await swClient.init();

swClient.on('message', ({message, nodeAddress}) => {
    console.log('Received message', message, nodeAddress);
});

swClient.on('error', ({error, message}) => {
    console.error('Error', error, message);

});

await swClient.connect('ws://localhost:8080');

await swClient.waitConnection();

console.log('Connected');
await swClient.sendMessage('0xa75502d567ab67ff94e875015cee4440372aab10', {message: 'Hello from client'});
