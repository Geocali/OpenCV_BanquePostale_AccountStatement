import os
import sys

curr_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(curr_path + "/..")

import BanquePostale_AccountStatement

class TestDetectDigits:

    def test_a(self) -> None:
        res = BanquePostale_AccountStatement.detect_digits(
            params=BanquePostale_AccountStatement.get_account_params(),
            downloaded_images_folder='tests/files/keyboard_lbp1',
        )
        assert res == {
            "0": "val_cel_10",
            "1": "val_cel_3",
            "2": "val_cel_12",
            "3": "val_cel_7",
            "4": "val_cel_9",
            "5": "val_cel_15",
            "6": "val_cel_6",
            "7": "val_cel_11",
            "8": "val_cel_1",
            "9": "val_cel_8",
        }
        a = 1
