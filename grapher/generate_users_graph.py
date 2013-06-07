#!/usr/bin/env python3
import networkx as nx

from sqlite_wrapper import SQLiteWrapper
from queries import *
from util import *

###
FILENAME = "users_graph"
db = SQLiteWrapper('../blockchain/blockchain.sqlite')

# Load clusters
with open("../clusterizer/clusters.dat", "rb") as infile:
	users = pickle.load(infile)

print("Clusters loaded - %d addresses." % len(users))

users = stripSingletons(users)

print("Singletons stripped - %d addresses." % len(users))

try:
  max_txid_res = db.query(max_txid_query, fetch_one=True)
except Exception as e:
  die(e)

G = nx.DiGraph()
min_txid = 1

try:
  G, min_txid = load(FILENAME)
except:
  pass

print("Scanning %d transactions, starting from %d." %(max_txid_res, min_txid))

for tx_id in range(min_txid, max_txid_res + 1):

  source_is_addr, dest_is_addr = False, False

  # Save progress to files
  if tx_id % 1000000 == 0:
    print("TRANSACTION ID: %d" % (tx_id))
    save(G, FILENAME, tx_id)
    print(nx.number_of_nodes(G), "nodes,", nx.number_of_edges(G), "edges so far.")

  try:
    in_res = db.query(in_query_addr, (tx_id,))
    out_res = db.query(out_query_addr_with_value, (tx_id,))
  except:
    # Just go to the next transaction
    continue

  # Pre-test: if more than two outputs, we can't say which is the real recipient.
  # So, skip. (Very very few transactions skipped)
  if len(out_res) > 2:
    continue

  source = None
  # IN
  for line in in_res:
    address = line[0]
    if address is None:
      continue
    pos = users.get(address)
    if pos is not None:
      source = pos
      break
  else:
    continue

  if source is None:
    source = address
    source_is_addr = True

  # OUT
  # One output transaction case
  try:
    if len(out_res) == 1:
      dest_addr = out_res[0][0]
      tx_value = float(out_res[0][1]) * 10**-8
  except:
    continue

  # If two outputs, real recipient is the second
  # Exploit bitcoin client bug - "change never last output"
  # https://bitcointalk.org/index.php?topic=128042.msg1398752#msg1398752
  # https://bitcointalk.org/index.php?topic=136289.msg1451700#msg1451700
  try:
    if len(out_res) == 2:
      dest_addr = out_res[1][0]
      tx_value = float(out_res[1][1]) * 10**-8
  except:
    continue

  if dest_addr is not None:
    dest = users.get(dest_addr)

    if dest is None:
      dest = dest_addr
      dest_is_addr = True

    # Ignore source -> dest if both are not clustered
    # if source_is_addr and dest_is_addr:
    #   continue
    G.add_node(dest)
  else:
    continue

  try:
      number_of_transactions = G.edge[source][dest]['number_of_transactions']
  except:
      number_of_transactions = 0

  G.add_edge(str(source), str(dest), number_of_transactions=number_of_transactions+1)
  G.node[str(dest)]['amount_received'] = G.node[dest].get('amount_received', 0) + tx_value

save(G, FILENAME, tx_id)