"""python backend for topk algorithm"""

from flask import Flask, request, jsonify, render_template
from topk_paths import load_graph, build_graph, find_topk_paths  

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

# Load graph once at startup
graph_data = load_graph('dataset/graph_info.json')
G = build_graph(graph_data)

@app.route('/find_paths', methods=['POST'])
def find_paths():
    data = request.json
    start = data.get("start")
    end = data.get("end")
    optimize_by = data.get("optimize")
    payment_amount_msat = 1000000

    # Validate input
    if not all([start, end, optimize_by]):
        return jsonify({"error": "Missing input parameters"}), 400

    try:
        # Use lazy Yen's method
        all_paths = find_topk_paths(G, start, end, payment_amount_msat, k=10, samples=50)

        if not all_paths:
            return jsonify({"error": "No paths found"}), 404

        # Sort by selected optimization
        key_func = {
            'fee': lambda x: x['total_fee_msat'],
            'hop': lambda x: x['hops'],
            'timelock': lambda x: x['total_timelock']
        }.get(optimize_by)

        if not key_func:
            return jsonify({"error": "Invalid optimization target"}), 400

        top_paths = sorted(all_paths, key=key_func)[:10]
        return jsonify(top_paths)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
