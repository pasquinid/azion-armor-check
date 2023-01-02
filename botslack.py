import slack_sdk
import time
from slack_sdk import WebClient
# from slack.errors import SlackApiError


class Slack:
    def __init__(self,channel,token):
        self.channel = channel
        self.token   = token
        self.client  = WebClient(token=self.token)

    def sendMessage(self,text):
        self.client.chat_postMessage(channel=self.channel,text=text)


    def processResults(self,results,gcpCtl):
        print(results)
        
        if results == {}:
            self.sendMessage("Não encontrei policies desatualizadas.")

        for project in results: 
            for policy in results[project]: 
                text='*========================================================================================*\n*Projeto:* '+project+'\n*Policy:* '+policy+'\n*Faltam os ips: *'
                arrangedIps = gcpCtl.arrangeIps(results[project][policy]['ADICIONAR'])
                for num in arrangedIps:
                    text = text + "   - " + arrangedIps[num] + "\n"

                #+str(results[project][policy]['ADICIONAR'])+'\n*========================================================================================*\n\n'
                self.sendMessage(text)
                time.sleep(2)


