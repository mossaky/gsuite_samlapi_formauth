#! env python
#
# Scraping Sample
#   scraping.py
#
import os
import sys
import json
import requests
import time
import base64
import logging
import xml.etree.ElementTree as ET
import re
import boto.sts
import boto.s3
import ConfigParser
import getpass
from os.path import expanduser
from selenium import webdriver
from bs4 import BeautifulSoup

##########################################################################
# Variables

# region: The default AWS region that this script will connect
# to for all API calls
region = 'ap-northeast-1'

# output format: The AWS CLI output format that will be configured in the
# saml profile (affects subsequent CLI calls)
outputformat = 'json'

# awsconfigfile: The file where this script will store the temp
# credentials under the saml profile
awsconfigfile = '/.aws/credentials'

# SSL certificate verification: Whether or not strict certificate
# verification is done, False should only be used for dev/test
sslverification = True

# idpentryurl: The initial url that starts the authentication process.
#idpentryurl = 'https://<fqdn>:<port>/idp/profile/SAML2/Unsolicited/SSO?providerId=urn:amazon:webservices'
#idpentryurl = 'https://accounts.google.com/o/saml2/initsso?idpid=C03fakw2d&spid=11493759999&forceauthn=false'
idpentryurl = 'https://accounts.google.com/AccountChooser?continue=https://accounts.google.com/o/saml2/initsso?idpid%3DC03fakw2d%26spid%3D11493759999%26forceauthn%3Dfalse%26from_login%3D1%26as%3D6ff994852c3247ed&ltmpl=popup&btmpl=authsub&scc=1&oauth=1'

# Uncomment to enable low level debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

##########################################################################

# Get the federated credentials from the user
print "Username:",
username = raw_input()
password = getpass.getpass()
print ''

username = "m.okamura@sonicmoov.com"
password = "K6m4UdZb"


# selenium settings
phantomjs_args = ['--cookie-file={}'.format("cookie.txt")]
driver = webdriver.PhantomJS(service_log_path=os.path.devnull)
# get HTML response
driver.get(idpentryurl)
driver.find_element_by_xpath("//input[@name='Email']").send_keys(username)
driver.find_element_by_xpath("//input[@id='next']").click()
time.sleep(2)
driver.find_element_by_xpath("//input[@name='Passwd']").send_keys(password)
driver.find_element_by_xpath("//input[@id='signIn']").submit()

response = driver.page_source.encode('utf-8')

# Overwrite and delete the credential variables, just for safety
username = '##############################################'
password = '##############################################'
del username
del password

# parse the response
soup = BeautifulSoup(response,  "lxml")
# extract
assertion = ''
for inputtag in soup.find_all('input'):
    if (inputtag.get('name') == 'SAMLResponse'):
        #print(inputtag.get('value'))
        assertion = inputtag.get('value')

if (assertion == ''):
    print "error: assertion is empty."
    sys.exit(1)

#print(base64.b64decode(assertion))

awsroles = []
root = ET.fromstring(base64.b64decode(assertion))
for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
    if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
        for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
            awsroles.append(saml2attributevalue.text)

# Note the format of the attribute value should be role_arn,principal_arn
# but lots of blogs list it as principal_arn,role_arn so let's reverse
# them if needed
for awsrole in awsroles:
    chunks = awsrole.split(',')
    if'saml-provider' in chunks[0]:
        newawsrole = chunks[1] + ',' + chunks[0]
        index = awsroles.index(awsrole)
        awsroles.insert(index, newawsrole)
        awsroles.remove(awsrole)

# If I have more than one role, ask the user which one they want,
# otherwise just proceed
print ""
if len(awsroles) > 1:
    i = 0
    print "Please choose the role you would like to assume:"
    for awsrole in awsroles:
        print '[', i, ']: ', awsrole.split(',')[0]
        i += 1
    print "Selection: ",
    selectedroleindex = raw_input()

    # Basic sanity check of input
    if int(selectedroleindex) > (len(awsroles) - 1):
        print 'You selected an invalid role index, please try again'
        sys.exit(0)

    role_arn = awsroles[int(selectedroleindex)].split(',')[0]
    principal_arn = awsroles[int(selectedroleindex)].split(',')[1]
else:
    role_arn = awsroles[0].split(',')[0]
    principal_arn = awsroles[0].split(',')[1]

logger.debug("role_arn: " + role_arn)
logger.debug("principal_arn: " + principal_arn)
logger.debug("assertion: " + assertion)
# Use the assertion to get an AWS STS token using Assume Role with SAML
conn = boto.sts.connect_to_region(region)
token = conn.assume_role_with_saml(role_arn, principal_arn, assertion)

# Write the AWS STS token into the AWS credential file
home = expanduser("~")
filename = home + awsconfigfile

# Read in the existing config file
config = ConfigParser.RawConfigParser()
config.read(filename)

# Put the credentials into a saml specific section instead of clobbering
# the default credentials
if not config.has_section('saml'):
    config.add_section('saml')

config.set('saml', 'output', outputformat)
config.set('saml', 'region', region)
config.set('saml', 'aws_access_key_id', token.credentials.access_key)
config.set('saml', 'aws_secret_access_key', token.credentials.secret_key)
config.set('saml', 'aws_session_token', token.credentials.session_token)

# Write the updated config file
with open(filename, 'w+') as configfile:
    config.write(configfile)

# Give the user some basic info as to what has just happened
print '\n\n----------------------------------------------------------------'
print 'Your new access key pair has been stored in the AWS configuration file {0} under the saml profile.'.format(filename)
print 'Note that it will expire at {0}.'.format(token.credentials.expiration)
print 'After this time, you may safely rerun this script to refresh your access key pair.'
print 'To use this credential, call the AWS CLI with the --profile option (e.g. aws --profile saml ec2 describe-instances).'
print '----------------------------------------------------------------\n\n'

# Use the AWS STS token to list all of the S3 buckets
s3conn = boto.s3.connect_to_region(region,
                     aws_access_key_id=token.credentials.access_key,
                     aws_secret_access_key=token.credentials.secret_key,
                     security_token=token.credentials.session_token)

buckets = s3conn.get_all_buckets()

print 'Simple API example listing all S3 buckets:'
print(buckets)

