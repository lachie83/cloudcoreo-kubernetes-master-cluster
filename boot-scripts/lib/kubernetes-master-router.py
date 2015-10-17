#!/usr/bin/env python

# Copyright 2015: CloudCoreo Inc
# License: Apache License v2.0
# Author(s):
#   - Paul Allen (paul@cloudcoreo.com)
# Example Usage:
#   - ./kubernetes-master-router.py --log-file /var/log/ha-nat.log --monitor-interval 15 --master-cidr-block "10.234.0.0/23"
#   - ./kubernetes-master-router.py --log-file /var/log/ha-nat.log --monitor-interval 15 --master-cidr-block "10.234.0.0/23" --eips "1.2.3.4,10.20.30.40,99.88.77.66"
#   - ./kubernetes-master-router.py --log-file /var/log/ha-nat.log --monitor-interval 15 --master-cidr-block "10.234.0.0/23" --create-eips
#

import boto
import boto.ec2
from boto.exception import EC2ResponseError
import datetime
import os
import sys
from optparse import OptionParser
from boto.vpc import VPCConnection
import subprocess
import socket
import time
from netaddr import IPNetwork

version = "0.0.1"

## globals for caching
MY_AZ = None
MY_VPC_ID = None
INSTANCE_ID = None
MY_SUBNETS = None
MY_ROUTE_TABLES = None

def parseArgs():
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("--debug",             dest="debug",          default=False, action="store_true",     help="Whether or not to run in debug mode [default: %default]")
    parser.add_option("--version",           dest="version",        default=False, action="store_true",     help="Display the version and exit")
    parser.add_option("--monitor-interval",  dest="monitorInterval",default="300",                          help="The frequency in seconds of which to check the routes [default: %default]")
    parser.add_option("--master-cidr-block", dest="masterCidrBlock",default="",                             help="A CIDR in which all kubernetes routes will exist")
    parser.add_option("--eips",              dest="eips",           default=None,                           help="A CSV of EIPs to assign to the NATs.")
    parser.add_option("--create-eips",       dest="createEips",     default=False, action="store_true",     help="Create EIPs to assign if there are none available.")
    parser.add_option("--log-file",          dest="logFile",        default="/var/log/ha-nat.log",          help="The log file in which to dump debug information [default: %default]")
    return parser.parse_args()

def log(statement):
    statement = str(statement)
    if options.logFile is None:
        return
    if not os.path.exists(os.path.dirname(options.logFile)):
        os.makedirs(os.path.dirname(options.logFile))
    logFile = open(options.logFile, 'a')
    ts = datetime.datetime.now()
    isFirst = True
    for line in statement.split("\n"):
        if isFirst:
            logFile.write("%s - %s\n" % (ts, line))
            isFirst = False
        else:
            logFile.write("%s -    %s\n" % (ts, line))
    logFile.close()

def cmd_output(args, **kwds):
    ## this function will run a command on the OS and return the result
    kwds.setdefault("stdout", subprocess.PIPE)
    kwds.setdefault("stderr", subprocess.STDOUT)
    proc = subprocess.Popen(args, **kwds)
    return proc.communicate()[0]
    
def metaData(dataPath):
    ## using 169.254.169.254 instead of 'instance-data' because some people
    ## like to modify their dhcp tables...
    return cmd_output(["curl", "-sL", "169.254.169.254/latest/meta-data/" + dataPath])

def getAvailabilityZone():
    ## cached
    global MY_AZ
    if MY_AZ is None:
        MY_AZ = metaData("placement/availability-zone")
    return MY_AZ

def getRegion():
  return getAvailabilityZone()[:-1]

def getInstanceId():
    ## cached
    global INSTANCE_ID
    if INSTANCE_ID == None:
        INSTANCE_ID = metaData("instance-id")
    return INSTANCE_ID

def findBlackholes():
    ## don't cache this value as we need to keep checking
    myFilters = [['vpc-id', getMyVPCId()], ['route.state', 'blackhole']]
    retTables = VPC.get_all_route_tables(filters=myFilters)
    log("found blackholes: %s" % retTables)
    return retTables

def disableSourceDestChecks():
    EC2.modify_instance_attribute(getInstanceId(), "sourceDestCheck", False)

def getMyRouteTables(subnet):
    ## this cannot be cached beacuse we need to keep checking the route tables
    rt_filters = [['vpc-id', getMyVPCId()], ['association.subnet-id', subnet.id]]
    return VPC.get_all_route_tables(filters=rt_filters)
  
def getSubnetById(subnetid):
    ## cached
    subnet_filters = [['subnet-id', subnetid]]
    subnet = VPC.get_all_subnets(filters=subnet_filters)[0]
    log('got a subnet: %s' % subnet.id)
    return subnet

def getMyVPCId():
    ## cached
    global MY_VPC_ID
    if MY_VPC_ID == None:
        MY_VPC_ID = getMe().vpc_id
    return MY_VPC_ID
  
def getMySubnets():
    ## cached
    global MY_SUBNETS
    if MY_SUBNETS == None:
        az_subnet_filters = [['availability-zone', getAvailabilityZone()],['vpc-id', getMyVPCId()]]
        MY_SUBNETS = VPC.get_all_subnets(filters=az_subnet_filters)
    return MY_SUBNETS

def getMe():
    ## don't cache this as our instance attributes can change
    return EC2.get_only_instances(instance_ids=[getInstanceId()])[0]

def replaceIfWrongAZ():
    log("replaceIfWrongAZ | checking getAvailabilityZone(): %s" % getAvailabilityZone())
    ## find subnet(s) in my AZ
    for subnet in getMySubnets():
        log("replaceIfWrongAZ | checking subnet: %s" % subnet.id)
        ## find routes with instances
        for route_table in getMyRouteTables(subnet):
            log("replaceIfWrongAZ | checking route table: %s" % route_table.id)
            if route_table.id == None:
                continue
            for route in route_table.routes:
                log("replaceIfWrongAZ | checking route: %s | %s" % (route.destination_cidr_block, route.instance_id))
                if routeDestinationIsInCidrBlock(route.destination_cidr_block) == False:
                    continue
                if route.instance_id == None:
                    continue
                if route.instance_id == None or route.instance_id == "":
                    continue
                ## check the AZ of the instances
                for instance in EC2.get_only_instances(instance_ids=[route.instance_id]):
                    if instance.placement != getAvailabilityZone():
                        ## wrong zone
                        ## if the AZ of the instance is different than ours and the route table, replace it
                        log('incorrect az - replacing route')
                        if not options.debug:
                            VPC.replace_route(route_table_id = route_table.id,
                                              destination_cidr_block = route.destination_cidr_block,
                                              gateway_id = route.gateway_id,
                                              instance_id = getInstanceId())
                        else:
                            log('skipped VPC.replace_route due to debug flag')

                    else:
                        ## correct zone
                        ## if the AZ of the instance is the same, do nothing
                        log('correct az - not replacing the route')

def routeDestinationIsInCidrBlock(destination_cidr_block):
    log("routeDestinationIsInCidrBlock | checking cidr %s" % destination_cidr_block)
    log("IPNetwork(%s) in IPNetwork(%s)" % (destination_cidr_block,options.masterCidrBlock))
    retBool = IPNetwork(destination_cidr_block) in IPNetwork(options.masterCidrBlock)
    log("routeDestinationIsInCidrBlock | returning %s" % retBool)
    return retBool

def main():
    ## this should do the following
    ##   1) if eips are called out or createEips is enabled, ensure we have an EIP assigned to us
    ##      a) if we do not
    ##         i) look through the list assinged
    ##        ii) if we find one unassigned, take it
    ##       iii) if we do not find one unassigned, check if we are allowed to create EIPs
    ##        iv) if we are allowed to create EIPs, create one and assign it to ourself
    ##         v) if we are not allowed to create EIPs, log an error and continue to try again later
    ##       b) if we do have an EIP, move on
    ##   2) ensure a private subnet route exists pointing to 0.0.0.0/0
    ##   3) ensure source/destination checks are disabled
    ##   4) if there is a blackhole in replace it with this instnace
    ##   5) if there is no blackhole in this AZ, replace only if the registered instance
    ##      is NOT in this AZ
    if options.createEips or (options.eips != None and options.eips != ""):
        log("we have been asked to handle eips - handling now")
        ## check if we have an EIP assigned to us
        filters = {'instance-id': getInstanceId()}
        addresses = EC2.get_all_addresses(filters = filters)
        log("got addresses: %s" % addresses)
        have_eip = False
        if not addresses:
            ## we don't have an EIP
            log("no EIP assigned to this instance - looking for EIPS")
            if options.eips != "":
                log("eips have been specified")
                for eip_assigned in options.eips.split(','):
                    if eip_assigned == "":
                        continue
                    log(" - searching for %s" % eip_assigned)
                    try:
                        address = EC2.get_all_addresses(addresses = [eip_assigned])[0]
                        log(" - found address: %s" % (address))
                    except EC2ResponseError:
                        log("ERROR: address not found in account %s" % eip_assigned)
                        continue
                    ## we only care about addresses that are not associated
                    if address.association_id:
                        continue
                    if address.public_ip == eip_assigned:
                        log("found matching usable ip %s - associating to this instance [%s]" % (eip_assigned, getInstanceId()))
                        EC2.associate_address(instance_id = getInstanceId(), public_ip = eip_assigned)
                        have_eip = True
                ## we should have an eip here now, if not lets raise an exception
                raise Exception("Expected to have an EIP at this point, but do not")

            if have_eip == False and options.createEips:
                ## we still dont have an EIP, but we are allowed to create them, so lets do that
                ## first, we will just check if there is an empty one we can use
                addresses = EC2.get_all_addresses()
                for address in addresses:
                    if address.association_id:
                        ## we only care about unassociated ip addresses
                        continue
                    ## if we made it here, lets just take it and exit
                    log("found an IP address - associating [%s] with instance_id [%s]" % (address.public_ip, getInstanceId()))
                    EC2.associate_address(instance_id = getInstanceId(), public_ip = address.public_ip)
                    have_eip = True
                    break
                if have_eip == False:
                    ## we still have no EIP - time to create one
                    log("creating new IP address")
                    try:
                        new_address = EC2.allocate_address()
                        log("associating new ip address [%s] with instance_id [%s]" % (new_address.public_ip, getInstanceId()))
                        EC2.associate_address(instance_id = getInstanceId(), public_ip = new_address.public_ip)
                        have_eip = True
                    except:
                        log("ERROR: cannot allocate and assign a new IP address")
            log("EIPs have been handled to the best of our ability - continuing on now")
        else:
            have_eip = True
        
        if have_eip == False:
            raise Exception('Unable to assign requested EIP - not continuing')

    for route_table in findBlackholes():
        log("main | checking route table: %s" % route_table.id)
        if route_table.id == None:
            continue
        for route in route_table.routes:
            log("main | checking route: %s | %s" % (route.destination_cidr_block, route.instance_id))
            if routeDestinationIsInCidrBlock(route.destination_cidr_block) == False:
                log("main | continuing because routeDestinationIsInCidrBlock(route.destination_cidr_block) == False")
                continue
            if not route.state == 'blackhole':
                continue
            log('main | found a black hole - taking the route over')
            if not options.debug:
                VPC.replace_route(route_table_id = route_table.id,
                                  destination_cidr_block = route.destination_cidr_block,
                                  gateway_id = route.gateway_id,
                                  instance_id = getInstanceId())
            else:
                log('skipped VPC.replace_route due to debug flag')
    replaceIfWrongAZ()                         
   
print "here"
print "here"
(options, args) = parseArgs()

if options.version:
    print(version)
    sys.exit(0)

print options
EC2 = boto.ec2.connect_to_region(getRegion())
VPC = boto.vpc.connect_to_region(getRegion())

## these only need to run once
log("disabling source/destination checks")
disableSourceDestChecks()

while True:
    try:
        main()
    except Exception as e:
        log("ERROR: %s" % str(e))
    log("sleeping %d before rechecking" % (int(options.monitorInterval)))
    time.sleep(int(options.monitorInterval))
