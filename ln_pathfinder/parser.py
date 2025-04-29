import json
from collections import defaultdict

# Load network_graph.json file
with open('dataset/raw_data.json', 'r') as f:
    graph = json.load(f)

nodes = graph['nodes']
edges = graph['edges']

# 1. Count node & channel number
num_nodes = len(nodes)
num_edges = len(edges)
print(f"Total number of nodes: {num_nodes}")
print(f"Total number of channels: {num_edges}")

# 2. Assign edges to nodes
node_channels = defaultdict(list)

for edge in edges:
    node1 = edge['node1_pub']
    node2 = edge['node2_pub']
    channel_id = edge['channel_id']
    capacity = int(edge['capacity'])  # unit: satoshi

    node1_policy = edge.get('node1_policy')
    node2_policy = edge.get('node2_policy')

    node_channels[node1].append({
        'channel_id': channel_id,
        'peer': node2,
        'capacity': capacity,
        'own_policy': node1_policy,
        'peer_policy': node2_policy
    })

    node_channels[node2].append({
        'channel_id': channel_id,
        'peer': node1,
        'capacity': capacity,
        'own_policy': node2_policy,
        'peer_policy': node1_policy
    })

# 3. Save new format to file
with open('dataset/graph_info.json', 'w') as f:
    json.dump(node_channels, f, indent=2)
