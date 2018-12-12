# -*- coding: utf-8 -*-

import sys
import json
from datetime import datetime
from time import strftime
import requests
from bs4 import BeautifulSoup

class KmaCrawler:

    def __init__(self):
        self.server_url = "http://www.kma.go.kr/cgi-bin/aws/nph-aws_txt_min"
        self.text_list = ['강수여부', 'r15', '강수량', 'r6h', 'r12h',
                          'r1d', '기온', 'w_360',
                          'w_dir', '풍속', 'w10_360', 'w10_dir',
                          'w10_s', '습도', 'atmo']


    def set_date(self, date):
        self.server_url = '%s%s' % ('http://www.kma.go.kr/cgi-bin/aws/nph-aws_txt_min?', date)


    def crawl(self, region):
        target = requests.get(self.server_url)
        target.encoding = 'euc-kr'
        target = target.text

        if region != None:
            self.region = unicode(region, 'utf-8')
            self.parse(target)
        else:
            pass
            #print ("지역을 입력해주세요")

    def get_result_dict(self, td_list):

        result_dict = {'%s' % (text): td_list[
            idx + 3] for idx, text in enumerate(self.text_list)}

        return result_dict

    def get_tr_list(self, html):
        soup = BeautifulSoup(html, "html.parser")
        tr_list = soup.find_all('tr')
        return tr_list

    def get_td_list(self, tr):
        td_list = tr.find_all('td')
        td_list = [td.string.strip() for td in td_list[:-1]]
        td_list[3] = td_list[3] == u'●'
        return td_list

    def parse(self, html):

        tr_list = self.get_tr_list(html)

        for tr in tr_list[1:-3]:
            td_list = self.get_td_list(tr)

            kma_region = td_list[1]
            
            if kma_region != self.region:
                continue

            print ('성공')
            result_dict = self.get_result_dict(td_list)
            print (result_dict)
            sys.stdout.write('%s \n' % json.dumps(result_dict))
            sys.stdout.flush()

            break


    def run(self, region, date):
        #self.set_date(date)
        self.crawl(region)


if __name__ == "__main__":
    try:
        region = sys.argv[1]
        date = sys.argv[2]

        print (region)
        print (date)

        kma_crawler = KmaCrawler()
        kma_crawler.run(region, date)

    except Exception as ex:
        str(ex)
