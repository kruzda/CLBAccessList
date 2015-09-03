#!/usr/bin/env python
############################################################################
# Author: Blake Moore 2015                                                 #
# Contributors: Erik Ljungstrom                                            #
###########################################################################
# Description: This script is designed to manage your access list on       #
# a Rackspace cloud server.                                                #
# It was iniitally built with the idea of adding into fail2ban to block    #
# malious Wordpress logins on the Load Balancer level.                     #
############################################################################

import requests
import json
import sys
import time
from functools import wraps

# The below variables need to be set before running this script.

username = ""
api_key = ""
lb_id = ""
region = ""

try:
    from credentials import username, api_key, lb_id, region
except ImportError:
    pass

if not all(key for key in [username, api_key, lb_id, region]):
    print "Make sure you have provided all required credentials"\
          " by editing %s" % sys.argv[0]
    exit(1)

# These dont really change
headers = {"Content-Type": "application/json"}
auth_url = "https://identity.api.rackspacecloud.com/v2.0/tokens"


# a fuction to print usage
def usage():
    print "Usage: %s [--list] [--delete-everything] | [--add] [--delete] <12" \
        "3.45.67.89>" % sys.argv[0]
    print "-a|-A|--add <IP Address>         - Add an IP address to your " \
        "load balancers access list."
    print "-d|-D|--delete <IP address>      - Remove an IP address to yo"\
        "ur load balancers access list."
    print "-l|-L|--list                     - Shows the current access list."
    print "-rmrf|-RMRF|--delete-everything  - Deletes the entire access list."
    print "-h|-H|--help                     - Show help dialog."
    exit(1)


# Error message for if we don't get the expected http code
def api_fail(message, status_code, origin):
    print "An API error has occured whilst running '%s'. Status code: %s" \
        % (origin, status_code)
    print message
    exit(1)


# Get serviceCatalog / Authentication details
def service_catalog():
    data = {
        "auth":
        {
            "RAX-KSKEY:apiKeyCredentials":
            {
                "username": username,
                "apiKey": api_key
            }
        }
    }
    result = requests.post(auth_url, headers=headers, data=json.dumps(data))
    if result.status_code != 200:
        print "Error during authentication."
        print "Message: %s Code: %s" % (
            result.json().get("unauthorized").get("message"),
            result.status_code
        )
        exit(1)
    return result.json()


# Get Authentication token
def get_token(auth_data):
    auth_token = auth_data.get("access").get("token").get("id")
    return auth_token


# Get LB endpoint for the correct region
def get_endpoint(auth_data):
    lb_endpoint = None
    for service in auth_data.get("access").get("serviceCatalog"):
        if service.get("name") == "cloudLoadBalancers":
            for endpoint in service.get("endpoints"):
                if endpoint.get("region") == region:
                    lb_endpoint = endpoint.get("publicURL")
    if not lb_endpoint:
        print endpoint.get("region")
        print "Load Balancer endpoint could not be set"
        exit(1)

    return lb_endpoint


class PendingError(Exception):
    def __init__(self, message):
        super(PendingError, self).__init__(message)


def retry(ExceptionToCheck=PendingError, retries=5, delay=2):
    def retry_decorator(f):
        @wraps(f)
        def retry_deco(*args, **kwargs):
            _retries = retries
            while _retries:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck:
                    print "Load balancer is in a pending state,"\
                          " waiting %d second%s. %d retries remaining." % (
                              delay,
                              "" if delay == 1 else "s",
                              _retries)
                    _retries -= 1
                    time.sleep(delay)
            return f(*args, **kwargs)
        return retry_deco
    return retry_decorator


# Add an IP address to the Load Balancers access list.
@retry()
def add_ban(url):
    deny_data = {
        "accessList": [
            {
                "type": "DENY",
                "address": sys.argv[2]
            }
        ]
    }
    result = requests.post(url, headers=headers, data=json.dumps(deny_data))
    if result.status_code == 422:
        raise PendingError("")
    elif result.status_code not in [202, 200]:
        api_fail(result.text, result.status_code, "add_ban")

    print "Success. %s added to ban" % sys.argv[2]


# Remove an IP address from the Load Balancers access list.
@retry()
def delete_ban(url):
    result = requests.get(url, headers=headers)
    network_id = None
    for address in result.json().get("accessList"):
        if address.get("address") == sys.argv[2]:
            network_id = address.get("id")

    if not network_id:
        print "Network ID could not be retrieved"
        exit(1)
    url = "%s/%s" % (url, network_id)
    result = requests.delete(url, headers=headers)
    if result.status_code == 422:
        raise PendingError("")
    elif result.status_code not in [202, 200]:
        api_fail(result.text, result.status_code, "delete_ban")

    print "Success. %s has been unbanned" % sys.argv[2]


# List all current rules on the access list
def list_rules(url):
    result = requests.get(url, headers=headers)
    if result.status_code not in [202, 200]:
        api_fail(result.text, result.status_code, "list_rules")
        print result.json().get("accessList")
    for address in result.json().get("accessList"):
        print json.dumps(address)


# Delete allthethings
@retry()
def delete_all_rules(url):
    result = requests.delete(url, headers=headers)
    if result.status_code == 422:
        raise PendingError("")
    elif result.status_code not in [202, 200]:
        api_fail(result.text, result.status_code, "delete_all_rules")
    print result.status_code

# Exit script if there are not enough, or too few arguments passed
if len(sys.argv) not in [2, 3]:
    usage()

auth_data = service_catalog()
token = get_token(auth_data)
headers["X-Auth-Token"] = token
endpoint = get_endpoint(auth_data)
url = "%s/loadbalancers/%s/accesslist" % (endpoint, lb_id)

# If two options are passed, send to -a/-d as these are the options which
# require multiple arguments
if len(sys.argv) == 3:
    if sys.argv[1].lower() in ["-a", "--add"]:
        add_ban(url)
    elif sys.argv[1].lower() in ["-d", "--delete"]:
        delete_ban(url)
    else:
        usage()
# If only the options alone is passed, send to -l/-h/-rmrf
elif len(sys.argv) == 2:
    if sys.argv[1].lower() in ["-l", "--list"]:
        list_rules(url)
    elif sys.argv[1].lower() in ["-h", "--help"]:
        usage()
    elif sys.argv[1].lower() in ["-rmrf", "--delete-everything"]:
        delete_all_rules(url)
    else:
        usage()
