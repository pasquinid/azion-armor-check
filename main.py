import re
import azion
import gcp
import botslack
import os

def main(arg):
    print("Its ON baby!")
    print("Starting Azion Controller..")
    azionCtl = azion.Azion('https://api.azionapi.net/tokens','https://api.azionapi.net/network_lists/187',os.environ.get('AZION_USERNAME'),os.environ.get('AZION_PASSWORD'))
    print("Starting GCP Controller..")
    gcpCtl = gcp.GCP('azion',10)
    print('GCP Controller initialized!!')
    print("Starting Slack Controller..")
    slackCtl = botslack.Slack('CHANNEL','TOKEN')
    print('Slack Controller initialized!!')
    print("Searching the latest azion shield ip list...")
    azionCtl.setValidIpList()
    print("Done!")
    print("Initializing search in every projects Amor Azion policies for discrepancies...")
    statusResult = gcpCtl.updateProjects(azionCtl.validIps)
    print("Done!")
    retryCommands= gcpCtl.appendNewRules(statusResult,"AzionBOT")
    
    #slackCtl.processResults(statusResult,gcpCtl)
    
    for command in retryCommands:
        slackCtl.sendMessage(command)
main(1)