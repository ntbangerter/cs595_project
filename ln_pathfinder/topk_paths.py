"""
Use lazy Yen's algorithm to find the best-k paths with minimum fee/timelock/hops
Provide more options but may slow down the routing process
"""

import json
import networkx as nx

def load_graph(file_path):
    """Load the graph from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def build_graph(data, payment_amount_msat=1000000):
    """Build the graph with fee, hops, and timelock attributes."""
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
            fee_base = int(own_policy.get('fee_base_msat', 0))
            fee_rate = int(own_policy.get('fee_rate_milli_msat', 0))
            fee = fee_base + (payment_amount_msat * fee_rate) // 1_000_000
            time_lock_delta = int(own_policy.get('time_lock_delta', 0))

            G.add_edge(node_id, peer_id,
                       weight_fee=fee,
                       weight_hop=1,
                       weight_timelock=time_lock_delta,
                       capacity=capacity,
                       fee_base=fee_base,
                       fee_rate=fee_rate,
                       time_lock_delta=time_lock_delta)
    return G

def analyze_path(G, path, payment_amount_msat):
    """Analyze a path: total fee, timelock, min capacity, and hops."""
    total_fee = 0
    total_timelock = 0
    min_capacity = float('inf')

    for i in range(len(path)-1):
        u = path[i]
        v = path[i+1]
        edge = G[u][v]
        fee = edge['fee_base'] + (payment_amount_msat * edge['fee_rate']) // 1_000_000
        total_fee += fee
        total_timelock += edge['time_lock_delta']
        min_capacity = min(min_capacity, edge['capacity'])

    return {
        'path': path,
        'hops': len(path) - 1,
        'total_fee_msat': total_fee,
        'min_capacity_sat': min_capacity,
        'total_timelock': total_timelock
    }

def find_topk_paths(G, source, target, payment_amount_msat, samples=100, k=10, max_hop=10):
    """Sample multiple times to find candidate paths."""
    all_candidate_paths = []

    for _ in range(samples):
        try:
            paths = nx.shortest_simple_paths(G, source, target, weight='weight_fee')
            count = 0
            for path in paths:
                if len(path) - 1 > max_hop:
                    continue
                path_info = analyze_path(G, path, payment_amount_msat)
                all_candidate_paths.append(path_info)
                count += 1
                if count >= k:
                    break
        except nx.NetworkXNoPath:
            continue

    return all_candidate_paths

def save_bestk_paths(all_paths, output_dir='dataset/', k=10):
    """Select top-k paths by fee, hops, and timelock separately and save to different JSON files."""
    if not all_paths:
        print("No candidate paths found.")
        return

    # Sort and select top-k
    paths_by_fee = sorted(all_paths, key=lambda x: x['total_fee_msat'])[:k]
    paths_by_hops = sorted(all_paths, key=lambda x: x['hops'])[:k]
    paths_by_timelock = sorted(all_paths, key=lambda x: x['total_timelock'])[:k]

    # Save
    with open(output_dir + 'paths_by_fee.json', 'w') as f:
        json.dump(paths_by_fee, f, indent=2)
    with open(output_dir + 'paths_by_hops.json', 'w') as f:
        json.dump(paths_by_hops, f, indent=2)
    with open(output_dir + 'paths_by_timelock.json', 'w') as f:
        json.dump(paths_by_timelock, f, indent=2)

    print(f"Saved top-{k} paths separately by fee, hops, and timelock.")

# === Example usage ===
graph_info = load_graph('dataset/graph_info.json')

start_node = '03933884aaf1d6b108397e5efe5c86bcf2d8ca8d2f700eda99db9214fc2712b134'
end_node = '03ec72b4fa2664e0c51c7d303b61e88b3c070744f0c6e21b08653c5b8347cd4961'   
payment_amount_msat = 1000000

G = build_graph(graph_info, payment_amount_msat=payment_amount_msat)

# Find paths
all_paths = find_topk_paths(G, start_node, end_node, payment_amount_msat, k=10, samples=100)

# Select and save best ones
save_bestk_paths(all_paths, output_dir='dataset/')
