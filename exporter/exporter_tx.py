#!/usr/bin/env python3
import networkx as nx
import os
import pickle

from sys import argv

try:
	f = argv[1]
except:
	f = '../grapher/tx_graph.dat'

# Config
#
# Filter? (DOT will be a subgraph)
filter_dot = True
# Minimum amount of BTC sent a -> b to have an edge between them
# (in AND with the following other conditions)
threshold_recv = 1 # BTC
# a must have sent b money in more than threshold_number_of_transactions times
threshold_number_of_transactions = 1 # n
# minimum out degree of a
threshold_out_degree_src = 1 # n
# minimum in degree of b
threshold_in_degree_dst = 1 # n

with open(f, "rb") as infile:
	G = pickle.load(infile)

print("Graph loaded.")

f, _ = os.path.splitext(f)

nodes, edges = set(), []

with open(f + ".dot", 'w') as f:
	f.write('digraph G {\n');

	for u, v, d in G.edges_iter(data=True):
		n_of_tx = d['number_of_transactions']
		dst_recv = G.node[v].get('amount_received', 0)

		if filter_dot and (n_of_tx < threshold_number_of_transactions or dst_recv < threshold_recv or G.out_degree(u) < threshold_out_degree_src or G.in_degree(v) < threshold_in_degree_dst):
			continue
		nodes.add(u)
		nodes.add(v)
		edges.append((u, v, n_of_tx))

	print("Filtering results: %d nodes and %d edges." % (len(nodes), len(edges)))
	print("Generating a DOT file...")

	nodes = sorted(list(nodes))

	for n in nodes:
		recv = str(int(G.node[n].get('amount_received', 0)))
		f.write('"%s" [recv=%s];\n' % (n, recv))

	del G
	f.write('\n')

	for edge in edges:
		(u, v, n_of_tx) = edge
		f.write('"%s" -> "%s" [weight=%s];\n' % (u, v, str(n_of_tx)))

	f.write('};\n')