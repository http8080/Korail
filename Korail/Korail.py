from datetime import datetime, timedelta, timezone
import json
from functools import reduce
from .KorailExceptions.KorailExceptions import (
    KorailError, NoResultsError, SoldOutError, NeedToLoginError
)
from .KorailConstants.KorailConstants import KORAIL_URLS

from .KorailClass.KorailClass import (
    Train, Ticket, Passenger, AdultPassenger,
    ChildPassenger, SeniorPassenger, TrainType,
    ReserveOption, Reservation, KorailSession
)

class Korail(KorailSession):

    def __init__(self, korail_id, korail_pw, auto_login=True, want_feedback=False):
        super(Korail, self).__init__(korail_id, korail_pw, auto_login)
        self.want_feedback = want_feedback

    def _result_check(self, j):
        if self.want_feedback:
            print(j["h_msg_txt"])

        if j["strResult"] == "FAIL":
            h_msg_cd = j.get("h_msg_cd", None)
            h_msg_txt = j.get("h_msg_txt", None)
            matched_error = []
            for error in (NoResultsError, NeedToLoginError, SoldOutError):
                if h_msg_cd in error.codes:
                    matched_error.append(error)
            if matched_error:
                raise matched_error[0](h_msg_cd)
            else:
                raise KorailError(h_msg_txt, h_msg_cd)
        else:
            return True

    def search_train_allday(
        self,
        dep,
        arr,
        date=None,
        time=None,
        train_type=TrainType.ALL,
        passengers=None,
        available_only=False,
    ):
        min1 = timedelta(minutes=1)
        all_trains = []
        last_time = time
        for i in range(15):
            try:
                trains = self.search_train(
                    dep, arr, date, last_time, train_type, passengers, True
                )
                all_trains.extend(trains)
                t = datetime.strptime(all_trains[-1].dep_time, "%H%M%S") + min1
                last_time = t.strftime("%H%M%S")
            except NoResultsError:
                break

        if available_only:
            all_trains = list(filter(lambda x: x.seat_available(), all_trains))

        if len(all_trains) == 0:
            print("No results")

        # # 기차 정보 출력에 번호 추가
        # for index, train in enumerate(all_trains, start=1):
        #     print(f"{index:02d}. {train}")

        return all_trains


    def search_train(
        self,
        dep,
        arr,
        date=None,
        time=None,
        train_type=TrainType.ALL,
        passengers=None,
        available_only=False,
    ):
        kst = timezone(timedelta(hours=9))
        if date is None:
            date = datetime.utcnow().astimezone(kst).strftime("%Y%m%d")
        if time is None:
            time = datetime.utcnow().astimezone(kst).strftime("%H%M%S")

        if passengers is None:
            passengers = [AdultPassenger()]

        passengers = Passenger.reduce(passengers)

        adult_count = reduce(
            lambda a, b: a + b.count,
            list(filter(lambda x: isinstance(x, AdultPassenger), passengers)),
            0,
        )
        child_count = reduce(
            lambda a, b: a + b.count,
            list(filter(lambda x: isinstance(x, ChildPassenger), passengers)),
            0,
        )
        senior_count = reduce(
            lambda a, b: a + b.count,
            list(filter(lambda x: isinstance(x, SeniorPassenger), passengers)),
            0,
        )

        url = KORAIL_URLS["search_schedule"]
        data = {
            "Device": self._device,
            "radJobId": "1",
            "selGoTrain": train_type,
            "txtCardPsgCnt": "0",
            "txtGdNo": "",
            "txtGoAbrdDt": date,  # '20140803',
            "txtGoEnd": arr,
            "txtGoHour": time,  # '071500',
            "txtGoStart": dep,
            "txtJobDv": "",
            "txtMenuId": "11",
            "txtPsgFlg_1": adult_count,  # 어른
            "txtPsgFlg_2": child_count,  # 어린이
            "txtPsgFlg_3": senior_count,  # 경로
            "txtPsgFlg_4": "0",  # 장애인1
            "txtPsgFlg_5": "0",  # 장애인2
            "txtSeatAttCd_2": "000",
            "txtSeatAttCd_3": "000",
            "txtSeatAttCd_4": "015",
            "txtTrnGpCd": train_type,
            "Version": self._version,
        }

        r = self._session.get(url, params=data)
        j = json.loads(r.text)

        try:
            if self._result_check(j):
                train_infos = j["trn_infos"]["trn_info"]
                # print("표조회결과: ", train_infos)
                trains = []

                for info in train_infos:
                    print(info)
                    trains.append(Train(info))

                if available_only:
                    trains = list(filter(lambda x: x.seat_available(), trains))

                if len(trains) == 0:
                    print("No results found.")

                return trains
        except KorailError as error:
            print(f"기차 검색에 실패하였습니다. 원인: {error}")
            return []


    def reserve(self, train, passengers=None, option=ReserveOption.GENERAL_FIRST):
        seat_type = None
        if train.seat_available() is False:
            raise SoldOutError()
        elif option == ReserveOption.GENERAL_ONLY:
            if train.general_seat_available():
                seat_type = "1"
            else:
                raise SoldOutError()
        elif option == ReserveOption.SPECIAL_ONLY:
            if train.special_seat_available():
                seat_type = "2"
            else:
                raise SoldOutError()
        elif option == ReserveOption.GENERAL_FIRST:
            if train.general_seat_available():
                seat_type = "1"
            else:
                seat_type = "2"
        elif option == ReserveOption.SPECIAL_FIRST:
            if train.special_seat_available():
                seat_type = "2"
            else:
                seat_type = "1"

        if passengers is None:
            passengers = [AdultPassenger()]

        passengers = Passenger.reduce(passengers)
        cnt = reduce(lambda x, y: x + y.count, passengers, 0)
        url = KORAIL_URLS["ticket_reservation"]
        data = {
            "Device": self._device,
            "Version": self._version,
            "Key": self._key,
            "txtGdNo": "",
            "txtJobId": "1101",
            "txtTotPsgCnt": cnt,
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            "txtSeatAttCd4": "015",
            "txtSeatAttCd5": "000",
            "hidFreeFlg": "N",
            "txtStndFlg": "N",
            "txtMenuId": "11",
            "txtSrcarCnt": "0",
            "txtJrnyCnt": "1",
            # 이하 여정정보1
            "txtJrnySqno1": "001",
            "txtJrnyTpCd1": "11",
            "txtDptDt1": train.dep_date,
            "txtDptRsStnCd1": train.dep_code,
            "txtDptTm1": train.dep_time,
            "txtArvRsStnCd1": train.arr_code,
            "txtTrnNo1": train.train_number,
            "txtRunDt1": train.run_date,
            "txtTrnClsfCd1": train.train_type,
            "txtPsrmClCd1": seat_type,
            "txtTrnGpCd1": train.train_group,
            "txtChgFlg1": "",
            # 이하 여정정보2
            "txtJrnySqno2": "",
            "txtJrnyTpCd2": "",
            "txtDptDt2": "",
            "txtDptRsStnCd2": "",
            "txtDptTm2": "",
            "txtArvRsStnCd2": "",
            "txtTrnNo2": "",
            "txtRunDt2": "",
            "txtTrnClsfCd2": "",
            "txtPsrmClCd2": "",
            "txtChgFlg2": "",
            # 이하 txtTotPsgCnt 만큼 반복
            # 'txtPsgTpCd1'    : '1',   #손님 종류 (어른, 어린이)
            # 'txtDiscKndCd1'  : '000', #할인 타입 (경로, 동반유아, 군장병 등..)
            # 'txtCompaCnt1'   : '1',   #인원수
            # 'txtCardCode_1'  : '',
            # 'txtCardNo_1'    : '',
            # 'txtCardPw_1'    : '',
        }

        index = 1
        for psg in passengers:
            data.update(psg.get_dict(index))
            index += 1

        r = self._session.get(url, params=data)
        j = json.loads(r.text)
        if self._result_check(j):
            rsv_id = j["h_pnr_no"]
            rsvlist = list(filter(lambda x: x.rsv_id == rsv_id, self.reservations()))
            if len(rsvlist) == 1:
                return rsvlist[0]

    def tickets(self):
        url = KORAIL_URLS["my_ticket_list"]
        data = {
            "Device": self._device,
            "Version": self._version,
            "Key": self._key,
            "txtIndex": "1",
            "h_page_no": "1",
            "txtDeviceId": "",
            "h_abrd_dt_from": "",
            "h_abrd_dt_to": "",
        }

        r = self._session.get(url, params=data)
        j = json.loads(r.text)
        try:
            if self._result_check(j):
                ticket_infos = j["reservation_list"]

                tickets = []

                for info in ticket_infos:
                    ticket = Ticket(info)
                    url = KORAIL_URLS["my_ticket_seat"]
                    data = {
                        "Device": self._device,
                        "Version": self._version,
                        "Key": self._key,
                        "h_orgtk_wct_no": ticket.sale_info1,
                        "h_orgtk_ret_sale_dt": ticket.sale_info2,
                        "h_orgtk_sale_sqno": ticket.sale_info3,
                        "h_orgtk_ret_pwd": ticket.sale_info4,
                    }
                    r = self._session.get(url, params=data)
                    j = json.loads(r.text)
                    if self._result_check(j):
                        seat = j["ticket_infos"]["ticket_info"][0]["tk_seat_info"][0]
                        ticket.seat_no = seat["h_seat_no"]
                        ticket.seat_no_end = None

                    tickets.append(ticket)

                return tickets
        except NoResultsError:
            return []


    def reservations(self):
        url = KORAIL_URLS["my_reservation_list"]
        data = {
            "Device": self._device,
            "Version": self._version,
            "Key": self._key,
        }
        r = self._session.get(url, params=data)
        j = json.loads(r.text)
        try:
            if self._result_check(j):
                rsv_infos = j["jrny_infos"]["jrny_info"]

                reserves = []

                for info in rsv_infos:
                    for tinfo in info["train_infos"]["train_info"]:
                        reserves.append(Reservation(tinfo))
                return reserves
        except NoResultsError:
            return []

    def cancel(self, rsv):
        assert isinstance(rsv, Reservation)
        url = KORAIL_URLS["cancel"]
        data = {
            "Device": self._device,
            "Version": self._version,
            "Key": self._key,
            "txtPnrNo": rsv.rsv_id,
            "txtJrnySqno": rsv.journey_no,
            "txtJrnyCnt": rsv.journey_cnt,
            "hidRsvChgNo": rsv.rsv_chg_no,
        }
        r = self._session.get(url, data=data)
        j = json.loads(r.text)
        if self._result_check(j):
            return True
