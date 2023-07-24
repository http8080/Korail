import re
from enum import Enum
from typing import Dict, Pattern

class InputFlag(Enum):
    MEMBERSHIP_NUMBER = "2"
    PHONE_NUMBER = "4"
    EMAIL = "5"

class SeatAttribute(Enum):
    DEFAULT = "000"
    RESERVED = "015"

SCHEME = "https"
KORAIL_HOST = "smart.letskorail.com"
KORAIL_PORT = "443"

KORAIL_DOMAIN = f"{SCHEME}://{KORAIL_HOST}:{KORAIL_PORT}"
KORAIL_MOBILE = f"{KORAIL_DOMAIN}/classes/com.korail.mobile"

EMAIL_REGEX: Pattern[str] = re.compile(r"[^@]+@[^@]+\.[^@]+")
PHONE_NUMBER_REGEX: Pattern[str] = re.compile(r"(\d{3})-(\d{3,4})-(\d{4})")

KORAIL_URLS: Dict[str, str] = {
    "login": f"{KORAIL_MOBILE}.login.Login",
    "logout": f"{KORAIL_MOBILE}.common.logout",
    "search_schedule": f"{KORAIL_MOBILE}.seatMovie.ScheduleView",
    "ticket_reservation": f"{KORAIL_MOBILE}.certification.TicketReservation",
    "refund": f"{KORAIL_MOBILE}.refunds.RefundsRequest",
    "my_ticket_list": f"{KORAIL_MOBILE}.myTicket.MyTicketList",
    "my_ticket_seat": f"{KORAIL_MOBILE}.refunds.SelTicketInfo",
    "my_reservation_list": f"{KORAIL_MOBILE}.reservation.ReservationView",
    "cancel": f"{KORAIL_MOBILE}.reservationCancel.ReservationCancelChk",
    "station_db": f"{KORAIL_MOBILE}.common.stationinfo?device=ip",
    "station_db_data": f"{KORAIL_MOBILE}.common.stationdata",
    "event": f"{KORAIL_MOBILE}.common.event",
    "payment": f"{KORAIL_DOMAIN}/ebizmw/PrdPkgMainList.do",
    "payment_voucher": f"{KORAIL_DOMAIN}/ebizmw/PrdPkgBoucherView.do",
}

DEFAULT_USER_AGENT: str = "Dalvik/2.1.0 (Linux; U; Android 5.1.1; Nexus 4 Build/LMY48T)"
