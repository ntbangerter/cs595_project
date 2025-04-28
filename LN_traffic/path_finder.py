import json
import networkx as nx

def load_graph(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def build_graph(data, optimize_for='hops', payment_amount_msat=1000000):
    G = nx.DiGraph()

    for node_id, peers in data.items():
        for channel in peers:
            peer_id = channel['peer']
            capacity = channel['capacity']
            own_policy = channel['own_policy']

            if not own_policy or own_policy.get('disabled', True):
                continue  # Skip disabled channels or missing policy

            fee_base = int(own_policy.get('fee_base_msat', 0))
            fee_rate = int(own_policy.get('fee_rate_milli_msat', 0))

            if optimize_for == 'hops':
                weight = 1
            elif optimize_for == 'fee':
                fee = fee_base + (payment_amount_msat * fee_rate) // 1_000_000
                weight = fee
            elif optimize_for == 'htlc':
                # For HTLC optimization, we prioritize bigger capacity (so use negative capacity as "cost")
                weight = -capacity
            else:
                raise ValueError("Unknown optimize_for option!")

            G.add_edge(node_id, peer_id, weight=weight, capacity=capacity)

    return G

def find_paths(G, source, target, k=3):
    try:
        paths = list(nx.shortest_simple_paths(G, source, target, weight='weight'))
        return paths[:k]
    except nx.NetworkXNoPath:
        return []

# Example usage:
graph_info = load_graph('dataset/graph_info.json')

# === PARAMETERS ===
start_node = '0201a01b9f91aa2a...'  
end_node = '0397b0a2b3f31fa2...'    
payment_amount_msat = 1000000       
optimize_for = 'fee'                # 'hops', 'fee', or 'htlc'
top_k = 3                           # return top 3 routes
# === PARAMETERS ===

G = build_graph(graph_info, optimize_for=optimize_for, payment_amount_msat=payment_amount_msat)
paths = find_paths(G, start_node, end_node, k=top_k)

print(f"Found {len(paths)} paths:")
for idx, path in enumerate(paths, 1):
    print(f"Path {idx}: {path}")
