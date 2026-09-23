"""
FastBox Logistics Simulator Engine
Author: Rahul Pawar
Description: Logistics simulation engine handling warehouse-to-agent allocation,
             sequential trip simulation, dynamic events, and reporting.
"""

import math
import json
import csv
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass(frozen=True)
class Coordinate:
    x: float
    y: float

    def distance_to(self, other: "Coordinate") -> float:
        """Calculates 2D Euclidean distance."""
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class Warehouse:
    id: str
    location: Coordinate


@dataclass
class Package:
    id: str
    warehouse_id: str
    destination: Coordinate


@dataclass
class Agent:
    id: str
    initial_location: Coordinate
    current_location: Coordinate
    packages_delivered: int = 0
    total_distance: float = 0.0
    total_delay_minutes: float = 0.0
    route_history: List[Tuple[float, float]] = field(default_factory=list)

    @property
    def efficiency(self) -> float:
        """
        Calculates distance per package delivered.
        Safe fallback to 0.0 prevents ZeroDivisionError for unassigned agents.
        """
        if self.packages_delivered == 0:
            return 0.0
        return round(self.total_distance / self.packages_delivered, 2)


class FastBoxSimulator:
    def __init__(self, routing_mode: str = "sequential", enable_delays: bool = False):
        self.routing_mode = routing_mode
        self.enable_delays = enable_delays
        self.warehouses: Dict[str, Warehouse] = {}
        self.agents: Dict[str, Agent] = {}
        self.packages: List[Package] = []
        self.assignments: Dict[str, List[Package]] = {}

    def load_data(self, filepath: str) -> None:
        """Parses and normalizes dual-schema variations across input files."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. Normalize Warehouses (supports dict mapping and list of objects)
        self.warehouses = {}
        raw_warehouses = data.get("warehouses", {})
        if isinstance(raw_warehouses, list):
            for item in raw_warehouses:
                loc = item.get("location", [0, 0])
                self.warehouses[item["id"]] = Warehouse(id=item["id"], location=Coordinate(loc[0], loc[1]))
        elif isinstance(raw_warehouses, dict):
            for w_id, loc in raw_warehouses.items():
                self.warehouses[w_id] = Warehouse(id=w_id, location=Coordinate(loc[0], loc[1]))

        # 2. Normalize Agents
        self.agents = {}
        self.assignments = {}
        raw_agents = data.get("agents", {})
        if isinstance(raw_agents, list):
            for item in raw_agents:
                loc = item.get("location", [0, 0])
                coord = Coordinate(loc[0], loc[1])
                self.agents[item["id"]] = Agent(
                    id=item["id"],
                    initial_location=coord,
                    current_location=coord,
                    route_history=[(coord.x, coord.y)]
                )
                self.assignments[item["id"]] = []
        elif isinstance(raw_agents, dict):
            for a_id, loc in raw_agents.items():
                coord = Coordinate(loc[0], loc[1])
                self.agents[a_id] = Agent(
                    id=a_id,
                    initial_location=coord,
                    current_location=coord,
                    route_history=[(coord.x, coord.y)]
                )
                self.assignments[a_id] = []

        # 3. Normalize Packages
        self.packages = []
        for pkg in data.get("packages", []):
            wh_id = pkg.get("warehouse") or pkg.get("warehouse_id")
            dest = pkg.get("destination", [0, 0])
            self.packages.append(
                Package(
                    id=pkg["id"],
                    warehouse_id=wh_id,
                    destination=Coordinate(dest[0], dest[1]),
                )
            )

    def assign_packages(self) -> None:
        """
        Assigns package to nearest agent based on initial Euclidean distance to warehouse.
        Tie-breaker: Lexicographical order on agent_id (e.g., A1 beats A2).
        """
        for pkg in self.packages:
            warehouse = self.warehouses[pkg.warehouse_id]
            best_agent_id: Optional[str] = None
            min_dist = float("inf")

            for a_id in sorted(self.agents.keys()):
                agent = self.agents[a_id]
                dist = agent.initial_location.distance_to(warehouse.location)
                if dist < min_dist:
                    min_dist = dist
                    best_agent_id = a_id

            if best_agent_id:
                self.assignments[best_agent_id].append(pkg)

    def simulate(self) -> None:
        """Executes deliveries: Current location -> Warehouse -> Destination."""
        for a_id, pkgs in self.assignments.items():
            agent = self.agents[a_id]
            for pkg in pkgs:
                warehouse = self.warehouses[pkg.warehouse_id]

                # Leg 1: Current position to warehouse
                dist_to_wh = agent.current_location.distance_to(warehouse.location)
                # Leg 2: Warehouse to drop-off point
                dist_to_dest = warehouse.location.distance_to(pkg.destination)

                agent.total_distance += dist_to_wh + dist_to_dest

                # Bonus: Handling delay simulation
                if self.enable_delays:
                    delay = round(random.uniform(5.0, 15.0), 1)
                    agent.total_delay_minutes += delay

                if self.routing_mode == "sequential":
                    agent.current_location = pkg.destination
                else:
                    agent.current_location = agent.initial_location

                agent.route_history.append((pkg.destination.x, pkg.destination.y))
                agent.packages_delivered += 1

            agent.total_distance = round(agent.total_distance, 2)

    def generate_report(self) -> Dict[str, Any]:
        """Generates required operational report."""
        report: Dict[str, Any] = {}
        best_agent: Optional[str] = None
        best_efficiency = float("inf")

        for a_id in sorted(self.agents.keys()):
            agent = self.agents[a_id]
            eff = agent.efficiency

            report[a_id] = {
                "packages_delivered": agent.packages_delivered,
                "total_distance": agent.total_distance,
                "efficiency": eff,
            }

            if agent.packages_delivered > 0 and eff < best_efficiency:
                best_efficiency = eff
                best_agent = a_id

        report["best_agent"] = best_agent
        return report

    def save_report(self, filepath: str = "report.json") -> None:
        """Saves output to report.json."""
        report = self.generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)


def export_top_performer_to_csv(report: Dict[str, Any], filepath: str = "top_performer.csv") -> None:
    """Bonus: Exports highest efficiency agent to CSV."""
    best_id = report.get("best_agent")
    if not best_id or best_id not in report:
        return

    data = report[best_id]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Agent_ID", "Packages_Delivered", "Total_Distance", "Efficiency"])
        writer.writerow([
            best_id,
            data["packages_delivered"],
            data["total_distance"],
            data["efficiency"]
        ])


def render_ascii_map(warehouses: Dict[str, Warehouse], agents: Dict[str, Agent], width: int = 40, height: int = 15) -> None:
    """Bonus: Visualizes operational layout on terminal."""
    grid = [["." for _ in range(width)] for _ in range(height)]
    max_x = max([w.location.x for w in warehouses.values()] + [a.initial_location.x for a in agents.values()] + [100])
    max_y = max([w.location.y for w in warehouses.values()] + [a.initial_location.y for a in agents.values()] + [100])

    def scale(c: Coordinate):
        gx = min(width - 1, max(0, int((c.x / max_x) * (width - 1))))
        gy = min(height - 1, max(0, int((c.y / max_y) * (height - 1))))
        return gx, gy

    for w in warehouses.values():
        gx, gy = scale(w.location)
        grid[height - 1 - gy][gx] = "W"

    for a in agents.values():
        gx, gy = scale(a.initial_location)
        grid[height - 1 - gy][gx] = "A"

    print("\n--- Operational Grid Map (W = Warehouse, A = Agent Base) ---")
    for row in grid:
        print(" ".join(row))
    print("------------------------------------------------------------\n")