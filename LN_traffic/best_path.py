"""Use Dijkstra's algorithm to find the best path with minimum fee/timelock/hops"""

import json
import networkx as nx

def load_graph(file_path):
    """Load the graph from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def build_graph(data, payment_amount_msat=1000000):
    """Build the graph with edge attributes: fee, capacity, timelock."""
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
    """Analyze a path: total fee, total timelock, min capacity, hops."""
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

def find_best_path(G, source, target, payment_amount_msat, weight_type):
    """Find the best path based on a specific weight."""
    try:
        path = nx.dijkstra_path(G, source, target, weight=weight_type)
        return analyze_path(G, path, payment_amount_msat)
    except nx.NetworkXNoPath:
        return None

# === Example usage ===
graph_info = load_graph('dataset/graph_info.json')

start_node = '03933884aaf1d6b108397e5efe5c86bcf2d8ca8d2f700eda99db9214fc2712b134'
end_node = '03ec72b4fa2664e0c51c7d303b61e88b3c070744f0c6e21b08653c5b8347cd4961'   
payment_amount_msat = 1000000

G = build_graph(graph_info, payment_amount_msat=payment_amount_msat)

results = {}

# Find best paths
results['fee_min'] = find_best_path(G, start_node, end_node, payment_amount_msat, weight_type='weight_fee')
results['hop_min'] = find_best_path(G, start_node, end_node, payment_amount_msat, weight_type='weight_hop')
results['timelock_min'] = find_best_path(G, start_node, end_node, payment_amount_msat, weight_type='weight_timelock')

# Save results
with open('dataset/dijkstra_best_paths.json', 'w') as f:
    json.dump(results, f, indent=2)

print("Saved Dijkstra best paths (fee, hop, timelock).")
