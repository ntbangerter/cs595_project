import json
import heapq
import itertools
import networkx as nx

def load_graph(file_path):
    """Load the graph information from a JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def build_graph(data, payment_amount_msat=1000000):
    """Build a directed graph with edge attributes for fee, capacity, and timelock."""
    G = nx.DiGraph()

    for node_id, peers in data.items():
        for channel in peers:
            peer_id = channel['peer']
            capacity = channel['capacity']
            own_policy = channel['own_policy']

            if not own_policy or own_policy.get('disabled', True):
                continue

            if capacity * 1000 < payment_amount_msat:
                continue  # Skip if the channel capacity is too small for the payment

            fee_base = int(own_policy.get('fee_base_msat', 0))
            fee_rate = int(own_policy.get('fee_rate_milli_msat', 0))
            time_lock_delta = int(own_policy.get('time_lock_delta', 0))

            fee = fee_base + (payment_amount_msat * fee_rate) // 1_000_000

            G.add_edge(node_id, peer_id,
                       weight=fee,  # Use fee as the edge weight for shortest path search
                       capacity=capacity,
                       fee_base=fee_base,
                       fee_rate=fee_rate,
                       time_lock_delta=time_lock_delta)

    return G

def analyze_path(G, path, payment_amount_msat):
    """Analyze a given path to compute total fee, total timelock, and minimum capacity."""
    total_fee = 0
    total_timelock = 0
    min_capacity = float('inf')

    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        edge_data = G[u][v]

        fee_base = edge_data.get('fee_base', 0)
        fee_rate = edge_data.get('fee_rate', 0)
        capacity = edge_data.get('capacity', 0)
        time_lock_delta = edge_data.get('time_lock_delta', 0)

        fee = fee_base + (payment_amount_msat * fee_rate) // 1_000_000
        total_fee += fee
        total_timelock += time_lock_delta
        min_capacity = min(min_capacity, capacity)

    return {
        "path": path,
        "hops": len(path) - 1,
        "total_fee_msat": total_fee,
        "min_capacity_sat": min_capacity,
        "total_timelock": total_timelock
    }

def save_to_file(paths, filename):
    """Save the list of paths information into a JSON file."""
    with open(filename, 'w') as f:
        json.dump(paths, f, indent=2)

def find_topk_paths(G, source, target, payment_amount_msat, top_k=10, max_no_improve=500, max_hop=6):
    """
    Find top-k paths optimized by different metrics.
    Stop early if no better path is found for a long time.
    """
    top_fee = []
    top_timelock = []
    top_hops = []
    counter = itertools.count()

    print("Start searching paths...")

    gen_paths = nx.shortest_simple_paths(G, source, target, weight='weight')

    best_fee = float('inf')
    no_improve_count = 0
    total_checked = 0

    for path in gen_paths:
        # Skip paths that are too long
        if len(path) - 1 > max_hop:
            continue

        path_info = analyze_path(G, path, payment_amount_msat)
        cnt = next(counter)

        # Push into heaps
        heapq.heappush(top_fee, (path_info['total_fee_msat'], cnt, path_info))
        heapq.heappush(top_timelock, (path_info['total_timelock'], cnt, path_info))
        heapq.heappush(top_hops, (path_info['hops'], cnt, path_info))

        if len(top_fee) > top_k:
            heapq.heappop(top_fee)
        if len(top_timelock) > top_k:
            heapq.heappop(top_timelock)
        if len(top_hops) > top_k:
            heapq.heappop(top_hops)

        # Early stop condition: no better fee found
        if path_info['total_fee_msat'] < best_fee:
            best_fee = path_info['total_fee_msat']
            no_improve_count = 0
        else:
            no_improve_count += 1

        total_checked += 1
        if no_improve_count >= max_no_improve:
            print(f"No better fee found after {max_no_improve} paths, stopping early...")
            break

    print(f"Total paths checked: {total_checked}")

    # Sort the final paths
    paths_by_fee = [x[2] for x in sorted(top_fee)]
    paths_by_timelock = [x[2] for x in sorted(top_timelock)]
    paths_by_hops = [x[2] for x in sorted(top_hops)]

    return paths_by_fee, paths_by_timelock, paths_by_hops

# === Example usage ===
graph_info = load_graph('dataset/graph_info.json')

# === PARAMETERS ===
#start_node = '03933884aaf1d6b108397e5efe5c86bcf2d8ca8d2f700eda99db9214fc2712b134'
#end_node = '03d2fc638243a9bdaf4a4244510c73e5af874e6fcf99deb3d532019ba3e3f57e4d'
start_node = '03933884aaf1d6b108397e5efe5c86bcf2d8ca8d2f700eda99db9214fc2712b134'
end_node = '03ec72b4fa2664e0c51c7d303b61e88b3c070744f0c6e21b08653c5b8347cd4961'
payment_amount_msat = 1000000  # 1000 sat
top_k = 10
max_no_improve = 500  # Stop early if no better fee after 500 paths
max_hop = 10           # Only accept paths up to 6 hops
# === PARAMETERS END ===

G = build_graph(graph_info, payment_amount_msat=payment_amount_msat)

paths_by_fee, paths_by_timelock, paths_by_hops = find_topk_paths(
    G,
    start_node,
    end_node,
    payment_amount_msat,
    top_k=top_k,
    max_no_improve=max_no_improve,
    max_hop=max_hop
)

save_to_file(paths_by_fee, 'dataset/paths_by_fee.json')
save_to_file(paths_by_timelock, 'dataset/paths_by_timelock.json')
save_to_file(paths_by_hops, 'dataset/paths_by_hops.json')

print("Saved top-k paths sorted by fee, timelock, and hops!")
