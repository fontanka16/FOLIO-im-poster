import json
import sys
import time
import multiprocessing
import requests
print("Script starting")

start = time.time()

print('Will post data to')

okapi_url = sys.argv[3]
print("\tOkapi URL:\t", okapi_url)

tenant_id = sys.argv[4]
print("\tTenanti Id:\t", tenant_id)

okapi_token = sys.argv[5]
print("\tToken:   \t", okapi_token)

print("Opening file", sys.argv[2])
myi = 0
i = 0
url = ""
instance_id_mappings = {}
lookups = 0
cache_hits = 0
okapi_headers = {'x-okapi-token': okapi_token,
                 'x-okapi-tenant': tenant_id,
                 'content-type': 'application/json'}


def get_folio_instance_id(old_id):
    if old_id in instance_id_mappings:
        print('cache hit!')
        return instance_id_mappings[old_id]
    else:
        instance_id_mappings[old_id] = lookup_folio_instance_id(old_id)
        return instance_id_mappings[old_id]


def lookup_folio_instance_id(old_id):
    path = "/instance-storage/instances"
    identifierTypeId = '7e591197-f335-4afb-bc6d-a6d76ca3bace'
    url = ('?limit=2&query=identifiers == \"*\\\"value\\\": \\\"{}*\\\",'
           '\\\"identifierTypeId\\\": \\\"{}\\\"*\" sortby'
           'title').format(old_id, identifierTypeId)
    req = requests.get(okapi_url+path+url,
                       headers=okapi_headers)
    folio_instance_id = json.loads(req.text)['instances'][0]['id']
    return folio_instance_id


def delete_item(item_id):
    path = '/items-storage/temss/{0}'.format(item_id)
    req = requests.delete(okapi_url+path, headers=okapi_headers)


def delete_instance(instance_id):
    path = '/instance-storage/instances/{0}'.format(instance_id)
    req = requests.delete(okapi_url+path, headers=okapi_headers)


def delete_holding(holding_id):
    path = '/holdings-storage/holdings/{0}'.format(holding_id)
    req = requests.delete(okapi_url+path, headers=okapi_headers)


def post_instance(instance):
    path = '/instance-storage/instances'
    try:
        req = requests.post(okapi_url+path,
                            data=json.dumps(instance),
                            headers=okapi_headers,
                            timeout=2)
        if req.status_code == 400 and 'already exists.' in req.text:
            delete_instance(instance['id'])
            # TODO: take care of infinite loop
            if post_instance(instance): 
                return True
        if req.status_code == 201:
            return True
        if 401 <= req.status_code <= 599:
            print("Error!")
            print("Code:\t{} Message:\t{}".format(req.status_code, req.text))
            print(instance)
            return False
    except Exception as e:
        print("ERROR!\ttype\t{} ID:\t{}".format(type(e), instance["id"]))
        return False


def post_item(item):
    path = '/item-storage/items'
    req = requests.post(okapi_url+path,
                        data=json.dumps(item),
                        headers=okapi_headers)
    if req.status_code == 400 and 'already exists.' in req.text:
        delete_item(item['id'])
        # TODO: take care of infinite loop
        post_item(item)
        print("Exists")


def post_holding(holding):
    path = '/holdings-storage/holdings'
    req = requests.post(okapi_url+path,
                        data=json.dumps(holding),
                        headers=okapi_headers)
    if req.status_code == 400 and 'already exists.' in req.text:
        delete_holding(holding['id'])
        # TODO: take care of infinite loop
        post_holding(holding)


def myformat(x):
        return ('%.2f' % x).rstrip('0').rstrip('.')


def handle_holding(line):
    holding = json.loads(line)
    old_instance_id = holding["instance_id"]
    holding["instance_id"] = get_folio_instance_id(old_instance_id)
    post_holding(holding)


def handle_instance(line):
    instance = json.loads(line)
    post_instance(instance)


def hadle_item(line):
    item = json.loads(line)
    post_item(item)


successful = 0
failed = 0
start = time.time()


def cb(result):
    global start
    global successful
    global failed
    if result:
        successful += 1
    else:
        failed += 1
#    if i % 10 == 0:
    elapsed = myformat((successful+failed)/(time.time() - start))
    print("r/s: {}\tFailed: {}\tSuccessful: {}".format(elapsed,
                                                       successful,
                                                       failed), end="\r")
    return successful


# Main
with multiprocessing.Pool(processes=1) as pool:
    if sys.argv[1] in ['holdings', 'holding', 'hold']:
        with open(sys.argv[2]) as f:
            pool.map(handle_holding,  f)
    elif sys.argv[1] in ['items', 'item']:
        with open(sys.argv[2]) as f:
            for line in f:
                pool.map(hadle_item, f)
    elif sys.argv[1] in ['bibs', 'bib', 'instance', 'instances']:
        with open(sys.argv[2]) as f:
            for line in f:
                cb(handle_instance(line))
                
print("Script finished")
