from abc import ABCMeta

class KorailError(Exception, metaclass=ABCMeta):
    codes = set()

    def __init__(self, msg, code):
        self.msg = msg
        self.code = code

    def __str__(self):
        return f"{self.msg} ({self.code})"

    @classmethod
    def __contains__(cls, item):
        return item in cls.codes


class NeedToLoginError(KorailError):
    codes = {"P058"}

    def __init__(self, code=None):
        super().__init__("Need to Login", code)


class NoResultsError(KorailError):
    codes = {"P100", "WRG000000", "WRD000061", "WRT300005"}

    def __init__(self, code=None):
        super().__init__("No Results", code)


class SoldOutError(KorailError):
    codes = {"ERR211161"}

    def __init__(self, code=None):
        super().__init__("Sold out", code)
