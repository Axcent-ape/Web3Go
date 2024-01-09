import random
from data import config
from core.web3go import Web3Go
from core.utils import random_line, logger
import asyncio


async def W3G(thread):
    logger.info(f"Thread {thread} | Started work")
    while True:
        private_key = await random_line('data/private_keys.txt')
        if not private_key: break

        web3go = Web3Go(key=private_key, thread=thread)

        if await web3go.login():

            if not web3go.web3_utils.balance_of_erc721(web3go.web3_utils.acct.address, '0xa4Aff9170C34c0e38Fed74409F5742617d9E80dc'):
                status, tx_hash = await web3go.mint_nft_pass()
                if status: logger.success(f"Thread {thread} | Minted pass: {private_key}:{tx_hash}")
                else: logger.error(f"Thread {thread} | Can't mint pass: {private_key}:{tx_hash}")

            if await web3go.claim_today():
                logger.warning(f"Thread {thread} | Today claimed points: {private_key}:{web3go.web3_utils.acct.address}")
            else:
                # клеймит поинты
                if await web3go.claim():
                    logger.success(f"Thread {thread} | Success claimed points: {private_key}:{web3go.web3_utils.acct.address}")

            await web3go.logout()

        random_sleep = random.randint(config.DELAY[0], config.DELAY[1])
        await asyncio.sleep(random_sleep)
        logger.info(f"Thread {thread} | Sleep {random_sleep} sec.")

    logger.info(f"Thread {thread} | Stopped work")


async def main():
    print("Soft author: https://t.me/ApeCryptor")

    thread_count = int(input("Input count of threads: "))
    # thread_count = 1
    tasks = []
    for thread in range(1, thread_count+1):
        tasks.append(asyncio.create_task(W3G(thread)))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
