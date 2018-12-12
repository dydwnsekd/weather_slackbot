# -*- coding: utf-8 -*-

import os
import time
import re
from slackclient import SlackClient

import sys
import json
from datetime import datetime
from time import strftime
import requests
from bs4 import BeautifulSoup

class KmaCrawler:

    def __init__(self):
        self.server_url = "http://www.kma.go.kr/cgi-bin/aws/nph-aws_txt_min"
        self.text_list = ['high' ,'is_r', 'r15', 'rain', 'r6h', 'r12h',
                          'r1d', 'temp', 'w_360',
                          'w_dir', 'w_s', 'w10_360', 'w10_dir',
                          'w10_s', 'hum', 'atmo']


    def set_date(self, date):
        self.date = date
        self.server_url = '%s%s' % ('http://www.kma.go.kr/cgi-bin/aws/nph-aws_txt_min?', date)

        if date == '':
            self.date = datetime.now().strftime('%Y%m%d%H%M')


    def crawl(self, region):
        target = requests.get(self.server_url)
        target.encoding = 'euc-kr'
        target = target.text

        if region != None:
            self.region = unicode(region, 'utf-8')
            return self.parse(target)

        else:
            pass

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
        return_message = None

        for tr in tr_list[1:-3]:
            td_list = self.get_td_list(tr)

            kma_region = td_list[1]
            
            if kma_region != self.region:
                continue

            elif kma_region == self.region:
                result_dict = self.get_result_dict(td_list)
                return_message = result_dict
                #sys.stdout.write('%s \n' % json.dumps(result_dict))
                #sys.stdout.flush()
                break
        
        return return_message

    def result_pre(self, result_dict):
        response = '''
                    %s %s 날씨 기온 %s, 강수량 %s, 풍속 %s, 습도 %s 입니다.
                    ''' % (self.region, self.date, result_dict['temp'], result_dict['rain'], result_dict['w_s'], result_dict['hum'])

        return response

    def run(self, region, date=''):
        self.set_date(date)
        result_dict = self.crawl(region)

        if result_dict == None:
            return "지역을 찾을 수 없습니다."
        else:
            return self.result_pre(result_dict)
        


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
COMMAND = ("help", "weather")
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """

    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            print event["text"]
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    print (matches)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, kma_crawler):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith('help'):
        response = "'weather 지역 (날짜 YYYYmmddHHMM)'형식으로 입력해주세요"

    elif command.startswith('weather'):
        command_split = command.split(' ')

        if len(command_split) == 1:
            respones = "'weather 지역 (날짜 YYYYmmddHHMM)'형식으로 입력해주세요"
        elif len(command_split) == 2:
            response = kma_crawler.run(str(command_split[1]))
        elif len(command_split) > 2:
            response = kma_crawler.run(str(command_split[1]), command_split[2])

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )


if __name__ == "__main__":

    reload(sys)  
    sys.setdefaultencoding('utf8')

    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        kma_crawler = KmaCrawler()
        print (starterbot_id)
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel, kma_crawler)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")


