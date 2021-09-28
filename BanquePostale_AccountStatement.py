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
import pydantic
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from skimage.measure import compare_ssim #for compare_ssim
# from skimage import measure #new version of compare_ssim
from skimage.metrics import structural_similarity as ssim, hausdorff_distance, mean_squared_error
from PIL import Image
import io
import cv2 #image matching
import os
import json

curr_path = os.path.dirname(os.path.realpath(__file__))

def get_account_params():

    #-> read banque account parameters from json file:
    params = {}
    try:
        accountFileName = 'BanquePostale_account.json'
        with open(accountFileName) as json_file:
            data = json.load(json_file)
    except:
        ThisError = sys.exc_info()[0]
        print("Error trying to import file",accountFileName,":",ThisError.__name__)
        sys.exit() #stop the script

    try:
        params['NumeroDeCompte'] = data['account'][0]['param_NumeroDeCompte']
        params['ID'] = data['account'][0]['param_ID']
        params['PWD'] = data['account'][0]['param_PWD']
        params['DownloadFolder'] =  curr_path
        params['HEADLESS_PROCESS'] =  data['account'][0]['param_HEADLESS_PROCESS']
    except:
        print("Incorrect input file format:",sys.exc_info())
        sys.exit() #stop the script

    print("Parameters extracted from input file: ",params['NumeroDeCompte'],    \
        '/',params['ID'],'/',params['PWD'],'/',params['DownloadFolder'],'/',            \
        params['HEADLESS_PROCESS'])
    return params

def create_driver(params):
    options = Options()

    if (params['HEADLESS_PROCESS'] == "True"):
        options.add_argument("--headless")

    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", params['DownloadFolder'])
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/tab-separated-values")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    driver = webdriver.Firefox(executable_path=curr_path + '/geckodriver', options=options)
    return driver


class IBankDownloader(abc.ABC):
    def login(
        driver: webdriver.Firefox,
        params
    ):
        pass

    def download_operations(
        driver: webdriver.Firefox,
        params
    ):
        pass


class LBPDownloader(IBankDownloader):

    def detect_digits(
        self,
        params,
        downloaded_images_folder: str = 'img',
    ):
        #-> Match for first pwd digit
        uniq_digits_in_pwd = list(set(params['PWD']))
        dictPWD = {
            params['PWD'][0]: "", params['PWD'][1]: "",
            params['PWD'][2]: "", params['PWD'][3]: "",
            params['PWD'][4]: "", params['PWD'][5]: ""
        }
        # loop on unique digits
        for element in range(len(uniq_digits_in_pwd)):

            # load Reference image for the current password digit
            if (params['HEADLESS_PROCESS'] == "True"):
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
        driver,
        params
    ):
        
        driver.get(
            "https://voscomptesenligne.labanquepostale.fr/wsost/OstBrokerWeb/"
            "loginform?TAM_OP=login&ERROR_CODE=0x00000000&"
            "URL=%2Fvoscomptes%2FcanalXHTML%2Fidentif.ea%3Forigin%3Dparticuliers"
        )

        # send id to form
        driver.find_element_by_id("val_cel_identifiant").send_keys(params['ID'])

        #-> get each image of each button from the virtual keyboard
        os.makedirs("img", exist_ok=True)
        for index in range(16):
            id_image = "val_cel_"+ str(index)
            img = driver.find_element_by_id(id_image).screenshot_as_png
            image = Image.open(io.BytesIO(img))
            image.save('img/'+id_image+'.png')

        dictPWD = self.detect_digits(params)

        #-> click on each button corresponding to the password
        for digit in params['PWD']:
            element = dictPWD.get(digit)
            driver.find_element_by_id(element).click()

        time.sleep(0.5)
        #-> then click on Validate button
        driver.find_element_by_id("valider").click()
        time.sleep(0.5)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[text()="Continuer sans accepter >"]')
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
        driver,
        params
    ):
        account = params['NumeroDeCompte']
        elmt = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//*/span[contains(text(),"{account}")]'
            ))
        )
        driver.execute_script("arguments[0].click();", elmt)

        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((
                By.XPATH,
                '//a[@data-titrepopinv2="Télécharger le détail"]'
            ))
        )
        time.sleep(1)
        button.click()

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

        driver.find_element_by_xpath('//*/span[contains(text(),"Confirmer")]').click()
        time.sleep(5)
        driver.find_element_by_xpath('//button[@class="close"]').click()
        driver.switch_to.default_content()
    
    

if __name__ == "__main__":

    params = get_account_params()
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
