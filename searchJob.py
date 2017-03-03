# -*- coding:utf-8 -*-

import requests
# from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from urllib.parse import urlencode
import csv
import re
import time

def getPage(keyWord, currentPage):
	firstPart = "http://search.51job.com/jobsearch/search_result.php?fromJs=1&jobarea=080200%2C00&district=000000&funtype=0000&industrytype=00&issuedate=9&providesalary=99&"
	secondPart = "&keywordtype=2&"
	thirdPart = "&lang=c&stype=1&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&lonlat=0%2C0&radius=-1&ord_field=0&list_type=0&fromType=14&dibiaoid=0&confirmdate=9"
	newPage = urlencode({"curr_page":currentPage})
	startPage = firstPart + keyWord + secondPart + newPage + thirdPart
	return startPage
	
def getInfo(link, user_agent):
	try:
		html = requests.get(link, headers = user_agent)
	except:
		return False
	html.encoding = 'gb2312'
	htmlContent = html.content
	bsObj = BeautifulSoup(htmlContent,"html.parser")
	
	if bsObj.find("body").find("div",{"class":"tCompany_center clearfix"}).find("div",{"id":"tHeader_mk"}) is None:
		return None
	#headerInfo
	headerInfo = bsObj.find("body").find("div",{"class":"tCompany_center clearfix"}).find("div",{"class":["tHeader tHjob","tHeader tHjob fix"]}).find("div",{"class":"in"}).find("div",{"class":"cn"})
	positionName = headerInfo.find("h1")['title']
	location = headerInfo.find("span").get_text()
	salary = headerInfo.find("strong").get_text()
	companyName = headerInfo.find("p",{"class":"cname"}).find("a")['title']
	companyInfo = headerInfo.find("p",{"class":"msg ltype"}).get_text()
	companyInfo = companyInfo.replace('\t','').replace('\r','').replace('\n','').replace(' ','') # \t 水平tab，\r 回车，\n 换行
	#bodyInfo
	bodyInfo = bsObj.find("body").find("div",{"class":"tCompany_center clearfix"}).find("div",{"class":"tCompany_main"}).find("div",{"class":"bmsg job_msg inbox"})
	positionInfo = bodyInfo.get_text()
	extra_span = bodyInfo.find("span").get_text()
	if bodyInfo.find("div",{"class":"mt10"}) is not None:
		extra_div = bodyInfo.find("div",{"class":"mt10"}).get_text()
		mark = True
	else:
		extra_div = ''
		mark = False
	extra_a1 = "分享" # bodyInfo.find("a",{"class":"icon_b i_share"}).get_text()
	extra_a2 = "举报" # bodyInfo.find("a",{"class":"icon_b i_note"}).get_text()
	positionInfo = positionInfo.replace(extra_span,'').replace(extra_div,'').replace(extra_a1,'').replace(extra_a2,'').replace('\t','').replace('\r','').replace('\n','')
	positionInfoList = re.split('[；。！]', positionInfo)
	#bodyEnd
	classification = ''
	keyWord = ''
	if mark == True:
		bodyEnd = bodyInfo.find("div",{"class":"mt10"}).findAll("p",{"class":"fp f2"})
		pNum = len(bodyEnd)
		if pNum != 0:	
			for span in bodyEnd[0].findAll("span",{"class":"el"}):
				classification = classification + span.get_text() + ' '
			if pNum > 1:	
				for span in bodyEnd[1].findAll("span",{"class":"el"}):
					keyWord = keyWord + span.get_text() + ' '
	#hiringInfo
	hiringInfo = bsObj.find("body").find("div",{"class":"tCompany_center clearfix"}).find("div",{"class":"tCompany_main"}).find("div",{"class":"jtag inbox"})
	companyWelfare = []
	if hiringInfo.find("p",{"class":"t2"}) is not None:
		if hiringInfo.find("p",{"class":"t2"}).find("span") is not None:
			for span in hiringInfo.find("p",{"class":"t2"}).findAll("span"):
				companyWelfare.append(span.get_text())
	experience = ''
	education = ''
	hiringNumber = ''
	issueDate = ''
	if hiringInfo.find("em",{"class":"i1"}) is not None:
		experience = hiringInfo.find("em",{"class":"i1"}).parent.get_text()
	if hiringInfo.find("em",{"class":"i2"}) is not None:
		education = hiringInfo.find("em",{"class":"i2"}).parent.get_text()
	if hiringInfo.find("em",{"class":"i3"}) is not None:
		hiringNumber = hiringInfo.find("em",{"class":"i3"}).parent.get_text()
	if hiringInfo.find("em",{"class":"i4"}) is not None:
		issueDate = hiringInfo.find("em",{"class":"i4"}).parent.get_text()
	
	writer.writerow((positionName,location,salary,companyName,companyInfo,positionInfoList,classification,keyWord,companyWelfare,experience,education,hiringNumber,issueDate))
	return True

def getLinks(startPage, user_agent):
	links = []
	html = requests.get(startPage, headers = user_agent).content
	bsObj = BeautifulSoup(html,"html.parser")
	for tag in bsObj.find("body").find("div",{"class":"dw_table"}).findAll("p",{"class":["t1 ","t1 tg"]}):
		if tag is None:
			return None
		try:
			if tag.find("span").find("a",href=re.compile("^(http://jobs).*$")) is not None:
				link = tag.span.a['href']
				if link not in links:
					#print(link)
					links.append(link)
		except:
			print("not found subTag or href")
	return links

	
user_agent = { 'Connection':'keep-alive',
			   'Accept': 'text/html, */*; q=0.01',
			   'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
			  }

keyWord = input("Please input the key word: ")
search = urlencode({"keyword": keyWord})


startFrom = input("Start page : ")
startFrom = int(startFrom)
lastPage = input("End page : ")

records = 0

csvFile = open("jobInfo.csv", 'wt', encoding = 'utf-8') 
try:
	writer = csv.writer(csvFile)
	writer.writerow(("职位名称","地区","薪资","公司名称","公司简介","职位信息","职能类别","关键字","公司福利","工作经验","学历","招聘人数","发布时间"))
	print('--------------START--------------')
	while startFrom <= int(lastPage):
		print("page %d" %startFrom)
		startPage = getPage(search, startFrom)
		links = getLinks(startPage, user_agent)
		if links is None:
			print('--------------- The End ------------------')
		else:
			print("   There are %d records " %len(links))
			records = records + len(links)
			for link in links:
				boolean = getInfo(link, user_agent)
				if boolean is False:
					print("some errors happen when opening: "+ link)
				if boolean is None:
					print("Not find any information, maybe this position is out of date")
					records -= 1
			startFrom += 1
			print("wait for 2 seconds")
			time.sleep(2)
	print('The number of all useful records is: %d' %records)
	print('---------------END---------------')
finally:
	csvFile.close()
