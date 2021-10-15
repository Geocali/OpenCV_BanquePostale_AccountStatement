import os
import sys

curr_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(curr_path + "/..")

import BanquePostale_AccountStatement

class Tests:

    def test_detect_digits_lbp(self) -> None:
        params = {
            'NumeroDeCompte': '2222222',
            'ID': '123456',
            'PWD': '123456',
            'DownloadFolder': '.',
            'HEADLESS_PROCESS': 'False',
        }
        res = BanquePostale_AccountStatement.LBPDownloader().detect_digits(
            params=params,
            downloaded_images_folder='tests/files/keyboard_lbp1',
        )
        assert res == {
            "1": "val_cel_3",
            "2": "val_cel_12",
            "3": "val_cel_7",
            "4": "val_cel_9",
            "5": "val_cel_15",
            "6": "val_cel_6",
        }
