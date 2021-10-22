import os
import sys
import time
from datetime import datetime, timedelta

from skimage.metrics import structural_similarity as ssim, hausdorff_distance, mean_squared_error
from PIL import Image
import io
import cv2 #image matching

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


curr_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(curr_path + "/..")

import model
from i_bank_downloader import IBankDownloader


class BanqPopDownloader(IBankDownloader):
    def login(
        self,
        driver: webdriver.Firefox,
        params: model.Account
    ):
        driver.get("https://www.banquepopulaire.fr/se-connecter/sso?service=cyber")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*/span[contains(text(),"Continuer sans accepter")]'
            ))
        ).click()
        time.sleep(0.5)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//select[@id="select-v2-1"]'
            ))
        ).click()
        # choose region
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//option[contains(text(),"{params[0].region}")]'
            ))
        ).click()
        # enter id
        driver.find_element_by_xpath('//input[@id="input-identifier"]').send_keys(params[0].id)
        # Validate
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*/span[contains(text(),"Valider")]'
            ))
        ).click()
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*/span[contains(text(),"Plus tard")]'
            ))
        ).click()
        a = 1

    def download_operations(
        self,
        driver: webdriver.Firefox,
        params: model.Account
    ):
        pass
