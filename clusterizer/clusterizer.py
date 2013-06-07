#!/usr/bin/env python3
from sys import argv

from sqlite_wrapper import SQLiteWrapper
from queries import *
from util import *
from collections import Counter
from pprint import pprint

import argparse
import itertools
import numpy
import csv
###

FILENAME = "clusters"

parser = argparse.ArgumentParser(description="BitIodine Clusterizer: groups addresses in ownership clusters.")
parser.add_argument('-d', dest='db', default="../blockchain/blockchain.sqlite",
				   help='SQLite database path')
parser.add_argument("--generate-clusters", action="store_true", dest="generate", default=False,
	help="Generate clusters (takes a long time)")
parser.add_argument("--load-clusters", action="store_true", dest="load", default=False,
	help="Load a previously generated clusters from disk")
options = parser.parse_args()

db = SQLiteWrapper(options.db)

if options.generate:
	try:
		max_txid_res = db.query(max_txid_query, fetch_one=True)
	except Exception as e:
		die(e)

	users, loaded = {}, False

	try:
		# Retrieve maximum cluster ID
		max_cluster_id = max(users.values())
	except ValueError:
		# users is empty
		max_cluster_id = 0

	try:
		users, min_txid = load(FILENAME)
		loaded = True
	except:
		min_txid = 1

	print("Scanning %d transactions, starting from %d." %(max_txid_res, min_txid))

	for tx_id in range(min_txid, max_txid_res + 1):
		# Save progress to files
		if tx_id % 1000000 == 0 and not loaded:
			print("TRANSACTION ID: %d" % (tx_id))
			save(users, FILENAME, tx_id)

		loaded = False

		try:
			in_res = db.query(in_query_addr, (tx_id,))
			out_res = db.query(out_query_addr, (tx_id,))
		except Exception as e:
			print(e)
			continue

		# IN - Heuristic 1 - multi-input transactions
		found = None
		for line in in_res:
			address = line[0]
			if address is None:
				continue
			pos = users.get(address)
			if pos is not None:
				users[address] = pos
				found = pos
			break
		else:
			continue

		if found is None:
			max_cluster_id += 1
			found = max_cluster_id

		for address in in_res:
			users[address[0]] = found

		# OUT - Heuristic 2 - shadow addresses
		# Exploit bitcoin client bug - "change never last output"
		# https://bitcointalk.org/index.php?topic=128042.msg1398752#msg1398752
		# https://bitcointalk.org/index.php?topic=136289.msg1451700#msg1451700
		if len(out_res) == 2:
			address1 = out_res[0][0]
			address2 = out_res[1][0]
			try:
				appeared1_res = db.query(used_so_far_query, (tx_id, address1), fetch_one=True)
				appeared2_res = db.query(used_so_far_query, (tx_id, address2), fetch_one=True)
			except Exception as e:
				die(e)

			if appeared1_res == 0:
				# Address 1 is never used and appeared, likely a shadow address, add to previous group
				# Exploits bitcoin client bug
				users[address1] = found

			if appeared2_res == 0 and appeared1_res == 1:
				# This is deterministic - last address is actually a shadow address
				users[address2] = found

	users = save(users, FILENAME, max_txid_res)

if options.load:
	try:
		users, _ = load(FILENAME)
		print("Clusters loaded - %d clusters, %d addresses in clusters." % (len(set(users.values())), len(users)))
	except Exception as e:
		die(e)

	counter = Counter(users.values())
	lengths = list(counter.values())

	users_no_singletons = stripSingletons(users)

	print("Minimum cluster size:", min(lengths))
	print("Maximum cluster size:", max(lengths))
	print("Average:", numpy.mean(lengths))
	print("Median:", numpy.median(lengths))
	print("Addresses clustered (no singletons):", len(users_no_singletons))

	# Generate histogram
	hist, bin_edges = numpy.histogram(lengths, bins=max(lengths)-1)

	with open("clusters_histogram.csv", "w") as f:
		writer = csv.writer(f)
		for i in range(0, len(hist)):
			writer.writerow([bin_edges[i], hist[i]])