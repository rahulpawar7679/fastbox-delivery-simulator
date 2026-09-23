"""
Entrypoint for FastBox simulation runs.
"""

import sys
import json
from simulator import FastBoxSimulator, export_top_performer_to_csv, render_ascii_map


def main():
    file_path = sys.argv[1] if len(sys.argv) > 1 else "base_case.json"
    print(f"Initializing FastBox Logistics Engine with: {file_path}")

    sim = FastBoxSimulator()
    sim.load_data(file_path)

    # ASCII Map Visualizer (Bonus)
    render_ascii_map(sim.warehouses, sim.agents)

    # Core Execution
    sim.assign_packages()
    sim.simulate()

    # Generate and save report
    report = sim.generate_report()
    sim.save_report("report.json")
    print("Simulation completed successfully. Report saved to report.json:")
    print(json.dumps(report, indent=4))

    # Export CSV (Bonus)
    export_top_performer_to_csv(report)
    print("\nTop performer metrics successfully written to top_performer.csv")


if __name__ == "__main__":
    main()