import SWWSClient from "./index.mjs";

let swClient = new SWWSClient({
    myPrivateKey: '0x082195f7d68ced30b6b33dd2a58c4e6b039d48837a91ec2899d3f14ec8e9a649'
});

let swClient2 = new SWWSClient({
    myPrivateKey: '0x082195f7d68ced30b6b33dd2a58c4e6b039d48837a91ec2899d3f14ec8e9a611'
});

await swClient.init();
await swClient2.init();

console.log('Address1', swClient.address);
console.log('Address2', swClient2.address);

swClient.on('message', ({message, nodeAddress}) => {
    console.log('Received message', message, nodeAddress);
});

swClient.on('error', ({error, message}) => {
    console.error('Error', error, message);

});

swClient2.on('message', ({message, nodeAddress}) => {
    console.log('Received message2', message, nodeAddress);
});


await swClient.connect('ws://localhost:8080');
await swClient2.connect('ws://localhost:8080');

await swClient.waitConnection();
await swClient2.waitConnection();

console.log('Connected');
await swClient.sendMessage('0x015f57EB2Ae50c72fEc2E488b5343069f36acFA1', {message: 'Hello from client'});
await swClient2.sendMessage('0x89d6A9e3A32e590eb3de53c4608018f3BC648959', {message: 'Hello from client2'});
