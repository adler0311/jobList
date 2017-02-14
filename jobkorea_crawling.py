#-*- coding: utf-8 -*- 

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from urllib2 import urlopen
from bs4 import BeautifulSoup
import re

def crawlCompanyList():
	companyList = []

	base = "http://www.jobkorea.co.kr/"
	html = urlopen(base+'starter/?schLocal=I000,B000&schPart=38888&schMajor=&schEduLevel=&schWork=&schCType=&isSaved=1&LinkGubun=0&LinkNo=0&Page=1&schOrderBy=0&schTxt=#divFilterContainer')
	bsObj = BeautifulSoup(html, 'html.parser')
	for el in bsObj.find('ul', {'class':'filterList'}).findAll('li'):
		name = el.find('a').get_text().encode('utf-8')
		titleElem = el.find('a', {'class':'link'})
		title = titleElem.get_text().encode('utf-8')
		link = titleElem['href']
		pos = el.find('div', {'class':'sTit'}).get_text().encode('utf-8')
		dueDate = el.find('span', {'class':'day'}).get_text().encode('utf-8')
		
		if "프로그래머" in pos:
			dict = {}
			if name[:3] == '\xe3\x88\x9c':
				
				dict['이름'] = name[3:]
			elif name[-3:] == '\xe3\x88\x9c':
				
				dict['이름']=name[:-3]
			else:
				
				dict['이름']=name
	#		print title
			dict['공고 제목'] = title
	#		print pos
			dict['직무'] = pos
	#		print link
			dict['공고 주소'] = base+link
	#		print dueDate
			dict['기한'] = dueDate
			companyList.append(dict)
	return companyList