# ⚡ Lightning Network Routing Demo

This project is a simple web application for demonstrating routing algorithms on the Lightning Network (LN).

It allows users to:
- Input a start node and an end node.
- Choose an optimization objective: minimize total fee, minimize hop count, or minimize total timelock.
- View the computed best route(s) based on the selected criteria.

---

---

## 🚀 How to Run

1. **Install Python dependencies** (Flask + NetworkX)

```bash
pip install flask networkx
```

2. **Run the backend server**

```bash
python app.py
```

3. **Open the web page**

  Visit http://127.0.0.1:5000 in your browser.

