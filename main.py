import random
from data import config
from core.web3go import Web3Go
from core.utils import random_line, logger
import asyncio


async def W3G(thread):
    logger.info(f"Поток {thread} | Начал работу")
    while True:
        act = await random_line('data/private_keys.txt')
        if not act: break

        if '::' in act:
            private_key, proxy = act.split('::')
        else:
            private_key = act
            proxy = None

        web3go = Web3Go(key=private_key, proxy=proxy)

        # логинится в аккаунте
        if await web3go.login():

            # минтит пасс, если он не сминчен
            if not web3go.web3_utils.balance_of_erc721(web3go.web3_utils.acct.address, '0xa4Aff9170C34c0e38Fed74409F5742617d9E80dc'):
                status, tx_hash = await web3go.mint_nft_pass()
                if status: logger.success(f"Поток {thread} | Сминтил пасс: {private_key}:{tx_hash}")
                else: logger.error(f"Поток {thread} | Сминтил пасс: {private_key}:{tx_hash}")

            await web3go.referral(config.REF_LINK.split('=')[1])

            # клеймит подарок, если он есть
            if await web3go.claim_gift():
                logger.success(f"Поток {thread} | Открыл подарок: {private_key}:{web3go.web3_utils.acct.address}")

            # проверяет, клеймил ли сегодня поинты
            if await web3go.claim_today():
                logger.warning(f"Поток {thread} | Сегодня уже клеймил поинты: {private_key}:{web3go.web3_utils.acct.address}")
            else:
                # клеймит поинты
                if await web3go.claim():
                    logger.success(f"Поток {thread} | Успешно заклеймил поинты: {private_key}:{web3go.web3_utils.acct.address}")

            # закрываем сессию
            await web3go.logout()

        # поток спит
        random_sleep = random.randint(config.DELAY[0], config.DELAY[1])
        logger.info(f"Поток {thread} | Спит {random_sleep} c.")
        await asyncio.sleep(random_sleep)

    logger.info(f"Поток {thread} | Закончил работу")


async def main():
    print("Автор софта: https://t.me/ApeCryptor")

    thread_count = int(input("Введите кол-во потоков: "))
    # thread_count = 1
    tasks = []
    for thread in range(1, thread_count+1):
        tasks.append(asyncio.create_task(W3G(thread)))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
