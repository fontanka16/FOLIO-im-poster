import json
import sys
import requests
import time
from random import randint


def getFOLIOInstanceId(oldId):
    if oldInstanceId in instanceIdMappings:
        return instanceIdMappings[oldId]
    else:
        instanceIdMappings[oldId] = lookupFOLIOInstanceId(oldId)
        return instanceIdMappings[oldId]


def lookupFOLIOInstanceId(oldId):
        path = "/instance-storage/instances"
        identifierTypeId = '7e591197-f335-4afb-bc6d-a6d76ca3bace'
        url = '?limit=2&query=identifiers == \"*\\\"value\\\": \\\"{}*\\\", \\\"identifierTypeId\\\": \\\"{}\\\"*\" sortby title'.format(oldId, identifierTypeId)
        req = requests.get(okapiUrl+path+url,
                           headers=okapiHeaders)
        folioInstanceId = json.loads(req.text)['instances'][0]['id']
        return folioInstanceId


def deleteItem(itemId):
    print('deleteing item record')
    path = '/items-storage/temss/{0}'.format(itemId)
    req = requests.delete(okapiUrl+path, headers=okapiHeaders)


def deleteHolding(holdingId):
    print('deleteing holding record')
    path = '/holdings-storage/holdings/{0}'.format(holdingId)
    req = requests.delete(okapiUrl+path, headers=okapiHeaders)


def postItem(item):
    path = '/item-storage/items'
    req = requests.post(okapiUrl+path,
                        data=json.dumps(item),
                        headers=okapiHeaders)
    if req.status_code == 400 and 'already exists.' in req.text:
        deleteItem(item['id'])
        # TODO: take care of infinite loop
        postItem(item)


def postHolding(holding):
    path = '/holdings-storage/holdings'
    req = requests.post(okapiUrl+path,
                        data=json.dumps(holding),
                        headers=okapiHeaders)
    if req.status_code == 400 and 'already exists.' in req.text:
        deleteHolding(holding['id'])
        # TODO: take care of infinite loop
        postHolding(holding)


def myformat(x):
        return ('%.2f' % x).rstrip('0').rstrip('.')


# Main
print("Script starting")
locationIds = ['53cf956f-c1df-410b-8bea-27f712cca7c0',
               'fcd64ce1-6995-48f0-840e-89ffa2288371',
               '758258bc-ecc1-41b8-abca-f7b610822ffd',
               'b241764c-1466-4e1d-a028-1a3684a5da87',
               'f34d27c6-a8eb-461b-acd6-5dea81771e70']

start = time.time()

print('Will post data to')

okapiUrl = sys.argv[3]
print("\tOkapi URL:\t", okapiUrl)

tenantId = sys.argv[4]
print("\tTenanti Id:\t", tenantId)

okapiToken = sys.argv[5]
print("\tToken:   \t", okapiToken)

print("Opening file", sys.argv[2])
i = 0
url = ""
instanceIdMappings = {}
lookups = 0
cacheHits = 0
okapiHeaders = {'x-okapi-token': okapiToken,
                'x-okapi-tenant': tenantId,
                'content-type': 'application/json'}

if sys.argv[1] in ['holdings', 'holding', 'hold']:
    with open(sys.argv[2]) as f:
        for line in f:
            try:
                i += 1
                # lookup the FOLIO id of the bib record
                holding = json.loads(line)
                oldInstanceId = holding["instanceId"]
                holding["instanceId"] = getFOLIOInstanceId(oldInstanceId)
                holding['permanentLocationId'] = locationIds[randint(0, 4)]
                postHolding(holding)
                if i % 100 == 0:
                    print(holding)
                    elapsed = myformat(i/(time.time() - start))
                    printTemplate = "Records/second: {}\tTot. Holdings: {}"
                    print(printTemplate.format(elapsed, i))
            except Exception as inst:
                print(type(inst))
                print(inst.args)
                print(inst)
elif sys.argv[1] in ['items', 'item']:
    with open(sys.argv[2]) as f:
        for line in f:
            item = json.loads(line)
            i += 1
            postItem(item)
            if i % 10000 == 0:
                elapsed = myformat(i/(time.time() - start))
                printTemplate = "Records/second: {}\tTot. Items: {}"
                print(printTemplate.format(elapsed, i))
print("Script finished")
