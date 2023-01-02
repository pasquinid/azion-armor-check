import googleapiclient.discovery
from oauth2client.client import GoogleCredentials
import time
from datetime import datetime

class GCP:
    def __init__(self,targetAzionPolicy,maxNumberOfIpsPerRule):
        self.projects = []
        #self.credentials = GoogleCredentials.get_application_default()
        self.compute     = googleapiclient.discovery.build('compute', 'v1')#,credentials=self.credentials)
        self.resourcemng = googleapiclient.discovery.build('cloudresourcemanager', 'v1')#,credentials=self.credentials)
        self.targetAzionPolicy = targetAzionPolicy
        self.maxNumberOfIpsPerRule = maxNumberOfIpsPerRule

    def listArmorPolicyRules(self,projectId,policyName):
        return self.compute.securityPolicies().get(project=projectId,securityPolicy=policyName).execute()["rules"]

    def isProjectUpdatable(self,projectId):
        try:
            self.compute.securityPolicies().list(project=projectId).execute()['items']
            return True
        except:
            return False 

    def filterProjectIds(self,response,currentIds):
        for project in response['projects']:
                currentIds.append(project['projectId'])
        return currentIds

    def setProjectList(self):
        print("Searching for the current project list...")
        requestList = self.resourcemng.projects().list()
        print("...wait for it...")
        response = requestList.execute()
        print("...wait more for it...")
        print(response)
        self.projects = []
        
        while 'nextPageToken' in  response:
            self.projects = self.filterProjectIds(response,self.projects)
            response = self.resourcemng.projects().list(pageToken=response['nextPageToken']).execute()
            print("...wait a bit more for it...")
        
        self.projects = self.filterProjectIds(response,self.projects)

        
        print ("and finally done!")
    
    def arrangeIps(self,validIps):
        arrangedIps = {}
        count = 0
        rulesCount = 0
        arrangedIps[0] = []

        for ip in validIps:
            if count >= self.maxNumberOfIpsPerRule:
                rulesCount = rulesCount + 1
                arrangedIps[rulesCount] = []
                count = 0
            arrangedIps[rulesCount].append(ip)
            count = count+1
            
        for num in arrangedIps:
            arrangedIps[num] = str(arrangedIps[num]).replace("'","").replace("[","").replace("]","").replace(" ","")

        return arrangedIps
        

    def updateProjects(self,validIps):
        print("Lookup inside the gcp projects has began!!...")
        #self.setProjectList()
        self.projects.append('careful-lock-236718')
        results = {}
        print("...wait for me to look inside every one of them...")
        for project in self.projects : 
            print('...looking inside project '+project)
            if self.isProjectUpdatable(project):
                policies = self.compute.securityPolicies().list(project=project).execute()['items']
                if project == 'careful-lock-236718':
                    rules = self.listArmorPolicyRules(project,'vortex-policy')
                    currentIps = []

                    for rule in rules:
                        if not 'config' in rule['match']:
                            continue                            
                        currentIps = currentIps + rule['match']['config']['srcIpRanges']     

                        newIps = []+list(set(validIps) - set(currentIps))
                        #outdatedIps = []+list(set(currentIps) - set(validIps))
                        
                    if len(newIps) == 0:
                        continue
                    
                    if not project in results:
                        print("==> Adding project "+project+" to result...")
                        results[project] = {} 


                    print("==>> Adding policy "+'vortex-policy'+" to result inside the project "+project)
                    results[project]['vortex-policy'] = {
                            'ADICIONAR' : newIps,
                            'REMOVER' : []#outdatedIps
                    }
                    print(results[project])                                                              
                else:
                    for policy in policies:
                        if ( policy['name'] == 'default' or 'azion' in policy['name'] or 'prd-default' == policy['name'] or 'hml-default' == policy['name']) and not 'azion-dynamic' in policy['name']:
                        #if policy['name'] == 'azion' :  
                            rules = self.listArmorPolicyRules(project,policy['name'])
                            currentIps = []

                            for rule in rules:
                                if not 'config' in rule['match']:
                                    continue                            
                                currentIps = currentIps + rule['match']['config']['srcIpRanges']
                                #if 'azion' in rule['description'].lower():
                                #    currentIps = currentIps + rule['match']['config']['srcIpRanges']
                                    
                            newIps = []+list(set(validIps) - set(currentIps))
                            #outdatedIps = []+list(set(currentIps) - set(validIps))
                            
                            if len(newIps) == 0:
                                continue
                            
                            if not project in results:
                                print("==> Adding project "+project+" to result...")
                                results[project] = {}
                            #         policy['name'] : {
                            #             'ADICIONAR' : newIps,
                            #             'REMOVER' : []#outdatedIps
                            #         }
                            #     }
                            # else:
                            print("==>> Adding policy "+policy['name']+" to result inside the project "+project)
                            results[project][policy['name']] = {
                                    'ADICIONAR' : newIps,
                                    'REMOVER' : []#outdatedIps
                            }
                            print(results[project])

        print("Lookup inside the projects has finished!!")
        return results              

    def sortRulesByPriority(self,rules):
        priorities = []
        newRules  = []
        for rule in rules:
            priorities.append(rule['priority'])
        priorities.sort()
        
        while len(newRules) < len(rules):
            for rule in rules:
                if rule['priority'] == priorities[0] :
                    newRules.append(rule)
                    priorities.pop(0)
                    break
        
        return newRules

    def getMaxPriority(self,rules,limit):
        max = 1
        for rule in rules:
            if not rule['priority'] > limit:
                max = rule['priority']
        
        return max

    def checkIfPriorityExists(self,rules,priority):
        for rule in rules:
            if rule['priority'] == priority:
                return True
        return False

    def checkNewIps(self,newRuleIps,policy):
        for rule in policy['rules']:
            if not 'deny' in rule['action']:
                try:
                    if newRuleIps == rule['match']['config']['srcIpRanges']:
                        return False
                except:
                    continue
        return True


    def appendNewRules(self,results,ruleDescription):

        retryCommands = []
        now = datetime.now().strftime("%b%d%Y%H%M%S")

        for project in results:
            for policy in results[project]:
                print("Listing rules from policy "+policy+" in project "+project+" ")
                while True:
                    try:
                        currentPolicy = self.compute.securityPolicies().get(project=project,securityPolicy=policy).execute()
                    except:
                        print("Error listing policies in project "+project)
                        time.sleep(5)
                        continue
                    break
                
                currentPolicy['rules'] = self.sortRulesByPriority(currentPolicy['rules'])
                                                                        
                maxPriority = self.getMaxPriority(currentPolicy['rules'],200000000)
                
                arrangedIps = self.arrangeIps(results[project][policy]['ADICIONAR'])
                numberOfRulesNeeded = len(arrangedIps)

                print(arrangedIps)
                print(numberOfRulesNeeded)

                rulesWrited=0
                
                for priority in list(range(maxPriority+1,maxPriority+numberOfRulesNeeded+1)):
                    if not self.checkIfPriorityExists(currentPolicy['rules'],priority):
                        ruletemplate = {
                            "description": ruleDescription+" "+now+" "+str(priority),
                            "priority": ""+str(priority),
                            "match":{
                                "versionedExpr":"SRC_IPS_V1",
                                "config":{
                                    "srcIpRanges": arrangedIps[rulesWrited].split(',')
                                }
                            },
                            "action":"allow",
                            "preview":False,
                            "kind":"compute#securityPolicyRule"
                        }
                        
                        
                        if self.checkNewIps(arrangedIps[rulesWrited],currentPolicy):
                            
                            try:
                                print("Adding rule: "+ str(priority)+"\n"+str(ruletemplate))
                                self.compute.securityPolicies().addRule(project=project,securityPolicy=policy,body=ruletemplate).execute()
                            except:
                                print("<(<( Erro ao escrever a regra acima no projeto "+project+" )>)>")
                                retryCommands.append("gcloud compute security-policies rules create "+str(priority)+" --security-policy "+policy+" --description \""+ruleDescription+" "+str(priority)+"\" --src-ip-ranges "+str(arrangedIps[rulesWrited]).replace("[","").replace("]","").replace("'","\"").replace(" ","")+" --action \"allow\" --project "+project+" \n")
                                
                        else:
                            print("+_+_+_    Ips are already in the policy "+policy['policy']+" in project "+project+"  _+_+_+")

                        rulesWrited = rulesWrited + 1

        return retryCommands

