import itertools
from functools import reduce
import json
import requests

from ..KorailConstants.KorailConstants import (
    EMAIL_REGEX, PHONE_NUMBER_REGEX, KORAIL_URLS, DEFAULT_USER_AGENT, InputFlag
)


class Schedule:
    def __init__(self, data):
        self.train_type = data.get("h_trn_clsf_cd")
        self.train_name = data.get("h_trn_clsf_nm")
        self.train_group = data.get("h_trn_gp_cd")
        self.train_number = data.get("h_trn_no")
        self.delay_time = data.get("h_expct_dlay_hr")

        self.dep_station_name = data.get("h_dpt_rs_stn_nm")
        self.dep_code = data.get("h_dpt_rs_stn_cd")
        self.dep_date = data.get("h_dpt_dt")
        self.dep_time = data.get("h_dpt_tm")

        self.arr_station_name = data.get("h_arv_rs_stn_nm")
        self.arr_code = data.get("h_arv_rs_stn_cd")
        self.arr_date = data.get("h_arv_dt")
        self.arr_time = data.get("h_arv_tm")

        self.run_date = data.get("h_run_dt")

    def __repr__(self):
        dep_time = f"{self.dep_time[:2]}:{self.dep_time[2:4]}"
        arr_time = f"{self.arr_time[:2]}:{self.arr_time[2:4]}"

        dep_date = f"{int(self.dep_date[4:6])}월 {int(self.dep_date[6:])}일"

        repr_str = f"[{self.train_name}] {dep_date}, {self.dep_station_name}~{self.arr_station_name}({dep_time}~{arr_time})"
        return repr_str

class Train(Schedule):
    def __init__(self, data):
        super().__init__(data)
        self.reserve_possible = data.get("h_rsv_psb_flg")
        self.reserve_possible_price = data.get("h_rsv_psb_nm")
        self.special_possible_price = data.get("h_spe_rsv_psb_nm")

        self.special_seat_state = data.get("h_spe_rsv_nm")
        self.general_seat_state = data.get("h_gen_rsv_nm")

    def __repr__(self):
        repr_str = super().__repr__()

        if self.reserve_possible_price is not None or self.special_possible_price:
            seats_info = []
            special_price = self.special_possible_price.replace('\n', ' ')
            reserve_price = self.reserve_possible_price.replace('\n', ' ')

            if self.special_seat_available():
                seats_info.append(f"특실: {special_price}, {self.special_seat_state}")

            if self.general_seat_available():
                seats_info.append(f"일반실: {reserve_price}, {self.general_seat_state}")

            repr_str += ', ' + ', '.join(seats_info).rstrip(', ')

        return repr_str

    def special_seat_available(self):
        return self.special_seat_state == "매진" or self.special_seat_state == "-"

    def general_seat_available(self):
        return self.general_seat_state == "매진" or self.general_seat_state == "-"

    def seat_available(self):
        return self.general_seat_available() or self.special_seat_available()

class TrainType:
    KTX = "100"  # "KTX, KTX-산천",
    SAEMAEUL = "101"  # "새마을호",
    MUGUNGHWA = "102"  # "무궁화호",
    TONGGUEN = "103"  # "통근열차",
    NURIRO = "102"  # "누리로",
    ALL = "109"  # "전체",
    AIRPORT = "105"  # "공항직통",
    KTX_SANCHEON = "100"  # "KTX-산천",
    ITX_SAEMAEUL = "101"  # "ITX-새마을",
    ITX_CHEONGCHUN = "104"  # "ITX-청춘",

    def __init__(self):
        raise NotImplementedError("Do not make instance.")

class ReserveOption:
    GENERAL_FIRST = "GENERAL_FIRST"  # 일반실 우선
    GENERAL_ONLY = "GENERAL_ONLY"  # 일반실만
    SPECIAL_FIRST = "SPECIAL_FIRST"  # 특실 우선
    SPECIAL_ONLY = "SPECIAL_ONLY"  # 특실만

    def __init__(self):
        raise NotImplementedError("Do not make instance.")

class Ticket(Train):
    def __init__(self, data):
        raw_data = data["ticket_list"][0]["train_info"][0]
        super().__init__(raw_data)

        self.seat_no_end = raw_data.get("h_seat_no_end")
        self.seat_no_count = int(raw_data.get("h_seat_cnt", 0))

        self.buyer_name = raw_data.get("h_buy_ps_nm")
        self.sale_date = raw_data.get("h_orgtk_sale_dt")
        self.sale_info1 = raw_data.get("h_orgtk_wct_no")
        self.sale_info2 = raw_data.get("h_orgtk_ret_sale_dt")
        self.sale_info3 = raw_data.get("h_orgtk_sale_sqno")
        self.sale_info4 = raw_data.get("h_orgtk_ret_pwd")
        self.price = int(raw_data.get("h_rcvd_amt", 0))

        self.car_no = raw_data.get("h_srcar_no")
        self.seat_no = raw_data.get("h_seat_no")

    def __repr__(self):
        repr_str = super().__repr__()

        repr_str += f" => {self.car_no}호"

        if self.seat_no_count != 1:
            repr_str += f" {self.seat_no}~{self.seat_no_end}"
        else:
            repr_str += f" {self.seat_no}"

        repr_str += f", {self.price}원"

        return repr_str

    def get_ticket_no(self):
        return "-".join(map(str, (self.sale_info1, self.sale_info2, self.sale_info3, self.sale_info4)))

class Passenger:
    def __init__(self, typecode, count=1, discount_type="000", card="", card_no="", card_pw=""):
        self.typecode = typecode
        self.count = count
        self.discount_type = discount_type
        self.card = card
        self.card_no = card_no
        self.card_pw = card_pw

    @staticmethod
    def reduce(passenger_list):
        """Reduce passenger's list."""
        if list(filter(lambda x: not isinstance(x, Passenger), passenger_list)):
            raise TypeError("Passengers must be based on Passenger")

        groups = itertools.groupby(passenger_list, lambda x: x.group_key())
        return list(
            filter(
                lambda x: x.count > 0,
                [reduce(lambda a, b: a + b, g) for k, g in groups],
            )
        )

    def __add__(self, other):
        assert isinstance(other, self.__class__)
        if self.group_key() == other.group_key():
            return self.__class__(
                typecode=self.typecode,
                count=self.count + other.count,
                discount_type=self.discount_type,
                card=self.card,
                card_no=self.card_no,
                card_pw=self.card_pw,
            )
        else:
            raise TypeError(
                "other's group_key(%s) is not equal to self's group_key(%s)."
                % (other.group_key(), self.group_key())
            )

    def group_key(self):
        return f"{self.typecode}_{self.discount_type}_{self.card}_{self.card_no}_{self.card_pw}"

    def get_dict(self, index):
        assert isinstance(index, int)
        index = str(index)
        return {
            "txtPsgTpCd" + index: self.typecode,
            "txtDiscKndCd" + index: self.discount_type,
            "txtCompaCnt" + index: self.count,
            "txtCardCode_" + index: self.card,
            "txtCardNo_" + index: self.card_no,
            "txtCardPw_" + index: self.card_pw,
        }

class AdultPassenger(Passenger):
    def __init__(self, count=1, discount_type="000", card="", card_no="", card_pw=""):
        super().__init__("1", count, discount_type, card, card_no, card_pw)

class ChildPassenger(Passenger):
    def __init__(self, count=1, discount_type="000", card="", card_no="", card_pw=""):
        super().__init__("3", count, discount_type, card, card_no, card_pw)

class SeniorPassenger(Passenger):
    def __init__(self, count=1, discount_type="131", card="", card_no="", card_pw=""):
        super().__init__("1", count, discount_type, card, card_no, card_pw)

class Reservation(Train):
    def __init__(self, data):
        super().__init__(data)
        self.dep_date = data.get("h_run_dt")
        self.arr_date = data.get("h_run_dt")

        self.rsv_id = data.get("h_pnr_no")
        self.seat_no_count = int(data.get("h_tot_seat_cnt"))
        self.buy_limit_date = data.get("h_ntisu_lmt_dt")
        self.buy_limit_time = data.get("h_ntisu_lmt_tm")
        self.price = int(data.get("h_rsv_amt"))
        self.journey_no = data.get("txtJrnySqno", "001")
        self.journey_cnt = data.get("txtJrnyCnt", "01")
        self.rsv_chg_no = data.get("hidRsvChgNo", "00000")

    def __repr__(self):
        repr_str = super().__repr__()

        repr_str += f", {self.price}원({self.seat_no_count}석)"

        buy_limit_time = f"{self.buy_limit_time[:2]}:{self.buy_limit_time[2:4]}"
        buy_limit_date = f"{int(self.buy_limit_date[4:6])}월 {int(self.buy_limit_date[6:])}일"

        repr_str += f", 구입기한 {buy_limit_date} {buy_limit_time}"

        return repr_str

class KorailSession:

    def __init__(self, korail_id, korail_pw, auto_login=True):
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        self.korail_id = korail_id
        self.korail_pw = korail_pw
        self._device = "AD"
        self._version = "190617001"
        self._key = "korail1234567890"
        self.membership_number = None
        self.name = None
        self.email = None
        self.is_login = False

        if auto_login:
            self.login(korail_id, korail_pw)

    def login(self, korail_id=None, korail_pw=None):
        if korail_id is None:
            korail_id = self.korail_id
        else:
            self.korail_id = korail_id

        if korail_pw is None:
            korail_pw = self.korail_pw
        else:
            self.korail_pw = korail_pw

        if EMAIL_REGEX.match(korail_id):
            txt_input_flg = InputFlag.EMAIL.value
        elif PHONE_NUMBER_REGEX.match(korail_id):
            txt_input_flg = InputFlag.PHONE_NUMBER.value
        else:
            txt_input_flg = InputFlag.MEMBERSHIP_NUMBER.value

        url = KORAIL_URLS["login"]
        data = {
            "Device": self._device,
            "Version": "150718001",
            "txtInputFlg": txt_input_flg,
            "txtMemberNo": korail_id,
            "txtPwd": korail_pw,
        }

        r = self._session.post(url, data=data)
        j = json.loads(r.text)

        if j["strResult"] == "SUCC" and j.get("strMbCrdNo") is not None:
            self._key = j["Key"]
            self.membership_number = j["strMbCrdNo"]
            self.name = j["strCustNm"]
            self.email = j["strEmailAdr"]
            self.is_login = True
            return True, self._session
        else:
            self.is_login = False
            return False, None

    def logout(self):
        url = KORAIL_URLS["logout"]
        self._session.get(url)
        self.is_login = False
