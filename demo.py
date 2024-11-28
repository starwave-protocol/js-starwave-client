from py_starwave_client import SWWSClient
import asyncio

async def main():
    swClient = SWWSClient(my_private_key='0x082195f7d68ced30b6b33dd2a58c4e6b039d48837a91ec2899d3f14ec8e9a649')
    swClient2 = SWWSClient(my_private_key='0x082195f7d68ced30b6b33dd2a58c4e6b039d48837a91ec2899d3f14ec8e9a611')

    await swClient.init()
    await swClient2.init()

    print('Address1', swClient.address)
    print('Address2', swClient2.address)

    swClient.on('message', lambda message, node_address: print('Received message', message, node_address))
    swClient.on('error', lambda error, message: print('Error', error, message))

    swClient2.on('message', lambda message, node_address: print('Received message2', message, node_address))
    swClient2.on('error', lambda error, message: print('Error', error, message))

    await swClient.connect('ws://localhost:8080')
    await swClient2.connect('ws://localhost:8080')

    await swClient.wait_connection()
    await swClient2.wait_connection()

    print('Connected')
    await swClient.send_message('0x015f57EB2Ae50c72fEc2E488b5343069f36acFA1', {'message': 'Hello from client'})
    await swClient2.send_message('0x89d6A9e3A32e590eb3de53c4608018f3BC648959', {'message': 'Hello from client2'})

if __name__ == '__main__':
    asyncio.run(main())
