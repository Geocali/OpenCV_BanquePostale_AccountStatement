import abc
from seleniumwire import webdriver

import model


class IBankDownloader(abc.ABC):
    def login(
        driver: webdriver.Firefox,
        params: model.Account
    ):
        pass

    def download_operations(
        driver: webdriver.Firefox,
        params: model.Account
    ):
        pass
