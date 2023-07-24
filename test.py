from Korail.Korail import Korail

# Korail 클래스의 인스턴스 생성 (Korail 계정과 비밀번호가 필요합니다)
korail = Korail("------------------", "-------------------")

# 기차 검색 (출발지, 도착지, 날짜, 시간)
trains = korail.search_train('서울', '부산', '20230630', '150000',available_only=False)

# 결과 출력
for train in trains:
    print(train)

# 예약하기 (예약하려는 기차, 승객 타입 및 인원이 담긴 passengers 리스트)
# reservation = korail.reserve(trains[3], passengers=None)

# 예약 내역 출력
# print(reservation)

# 예약 취소
# korail.cancel(reservation)
