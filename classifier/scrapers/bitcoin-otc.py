#!/usr/bin/env python3

from hashlib import sha256
from sys import exit
import urllib.request, urllib.error
import csv, re, os

def decode_base58(bc, length):
	CHARSET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
	n = 0
	for char in bc:
		n = n * 58 + CHARSET.index(char)
	return n.to_bytes(length, 'big')

def isBTCAddress(address):
	bcbytes = decode_base58(address, 25)
	return bcbytes[-4:] == sha256(sha256(bcbytes[:-4]).digest()).digest()[:4]

try:
	html = urllib.request.urlopen('http://blockchain.info/tags?filter=4').read().decode('utf-8')
except urllib.error.URLError as e:
	print(e.reason)
	exit(1)

results = re.findall(r"<span class=\"tag\" id=\"(\b1[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{20,40}\b)\">([^\"]+)</span>", html)

with open('../Lists/bitcoin-otc.csv', 'a') as f:
	writer = csv.writer(f)

	for result in results:

		address, username = result
		print("Adding user %s with address %s..." % (username, address))

		if not isBTCAddress(address):
			continue

		writer.writerow([address, username])

os.system("cp ../Lists/bitcoin-otc.csv /tmp/temp-bitcoin-otc.csv")
os.system("cat /tmp/temp-bitcoin-otc.csv | sort | uniq > ../Lists/bitcoin-otc.csv")
os.system("rm -f /tmp/temp-bitcoin-otc.csv")