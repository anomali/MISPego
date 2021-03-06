######################################################
# MISPego API miscellaneous functions.
#
# Author: Tom King (Based upon Emmanuel Bouillon's
# MISP_Maltego)
# Date: 09/03/2016
######################################################

from pymisp import PyMISP
from MaltegoTransform import *
from mispego_util import *
from datetime import datetime, timedelta
import shelve
import re

try:
    misp =  PyMISP(BASE_URL, API_KEY, MISP_VERIFYCERT, 'json', MISP_DEBUG)
except Exception as e:
    mt = MaltegoTransform()
    mt.addException("[Error] Cannot connect to MISP instance using %s with API key %s. Please check and try again" % (BASE_URL, API_KEY))
    mt.addException("[Error] %s" % e)
    mt.throwExceptions()

eventDB = "event.db"

def addDomain(domainValue):
    eid = checkAge()
    event = misp.get(eid)
    misp.add_domain(event, domainValue, to_ids=MISP_TO_IDS)
    returnSuccess("domain",domainValue,eid)

def addIP(ipValue):
    eid = checkAge()
    event = misp.get(eid)
    misp.add_ipdst(event, ipValue, to_ids=MISP_TO_IDS)
    returnSuccess("IP address",ipValue,eid)

def addEmail(emailValue):
    eid = checkAge()
    event = misp.get(eid)
    misp.add_email_src(event, emailValue, to_ids=MISP_TO_IDS)
    returnSuccess("email",emailValue,eid)

def addHash(hashValue):
    eid = checkAge()
    hashValue = hashValue.strip()
    md5 = re.compile(r'[0-9a-f]{32}$', flags = re.IGNORECASE)
    sha1= re.compile(r'[0-9a-f]{40}$', flags = re.IGNORECASE)
    sha256 = re.compile(r'[0-9a-f]{64}$', flags = re.IGNORECASE)
    event = misp.get(eid)
    if re.match(sha256, hashValue):
        hashType = "sha256"
        event = misp.add_hashes(event, sha256=hashValue, to_ids=MISP_TO_IDS)
    elif re.match(sha1, hashValue):
        hashType = "sha1"
        event = misp.add_hashes(event, sha1=hashValue, to_ids=MISP_TO_IDS)
    elif re.match(md5, hashValue):
        hashType = "md5"
        event = misp.add_hashes(event, md5=hashValue, to_ids=MISP_TO_IDS)
    else:
        returnFailure("hash", hashValue, "length of %s" % len(hashValue))
    returnSuccess("%s hash" % hashType,hashValue,eid)

def createEvent(eventName):
    mt = MaltegoTransform()
    mt.addUIMessage("[Info] Creating event with the name %s" % eventName)
    event = misp.new_event(MISP_DISTRIBUTION, MISP_THREAT, MISP_ANALYSIS, eventName,None,MISP_EVENT_PUBLISH)
    eid = event['Event']['id']
    einfo = event['Event']['info']
    eorgc = event['Event']['orgc_id']
    me = MaltegoEntity('maltego.MISPEvent',eid);
    me.addAdditionalFields('EventLink', 'EventLink', False, BASE_URL + '/events/view/' + eid )
    me.addAdditionalFields('Org', 'Org', False, eorgc)
    me.addAdditionalFields('notes', 'notes', False, eorgc + ": " + einfo)
    mt.addEntityToMessage(me);
    returnSuccess("event", eid, None, mt)

def selectEvent(eventID):
    s = shelve.open(eventDB)
    s['id'] = eventID
    s['age'] = datetime.today()
    s.close()
    mt = MaltegoTransform()
    mt.addUIMessage("[Info] Event with ID %s selected for insert" % eventID)
    mt.returnOutput()

def dataError(request):
    mt = MaltegoTransform()
    mt.addException("[Error] Failure to load function with name %s" % request)
    mt.throwExceptions()

def checkAge():
    s = shelve.open(eventDB)
    try:
        age = s['age']
        eid = s['id']
    except:
        age = datetime.today()-timedelta(seconds=6000)
        eid = "none"
    s.close()
    curDate = datetime.today()
    if age < curDate - timedelta(seconds=3600):
        mt = MaltegoTransform()
        mt.addException("[Warning] Selection of Event is over 1 hour old. Please reselect. Current selection: %s" % eid);
        mt.throwExceptions()
    else:
        return eid
def returnSuccess(etype,value,event=None, mt=None):
    if not mt:
        mt = MaltegoTransform()
    if event:
        mt.addUIMessage("[Info] Successful entry of %s with value %s into event %s" % (etype, value, event))
    else:
        mt.addUIMessage("[Info] Successful entry of %s with ID %s" % (etype, value))
    mt.returnOutput()

def returnFailure(etype, value, reason):
    mt = MaltegoTransform()
    mt.addException("[Error] Failed to add %s with value %s due to %s" % (etype, value, reason));
    mt.throwExceptions()

def main():
    request = sys.argv[0].split('_')[1][:-3]
    value = sys.argv[1]
    datatypes = {'createEvent':createEvent,'selectEvent':selectEvent,'addDomain':addDomain,
                'addIP':addIP,'addEmail':addEmail,'addHash':addHash}
    if request in datatypes:
        method = datatypes.get(request)
        method(value)
    else:
        dataError(request)

if __name__ == '__main__':
    main()
