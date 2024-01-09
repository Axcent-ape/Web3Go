from data import config
from core.utils import Web3Utils
from fake_useragent import UserAgent
import aiohttp

import datetime


class Web3Go:
    def __init__(self, key: str, thread: int):
        self.thread = thread
        self.web3_utils = Web3Utils(key=key, http_provider=config.BNB_RPC)

        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'uk-UA,uk;q=0.9',
            'Connection': 'keep-alive',
            'Origin': 'https://reiki.web3go.xyz',
            'Referer': 'https://reiki.web3go.xyz/taskboard',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': UserAgent(os='windows').random,
            'X-App-Channel': 'DIN',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        self.session = aiohttp.ClientSession(
            headers=headers,
            trust_env=True
        )

    @staticmethod
    def get_current_date(utc=False):
        if utc:
            return datetime.datetime.utcnow().strftime("%Y%m%d")
        return datetime.datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_utc_timestamp():
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    async def login(self):
        params = await self.get_login_params()
        address = params["address"]
        nonce = params["nonce"]
        msg = f"reiki.web3go.xyz wants you to sign in with your Ethereum account:\n{address}\n\n{params['challenge']}\n\nURI: https://reiki.web3go.xyz\nVersion: 1\nChain ID: 56\nNonce: {nonce}\nIssued At: {Web3Go.get_utc_timestamp()}"

        json_data = {
            'address': address,
            'nonce': nonce,
            'challenge': '{"msg":"' + msg.replace('\n', '\\n') + '"}',
            'signature': self.web3_utils.get_signed_code(msg),
        }

        response = await self.session.post('https://reiki.web3go.xyz/api/account/web3/web3_challenge', json=json_data)
        res_json = await response.json()
        auth_token = res_json.get("extra", {}).get("token")

        if auth_token:
            self.upd_login_token(auth_token)

        return bool(auth_token)

    async def get_login_params(self):
        json_data = {
            'address': self.web3_utils.acct.address,
        }

        response = await self.session.post('https://reiki.web3go.xyz/api/account/web3/web3_nonce', json=json_data)
        return await response.json()

    async def mint_nft_pass(self):
        # self.web3_utils.w3 = self.web3_utils.new_provider(http_provider=config.BNB_RPC)

        to = '0xa4Aff9170C34c0e38Fed74409F5742617d9E80dc'
        from_ = self.web3_utils.acct.address
        data = f"0x40d097c3000000000000000000000000{from_[2:].lower()}"
        gas_price = self.web3_utils.w3.to_wei(2, 'gwei')
        gas_limit = 165000
        chain_id = 56

        return self.web3_utils.send_data_tx(to=to, from_=from_, data=data, gas_price=gas_price, gas_limit=gas_limit, chain_id=chain_id)

    async def claim_today(self):
        start_data = int(self.get_current_date(True))

        url = f"https://reiki.web3go.xyz/api/checkin/points/his?start={start_data}&end={start_data+1}"
        response = await self.session.get(url=url)
        return (await response.json())[0].get('status') == 'checked'

    async def claim(self):
        params = {
            'day': self.get_current_date(),
        }

        response = await self.session.put('https://reiki.web3go.xyz/api/checkin', params=params)
        return await response.text() == "true"

    async def logout(self):
        await self.session.close()

    def upd_login_token(self, token: str):
        self.session.headers["Authorization"] = f"Bearer {token}"