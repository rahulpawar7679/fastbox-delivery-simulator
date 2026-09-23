# FastBox Delivery System Logistics Simulator

A production-grade logistics simulator engineered for the **Nexgensis Technologies Python Developer Assessment**.

---

## 📌 Explicit Engineering Assumptions & Trade-offs

In strict adherence to the assessment instructions regarding undefined scenarios and ambiguous logic, the following architectural choices were made:

### 1. Dual Schema Ingestion & Normalization
* **Observation:** The datasets present two differing JSON structures:
  * *Schema A (Base Case):* Warehouses and agents structured as lists of objects (`[{"id": "W1", "location": [0, 0]}]`) and packages referencing `warehouse_id`.
  * *Schema B (Test Cases 1–10):* Warehouses and agents structured as key-value dictionaries (`{"W1": [34, 29]}`) and packages referencing `warehouse`.
* **Decision:** The ingestion layer dynamically detects and normalizes both schemas into strongly typed `dataclass` models (`Coordinate`, `Warehouse`, `Package`, `Agent`). This eliminates runtime `KeyError` exceptions across varying input schemas.

### 2. Assignment Heuristic & Tie-Breaking
* **Assignment Criterion:** Packages are assigned based on the Euclidean distance from the agent's **initial coordinate** to the package's pickup warehouse:
  $$d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}$$
* **Deterministic Tie-Breaking:** If two agents are equidistant to a warehouse, deterministic tie-breaking selects the agent with the lexicographical lower ID (`A1` takes precedence over `A2`).

### 3. Sequential Route Execution
* **Routing Progression:** An agent travels from:
  $$\text{Current Position} \longrightarrow \text{Warehouse (Pickup)} \longrightarrow \text{Destination (Drop-off)}$$
* **State Retention:** For multiple packages assigned to the same agent, delivery occurs sequentially: the drop-off location of package $N$ becomes the departure point for package $N+1$.

### 4. Operational Efficiency Definition & Zero-Division Safety
* **Metric:**
  $$\text{Efficiency} = \frac{\text{Total Distance Traveled}}{\text{Packages Delivered}}$$
* **Interpretation:** In freight operations, a lower distance per delivery indicates superior operational efficiency. The agent with the **lowest non-zero efficiency score** is designated `best_agent`.
* **Idle Agent Guard:** In test cases with surplus agents (e.g., `A4` in `base_case.json` or `A1` in `test_case_10.json`), agents with zero deliveries default safely to `0.0` rather than causing an unhandled `ZeroDivisionError`, and are excluded from `best_agent` selection.

### 5. Delivery Invariant Guarantee
* $\sum \text{packages\_delivered} = \text{total input packages}$. Every single package is tracked, processed, and accounted for.

---

## 🌟 Bonus Features Included

1. **Terminal ASCII Grid Visualizer:** Scaled 2D ASCII grid rendering warehouse (`W`) and agent base (`A`) coordinates.
2. **Top Performer CSV Export:** Automatically outputs the winning agent's statistics to `top_performer.csv`.
3. **Traffic / Delay Simulation:** Configurable delay simulation modeling real-world transit delays.
4. **Comprehensive Verification Suite:** Automated batch verification across all test case files via `run_all_tests.py`.

---

## 🚀 Setup & Execution

### Run Base Simulation
```bash
python main.py base_case.json