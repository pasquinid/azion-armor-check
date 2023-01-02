import urllib.request
import base64
import json 

class Azion:
    def __init__(self,authUrl,networkListUrl,user,pswd):
        self.authUrl = authUrl
        self.ipListApiUrl = networkListUrl
        self.user = user 
        self.pswd = pswd
        print("Azion Controller initialized!")

    def authenticate(self):
        authString = self.user+":"+self.pswd
        hashedAuth = str(base64.b64encode(authString.encode("ascii")),"ascii")

        request = urllib.request.Request(self.authUrl, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json; version=3")
        request.add_header("Authorization", "Basic "+hashedAuth)
        response = urllib.request.urlopen(request).read()
        response_str = str(response)
        response_json = json.loads(response)

        self.authenticationToken = 'token ' + response_json['token']    

    def setValidIpList(self):

        self.authenticate()

        request = urllib.request.Request(self.ipListApiUrl, method="GET")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json; version=3")
        request.add_header("Authorization", self.authenticationToken)
        response = urllib.request.urlopen(request).read()
        self.validIps = json.loads(response)["results"]["items_values"]
    
    def sortValidIps(self):
        temporaryList = {}
        sortedIps = []

        for ip in self.validIps:
            temporaryList[int(ip.replace('.','').split('/')[0])] = ip

        sortedIds = sorted(temporaryList)

        for id in sortedIds:
            sortedIps.append(temporaryList[id])
        
        self.validIps = sortedIps