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
import os
import time
from typing import List
from pydantic import parse_file_as
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options

import model
from downloaders import banque_populaire, banque_postale

curr_path = os.path.dirname(os.path.realpath(__file__))

global DL_FOLDER
DL_FOLDER = "/home/beroot/source/OpenCV_BanquePostale_AccountStatement/downloads"
global HEADLESS_PROCESS
HEADLESS_PROCESS = False


def create_driver():
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
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference('useAutomationExtension', False)
    driver = webdriver.Firefox(executable_path=curr_path + '/geckodriver', options=options)
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
        })
        """
    )
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
        window.outerHeight - window.innerHeight + arguments[1]];
        """, 800, 600)
    driver.set_window_size(*window_size)
    return driver


if __name__ == "__main__":

    driver = create_driver()

    # params = parse_file_as(List[model.Account], 'BanquePostale_account.json')
    # logged_in = banque_postale.LBPDownloader().login(driver, params)
    # if not logged_in:
    #     print("Login failed, trying again")
    #     time.sleep(5)
    #     banque_postale.LBPDownloader().login(driver, params)
    # banque_postale.LBPDownloader().download_operations(driver, params)
    # time.sleep(10)  #let some seconds to download before stopping the webdriver

    params = parse_file_as(List[model.Account], 'BanquePopulaire_account.json')
    logged_in = banque_populaire.BanqPopDownloader().login(driver, params)
    if not logged_in:
        print("Login failed, trying again")
        time.sleep(5)
        banque_populaire.BanqPopDownloader().login(driver, params)
    banque_populaire.BanqPopDownloader.download_operations(driver, params)
    time.sleep(10)  #let some seconds to download before stopping the webdriver

    driver.quit()   # kill the firefox instance
