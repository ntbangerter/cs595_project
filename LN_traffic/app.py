"""python backend for topk algorithm"""

from flask import Flask, request, jsonify, render_template
from best_path import load_graph, build_graph, find_best_path 

app = Flask(__name__)

# Load the graph once
graph_data = load_graph('dataset/graph_info.json')
G = build_graph(graph_data)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/network_stats')
def network_stats():
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    total_capacity_sat = sum(G[u][v]['capacity'] for u, v in G.edges)
    total_capacity_btc = total_capacity_sat / 100_000_000  # convert to BTC

    return jsonify({
        "total_nodes": num_nodes,
        "total_channels": num_edges,
        "total_capacity_btc": total_capacity_btc
    })

@app.route('/find_paths', methods=['POST'])
def find_paths():
    data = request.json
    start = data.get("start")
    end = data.get("end")
    optimize_by = data.get("optimize")
    payment_amount_msat = 1000000

    if not all([start, end, optimize_by]):
        return jsonify({"error": "Missing input parameters"}), 400

    weight_map = {
        "fee": "weight_fee",
        "hop": "weight_hop",
        "timelock": "weight_timelock"
    }

    if optimize_by not in weight_map:
        return jsonify({"error": "Invalid optimization target"}), 400

    try:
        result = find_best_path(G, start, end, payment_amount_msat, weight_type=weight_map[optimize_by])

        if result is None:
            return jsonify({"error": "No path found"}), 404

        return jsonify([result])  # Wrap in a list for front-end compatibility

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
