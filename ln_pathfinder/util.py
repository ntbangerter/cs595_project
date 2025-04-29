import json
import networkx as nx
from itertools import combinations

def load_graph(file_path):
    """Load the graph info from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def build_graph(data, payment_amount_msat=1000000):
    """Build a directed graph only keeping channels with sufficient capacity."""
    G = nx.DiGraph()

    for node_id, peers in data.items():
        for channel in peers:
            peer_id = channel['peer']
            capacity = channel['capacity']
            own_policy = channel['own_policy']

            if not own_policy or own_policy.get('disabled', True):
                continue

            if capacity * 1000 < payment_amount_msat:
                continue

            G.add_edge(node_id, peer_id)

    return G

def find_most_connected_pair(G, max_pairs=1000, max_path_limit=1000):
    """
    Find the pair of nodes (u, v) which has the maximum number of paths,
    but the total number of paths must be less than max_path_limit.
    """
    max_paths = 0
    best_pair = None

    nodes = list(G.nodes)
    node_pairs = list(combinations(nodes, 2))

    for u, v in node_pairs[:max_pairs]:
        try:
            paths = list(nx.all_simple_paths(G, source=u, target=v, cutoff=6))  
            num_paths = len(paths)
            # !!! Important: use "and" instead of bitwise "&"
            if num_paths > max_paths and num_paths < max_path_limit:
                max_paths = num_paths
                best_pair = (u, v)
        except nx.NetworkXNoPath:
            continue

    return best_pair, max_paths

# === Example usage ===
graph_info = load_graph('dataset/graph_info.json')

payment_amount_msat = 1000000  # 1000 satoshis

G = build_graph(graph_info, payment_amount_msat=payment_amount_msat)

# Check 1000 random node pairs
best_pair, num_paths = find_most_connected_pair(G, max_pairs=1000, max_path_limit=1000)

if best_pair:
    print(f"Best live demo nodes found!")
    print(f"Source Node: {best_pair[0]}")
    print(f"Target Node: {best_pair[1]}")
    print(f"Number of possible paths: {num_paths}")
else:
    print("No suitable node pair found.")
