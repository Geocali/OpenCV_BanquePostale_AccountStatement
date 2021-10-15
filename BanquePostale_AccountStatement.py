################################################################################
# Script to download banking account statements from www.labanquepostale.fr
################################################################################
#__author__ = "https://github.com/johnmarcc"
#__copyright__ = ""
#__credits__ = []
#__license__ = ""
#__version__ = "1.0.0"
#__maintainer__ = ""
#__email__ = ""
#__status__ = "For test pupose only"
################################################################################
# Requirements:
#  Firefox installed in environment
#  pip install -r requirements.txt
#  download Geckodriver from https://github.com/mozilla/geckodriver/releases and put it in the directory
################################################################################
# PARAMETERS
# All input parameters extracted from json file "BanquePostale_account.json"
# -- param_NumeroDeCompte: Bank account 11 char (eg '123456789X0')
# -- param_ID: id to connect to internet site, 6 digits
# -- param_PWD: password to connect to internet site, 6 digits
# -- param_DownloadFolder: local download directory where the pdf bank account
#    notes are downloaded
# -- param_HEADLESS_PROCESS: 'True' when we want the script to get a firefox
#    instance without visible window (batch process)
#    else 'False' when we want the script to open a visible firefox window
################################################################################
import sys
import abc
from pydantic import BaseModel, parse_file_as
import time
from typing import List
from datetime import datetime, timedelta
# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
# from skimage.measure import compare_ssim #for compare_ssim
# from skimage import measure #new version of compare_ssim
from skimage.metrics import structural_similarity as ssim, hausdorff_distance, mean_squared_error
from PIL import Image
import io
import cv2 #image matching
import os
import json

curr_path = os.path.dirname(os.path.realpath(__file__))


global DL_FOLDER
DL_FOLDER = "/home/beroot/source/OpenCV_BanquePostale_AccountStatement/downloads"
global HEADLESS_PROCESS
HEADLESS_PROCESS = False


class Account(BaseModel):
    id: str
    pwd: str
    account_nb: str


def get_account_params():

    #-> read banque account parameters from json file:
    params = parse_file_as(List[Account], 'BanquePostale_account.json')
    return params

def create_driver(params):
    options = Options()

    if (HEADLESS_PROCESS == "True"):
        options.add_argument("--headless")

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", ".")
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.downloadDir", ".")
    options.set_preference("browser.download.defaultFolder", ".")
    options.set_preference("browser.download.useDownloadDir", True)
    # options.set_preference("browser.download.viewableInternally.enabledTypes", "")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", 'text/plain;application/pdf;text/html;application/vnd.ms-excel;text/csv;application/x-csv')
    options.set_preference("browser.helperApps.alwaysAsk.force", False)
    options.set_preference("browser.download.forbid_open_with", True)
    driver = webdriver.Firefox(executable_path=curr_path + '/geckodriver', options=options)
    return driver


class IBankDownloader(abc.ABC):
    def login(
        driver: webdriver.Firefox,
        params: Account
    ):
        pass

    def download_operations(
        driver: webdriver.Firefox,
        params: Account
    ):
        pass


class LBPDownloader(IBankDownloader):

    def detect_digits(
        self,
        params: Account,
        downloaded_images_folder: str = 'img',
    ):
        #-> Match for first pwd digit
        uniq_digits_in_pwd = list(set(params.pwd))
        dictPWD = {
            params.pwd[0]: "", params.pwd[1]: "",
            params.pwd[2]: "", params.pwd[3]: "",
            params.pwd[4]: "", params.pwd[5]: ""
        }
        # loop on unique digits
        for element in range(len(uniq_digits_in_pwd)):

            # load Reference image for the current password digit
            if (HEADLESS_PROCESS == "True"):
                referenceDIR = 'REF_HEADLESS'
            else:
                referenceDIR = 'REF_LIVE_MODE'

            referenceImage = referenceDIR + '/' + uniq_digits_in_pwd[element] + '_REF.png'
            referenceIMG = cv2.imread(referenceImage)

            # 2) Check for similarities between the 2 images
            # loop on downloaded images
            min_mse = 9999999
            min_ind = -1
            for index in range(16):
                localIMG = cv2.imread(
                    f"{downloaded_images_folder}/val_cel_{str(index)}.png"
                )

                # convert the images to grayscale
                gray_referenceIMG = cv2.cvtColor(referenceIMG, cv2.COLOR_BGR2GRAY)
                gray_localIMG = cv2.cvtColor(localIMG, cv2.COLOR_BGR2GRAY)

                # look fo rthe ref image with the lower mean squared error difference
                mse = mean_squared_error(gray_referenceIMG, gray_localIMG)
                if mse < min_mse:
                    min_mse = mse
                    min_ind = index

            dictPWD[uniq_digits_in_pwd[element]] = f"val_cel_{str(min_ind)}"
        return dictPWD

    def login(
        self,
        driver: webdriver.Firefox,
        params: Account
    ):
        
        driver.get(
            "https://voscomptesenligne.labanquepostale.fr/wsost/OstBrokerWeb/"
            "loginform?TAM_OP=login&ERROR_CODE=0x00000000&"
            "URL=%2Fvoscomptes%2FcanalXHTML%2Fidentif.ea%3Forigin%3Dparticuliers"
        )

        # send id to form
        driver.find_element_by_id("val_cel_identifiant").send_keys(params.id)

        #-> get each image of each button from the virtual keyboard
        os.makedirs("img", exist_ok=True)
        for index in range(16):
            id_image = "val_cel_"+ str(index)
            img = driver.find_element_by_id(id_image).screenshot_as_png
            image = Image.open(io.BytesIO(img))
            image.save('img/'+id_image+'.png')

        dictPWD = self.detect_digits(params)

        #-> click on each button corresponding to the password
        for digit in params.pwd:
            element = dictPWD.get(digit)
            driver.find_element_by_id(element).click()

        time.sleep(0.5)
        #-> then click on Validate button
        driver.find_element_by_id("valider").click()
        time.sleep(0.5)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[text()="Continuer sans accepter >" or text()="CONTINUER SANS ACCEPTER"]')
                )
            ).click()
            return True
        except TimeoutException:
            elmts = driver.find_elements_by_xpath('//a[contains(text(),"Dernière connexion")]')
            if len(elmts) > 0:
                return True
            return False

    def download_operations(
        self,
        driver: webdriver.Firefox,
        params: Account
    ):
        account = params.account_nb
        elmt = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//*/span[contains(text(),"{account}")]'
            ))
        )
        driver.execute_script("arguments[0].click();", elmt)
        time.sleep(5)

        # button = driver.find_element_by_xpath('//button[@data-titrepopinv2="Téléchargement du détail de vos comptes"]')
        # button.click()
        # time.sleep(5)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//button[@data-titrepopinv2="Téléchargement du détail de vos comptes"]'
            ))
        ).click()
        time.sleep(5)

        iframe = driver.find_elements_by_tag_name("iframe")[0]
        driver.switch_to.frame(iframe)
        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//a[@title="Modifier"]'
            ))
        )
        button.click()

        # choose start and end dates
        radio = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//label[text()="Télécharger les opérations pour une période définie"]'
            ))
        )
        radio.click()
        date2 = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
        date1 = (datetime.now() - timedelta(days=89)).strftime("%d/%m/%Y")
        input1 = driver.find_element_by_xpath('//input[@id="dateDebutPeriode"]')
        input2 = driver.find_element_by_xpath('//input[@id="dateFinPeriode"]')
        input1.send_keys(date1)
        input2.send_keys(date2)

        # choose type of file to download
        driver.find_element_by_xpath('//*/span[contains(text(), "Tableur TSV")]').click()
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//li[contains(text(), "Tableur CSV")]'
            ))
        ).click()
        time.sleep(0.5)

        driver.find_element_by_xpath('//*/span[contains(text(),"Confirmer")]').click()
        time.sleep(5)
        # POST request, to
        # 'https://voscomptesenligne.labanquepostale.fr/voscomptes/canalXHTML/comptesCommun/telechargementMouvement/validerTelechargement-telechargementMouvements.ea?ts=1634023883889'
        last_post_request = [req for req in driver.requests if req.method == 'POST'][-1]
        data = last_post_request.response.body.decode('CP1252').replace("\r", "").split('\n')
        name = data[0].split(";")[1]
        date = data[3].split(";")[1].split("/")
        lines = data[7:-1]
        with open(
            f"{DL_FOLDER}/LBP_{name}_{date[2]}-{date[1]}-{date[0]}.csv",
            'w'
        ) as file:
            file.write('\n'.join(lines))
        # driver.find_element_by_xpath('//button[@class="close"]').click()
        # driver.switch_to.default_content()
    

class BanqPopDownloader(IBankDownloader):
    def login(
        self,
        driver: webdriver.Firefox,
        params: Account
    ):
        driver.get("https://www.banquepopulaire.fr")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*/span[contains(text(),"Continuer sans accepter")]'
            ))
        ).click()
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//*/span[contains(text(),"Espace personnel")]'
            ))
        ).click()
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
                '//option[contains(text(),"AUVERGNE RHONE ALPES")]'
            ))
        ).click()
        # enter id
        driver.find_element_by_xpath('//input[@id="input-identifier"]').send_keys("66666666")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//button[@class="full primary ui-button bpce-focus-reset]'
            ))
        ).click()

    def download_operations(
        self,
        driver: webdriver.Firefox,
        params: Account
    ):
        pass


if __name__ == "__main__":

    params = get_account_params()[0]
    driver = create_driver(params)

    lbp_dl = LBPDownloader()
    logged_in = LBPDownloader().login(driver, params)
    if not logged_in:
        print("Login failed, trying again")
        time.sleep(5)
        LBPDownloader().login(driver, params)
    LBPDownloader().download_operations(driver, params)

    time.sleep(10)  #let some seconds to download before stopping the webdriver
    driver.quit()   # kill the firefox instance
