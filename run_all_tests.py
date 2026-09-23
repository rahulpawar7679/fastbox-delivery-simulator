"""
Automated batch test script validating all test cases in the current folder.
"""

import os
from simulator import FastBoxSimulator


def run_batch_tests():
    print("==========================================================")
    print("  FASTBOX LOGISTICS SIMULATOR - AUTOMATED BATCH RUNNER    ")
    print("==========================================================")

    # All files in current folder to test
    files_to_test = ["base_case.json"] + [f"test_case_{i}.json" for i in range(1, 11)]

    for filename in files_to_test:
        if not os.path.exists(filename):
            continue

        sim = FastBoxSimulator()
        sim.load_data(filename)
        sim.assign_packages()
        sim.simulate()
        report = sim.generate_report()

        delivered = sum(v["packages_delivered"] for k, v in report.items() if k != "best_agent")
        assert delivered == len(sim.packages), f"Delivery mismatch on {filename}"
        print(f"✓ {filename:<18}: PASSED (Packages Delivered: {delivered}/{len(sim.packages)}, Best Agent: {report['best_agent']})")

    print("\nAll test scenarios executed with zero exceptions and verified package integrity!")


if __name__ == "__main__":
    run_batch_tests()