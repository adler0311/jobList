#-*- coding: utf-8 -*- 

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Announcement, Resume

engine = create_engine('sqlite:///joblistwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create Dummy Users
User1 = User(name="Robo Barista", email="xxxxxxxx.gmail.com")
session.add(User1)
session.commit()


announcement1 = Announcement(companyName="ebay korea", title=unicode("모집 공고"), position=unicode("풀스택"),\
							pageLink=unicode("없어"), dueDate=unicode("오늘마감"), payment="0", user_id=1)

session.add(announcement1)
session.commit()

resume1 = Resume(user_id=1, question=unicode("1. 이름이 뭐에요?"), answer=unicode("저는 나원호입니다."), announcement=announcement1)

session.add(resume1)
session.commit()

resume2 = Resume(user_id=1, question=unicode("2. 가장 좋아하는 술은?"), answer=unicode("와인"), announcement=announcement1)

session.add(resume2)
session.commit()

resume3 = Resume(user_id=1, question=unicode("3. 하루 공부 시간은?"), answer=unicode("6~7시간"), announcement=announcement1)

session.add(resume3)
session.commit()


resume4 = Resume(user_id=1, question=unicode("4. 왜 반말 하심?"), answer=unicode("귀찮음"), announcement=announcement1)

session.add(resume4)
session.commit()


announcement2 = Announcement(companyName="samsung", title=unicode("모집 공고"), position=unicode("풀스택"),\
							pageLink=unicode("없어"), dueDate=unicode("오늘마감"), payment="0", user_id=1)

session.add(announcement2)
session.commit()

resume1 = Resume(user_id=1, question=unicode("1. 이름이 뭐에요?"), answer=unicode("나원호2요."), announcement=announcement2)

session.add(resume1)
session.commit()

resume2 = Resume(user_id=1, question=unicode("2. 뭐 먹고 싶어요?"), answer=unicode("삼겹살"), announcement=announcement2)

session.add(resume2)
session.commit()

resume3 = Resume(user_id=1, question=unicode("3. 하루 자는 시간은?"), answer=unicode("6에서 7시간"), announcement=announcement2)

session.add(resume3)
session.commit()


resume4 = Resume(user_id=1, question=unicode("4. 왜 반말 하심?"), answer=unicode("귀찮음"), announcement=announcement2)

session.add(resume4)
session.commit()


announcement3 = Announcement(companyName="NHN", title=unicode("모집 공고"), position=unicode("풀스택"), \
							pageLink=unicode("없어"), dueDate=unicode("오늘마감"), payment="0", user_id=1)

session.add(announcement3)
session.commit()

resume1 = Resume(user_id=1, question=unicode("1. 사는 곳은?"), answer=unicode("신촌."), announcement=announcement3)

session.add(resume1)
session.commit()

resume2 = Resume(user_id=1, question=unicode("2. 여행어디 가고 싶어요?"), answer=unicode("이탈리아"), announcement=announcement3)

session.add(resume2)
session.commit()

resume3 = Resume(user_id=1, question=unicode("3. 지금 있는 곳은?"), answer=unicode("스타벅스"), announcement=announcement3)

session.add(resume3)
session.commit()


resume4 = Resume(user_id=1, question=unicode("4. 자동차? 아님 집?"), answer=unicode("집"), announcement=announcement3)

session.add(resume4)
session.commit()

print "added menu items!"
