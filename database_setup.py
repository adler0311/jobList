from sqlalchemy import Column, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key=True)
	name = Column(String(250), nullable=False)
	email = Column(String(250), nullable=False)
	picture = Column(String(250))
	

class Announcement(Base):
	__tablename__ = 'announcement'

	id = Column(Integer, primary_key=True)
	companyName = Column(String(250), nullable=False)
	title = Column(String(250), nullable=False)
	position = Column(String(250), nullable=False)
	pageLink = Column(String(250))
	dueDate = Column(String(250))
	payment = Column(Integer)
	additional = Column(String(250))
	switch = Column(Boolean, unique=False, default = True)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)


class Resume(Base):
	__tablename__ = 'resume'

	id = Column(Integer, primary_key=True)
	question = Column(String(250), nullable=False)
	answer = Column(Text)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)
	announcement_id = Column(Integer, ForeignKey('announcement.id'))
	announcement = relationship(Announcement)


engine = create_engine('sqlite:///joblistwithusers.db')
Base.metadata.create_all(engine)