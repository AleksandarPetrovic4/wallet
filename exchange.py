import threading
import requests
from requests.adapters import HTTPAdapter, Retry
from time import time
from db import Wallet


class Exchange(object):
    def __init__(self, **kwargs):
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    last_read = 0  # Timestamp of last successful read from NBP API

    API_URL = "https://api.nbp.pl/api/exchangerates/tables/c/?format=json"
    API_DELAY = 5 * 60  # How long to wait until next API read (in seconds)

    _exchange_rates = {}
    lock = threading.Lock()

    def get_exchange_rates(self):
        # If it was more than API_DELAY since last read, contact API again
        if time() - self.last_read > self.API_DELAY:
            # lock entire block so only one thread contacts API
            self.lock.acquire()
            # Check if another thread successfully contacted API while this thread was waiting for lock.acquire()
            if time() - self.last_read <= self.API_DELAY:
                return self._exchange_rates
            response = self.session.get(self.API_URL)
            new_exchange_rates = {}
            for rate in response.json()[0]["rates"]:
                new_exchange_rates[rate["code"]] = rate["ask"]
            self._exchange_rates = new_exchange_rates
            self.last_read = time()
            self.lock.release()
        return self._exchange_rates

    def to_pln(self, wallet: Wallet) -> float:
        if wallet.currency not in self.get_exchange_rates():
            return 0
        return self.get_exchange_rates()[wallet.currency] * wallet.amount
