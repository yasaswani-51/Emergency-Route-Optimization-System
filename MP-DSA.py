import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import random
import math

# ============================================================
# EMERGENCY ROUTE OPTIMIZATION SYSTEM
# Graph Algorithms + Priority Queue + Dynamic Traffic
# ============================================================

LOCATIONS = {
    "Hospital": (100, 260),
    "Junction A": (230, 130),
    "Junction B": (230, 390),
    "Junction C": (390, 100),
    "Junction D": (390, 260),
    "Junction E": (390, 430),
    "Junction F": (560, 160),
    "Junction G": (560, 350),
    "Fire Station": (730, 260),
    "Accident Zone": (730, 90),
    "Police Station": (730, 430),
}

# (start, end, distance in km, normal speed in km/h)
ROAD_LIST = [
    ("Hospital", "Junction A", 4, 45),
    ("Hospital", "Junction B", 5, 40),
    ("Junction A", "Junction C", 3, 50),
    ("Junction A", "Junction D", 4, 45),
    ("Junction B", "Junction D", 3, 45),
    ("Junction B", "Junction E", 4, 40),
    ("Junction C", "Junction D", 2, 40),
    ("Junction C", "Junction F", 4, 50),
    ("Junction D", "Junction F", 3, 45),
    ("Junction D", "Junction G", 3, 40),
    ("Junction E", "Junction G", 3, 45),
    ("Junction F", "Fire Station", 4, 45),
    ("Junction F", "Accident Zone", 3, 35),
    ("Junction G", "Fire Station", 3, 50),
    ("Junction G", "Police Station", 4, 45),
    ("Fire Station", "Accident Zone", 3, 40),
    ("Police Station", "Accident Zone", 5, 40),
]

TRAFFIC_MULTIPLIER = {
    "Normal": 1.0,
    "Moderate": 1.5,
    "Heavy": 2.2,
    "Blocked": float("inf"),
}

PRIORITY = {"Critical": 1, "High": 2, "Normal": 3}
EMERGENCY_TYPES = ["Ambulance", "Fire Rescue", "Police"]


class EmergencyGraph:
    """Weighted graph stored using an adjacency list."""

    def __init__(self):
        self.adj = {node: [] for node in LOCATIONS}
        self.roads = []
        self.traffic = {}

        for i, (u, v, distance, speed) in enumerate(ROAD_LIST, 1):
            road_id = f"R{i}"
            self.roads.append((u, v, distance, speed, road_id))
            self.adj[u].append((v, distance, speed, road_id))
            self.adj[v].append((u, distance, speed, road_id))
            self.traffic[road_id] = "Normal"

    def edge_weight(self, distance, speed, road_id):
        """Return simulated travel time in minutes."""
        multiplier = TRAFFIC_MULTIPLIER[self.traffic[road_id]]

        if math.isinf(multiplier):
            return float("inf")

        normal_time = (distance / speed) * 60
        return normal_time * multiplier

    def dijkstra(self, source, destination, blocked_edges=None):
        """
        Dijkstra's shortest path algorithm.
        heapq is used as the min-priority queue.
        Weight = estimated travel time.
        """
        blocked_edges = blocked_edges or set()

        distance = {node: float("inf") for node in self.adj}
        parent = {node: None for node in self.adj}
        parent_road = {node: None for node in self.adj}

        distance[source] = 0
        min_heap = [(0, source)]

        while min_heap:
            current_time, u = heapq.heappop(min_heap)

            if current_time != distance[u]:
                continue

            if u == destination:
                break

            for v, km, speed, road_id in self.adj[u]:
                if road_id in blocked_edges:
                    continue

                weight = self.edge_weight(km, speed, road_id)
                if math.isinf(weight):
                    continue

                new_time = current_time + weight

                if new_time < distance[v]:
                    distance[v] = new_time
                    parent[v] = u
                    parent_road[v] = road_id
                    heapq.heappush(min_heap, (new_time, v))

        if distance[destination] == float("inf"):
            return None

        # Reconstruct path
        path = []
        roads = []
        current = destination

        while current is not None:
            path.append(current)
            if parent_road[current]:
                roads.append(parent_road[current])
            current = parent[current]

        path.reverse()
        roads.reverse()

        return {
            "path": path,
            "roads": roads,
            "time": distance[destination],
            "distance": self.path_distance(path),
        }

    def path_distance(self, path):
        total = 0

        for a, b in zip(path, path[1:]):
            for v, km, speed, road_id in self.adj[a]:
                if v == b:
                    total += km
                    break

        return total

    def alternative_route(self, source, destination, best):
        """
        Find an alternative by temporarily removing each road
        used by the optimal route and running Dijkstra again.
        """
        candidates = []

        for road_id in best["roads"]:
            result = self.dijkstra(
                source,
                destination,
                blocked_edges={road_id}
            )

            if result and result["path"] != best["path"]:
                candidates.append(result)

        return min(candidates, key=lambda x: x["time"]) if candidates else None


class EmergencyRouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Emergency Route Optimization System")
        self.root.geometry("1250x760")
        self.root.minsize(1100, 700)

        self.graph = EmergencyGraph()
        self.request_queue = []
        self.request_counter = 0
        self.active_route = None
        self.animation_step = 0

        self.setup_style()
        self.build_ui()
        self.draw_map()
        self.update_dashboard()

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 20, "bold")
        )
        style.configure(
            "Sub.TLabel",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=8
        )

    def build_ui(self):
        header = ttk.Frame(self.root, padding=(18, 12))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="🚑 Emergency Route Optimization System",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Label(
            header,
            text="Graph + Dijkstra + Priority Queue + Dynamic Traffic",
            style="Sub.TLabel"
        ).pack(side="right", pady=8)

        main = ttk.Frame(self.root, padding=(15, 5))
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, width=320)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        self.build_control_panel(left)

        center = ttk.Frame(main)
        center.pack(side="left", fill="both", expand=True)

        map_frame = ttk.LabelFrame(
            center,
            text="Live Road Network",
            padding=8
        )
        map_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            map_frame,
            bg="#f7f8fa",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_map())

        right = ttk.Frame(main, width=300)
        right.pack(side="right", fill="y", padx=(12, 0))
        right.pack_propagate(False)

        self.build_result_panel(right)

    def build_control_panel(self, parent):
        request = ttk.LabelFrame(
            parent,
            text="Emergency Request",
            padding=12
        )
        request.pack(fill="x", pady=(0, 10))

        ttk.Label(request, text="Emergency Type").pack(anchor="w")
        self.type_var = tk.StringVar(value="Ambulance")
        ttk.Combobox(
            request,
            textvariable=self.type_var,
            values=EMERGENCY_TYPES,
            state="readonly"
        ).pack(fill="x", pady=(3, 8))

        ttk.Label(request, text="Priority").pack(anchor="w")
        self.priority_var = tk.StringVar(value="Critical")
        ttk.Combobox(
            request,
            textvariable=self.priority_var,
            values=list(PRIORITY.keys()),
            state="readonly"
        ).pack(fill="x", pady=(3, 8))

        ttk.Label(request, text="Source").pack(anchor="w")
        self.source_var = tk.StringVar(value="Hospital")
        ttk.Combobox(
            request,
            textvariable=self.source_var,
            values=list(LOCATIONS.keys()),
            state="readonly"
        ).pack(fill="x", pady=(3, 8))

        ttk.Label(request, text="Destination").pack(anchor="w")
        self.destination_var = tk.StringVar(value="Accident Zone")
        ttk.Combobox(
            request,
            textvariable=self.destination_var,
            values=list(LOCATIONS.keys()),
            state="readonly"
        ).pack(fill="x", pady=(3, 10))

        ttk.Button(
            request,
            text="➕ Add Emergency",
            style="Action.TButton",
            command=self.add_request
        ).pack(fill="x", pady=3)

        ttk.Button(
            request,
            text="🚨 Dispatch Highest Priority",
            style="Action.TButton",
            command=self.dispatch_next
        ).pack(fill="x", pady=3)

        traffic = ttk.LabelFrame(
            parent,
            text="Traffic Control",
            padding=12
        )
        traffic.pack(fill="x", pady=(0, 10))

        ttk.Label(
            traffic,
            text="Select road and simulate traffic:"
        ).pack(anchor="w", pady=(0, 5))

        self.road_var = tk.StringVar(value="R1")
        ttk.Combobox(
            traffic,
            textvariable=self.road_var,
            values=[r[4] for r in self.graph.roads],
            state="readonly"
        ).pack(fill="x", pady=3)

        self.traffic_var = tk.StringVar(value="Normal")
        ttk.Combobox(
            traffic,
            textvariable=self.traffic_var,
            values=list(TRAFFIC_MULTIPLIER.keys()),
            state="readonly"
        ).pack(fill="x", pady=3)

        ttk.Button(
            traffic,
            text="🔄 Update Road Condition",
            command=self.update_traffic
        ).pack(fill="x", pady=3)

        ttk.Button(
            traffic,
            text="🎲 Random Traffic",
            command=self.random_traffic
        ).pack(fill="x", pady=3)

        ttk.Button(
            traffic,
            text="🟢 Clear Traffic",
            command=self.clear_traffic
        ).pack(fill="x", pady=3)

        queue = ttk.LabelFrame(
            parent,
            text="Emergency Queue",
            padding=8
        )
        queue.pack(fill="both", expand=True)

        columns = ("Priority", "Type", "Route")

        self.queue_tree = ttk.Treeview(
            queue,
            columns=columns,
            show="headings",
            height=7
        )

        for column in columns:
            self.queue_tree.heading(column, text=column)

        self.queue_tree.column(
            "Priority", width=60, anchor="center"
        )
        self.queue_tree.column(
            "Type", width=85, anchor="center"
        )
        self.queue_tree.column(
            "Route", width=120, anchor="center"
        )

        self.queue_tree.pack(fill="both", expand=True)

    def build_result_panel(self, parent):
        result = ttk.LabelFrame(
            parent,
            text="Optimization Result",
            padding=12
        )
        result.pack(fill="x", pady=(0, 10))

        self.status_label = ttk.Label(
            result,
            text="System Ready",
            font=("Segoe UI", 12, "bold")
        )
        self.status_label.pack(anchor="w", pady=(0, 10))

        self.route_text = tk.Text(
            result,
            height=8,
            width=30,
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            bg="#f7f8fa"
        )
        self.route_text.pack(fill="x")
        self.route_text.config(state="disabled")

        self.distance_label = ttk.Label(
            result,
            text="Distance: --"
        )
        self.distance_label.pack(anchor="w", pady=(8, 2))

        self.time_label = ttk.Label(
            result,
            text="Estimated Time: --"
        )
        self.time_label.pack(anchor="w", pady=2)

        self.alt_label = ttk.Label(
            result,
            text="Alternative: --"
        )
        self.alt_label.pack(anchor="w", pady=2)

        info = ttk.LabelFrame(
            parent,
            text="DSA Status",
            padding=12
        )
        info.pack(fill="x", pady=(0, 10))

        ttk.Label(
            info,
            text=(
                "✓ Weighted Graph\n"
                "✓ Adjacency List\n"
                "✓ Min Heap Priority Queue\n"
                "✓ Dijkstra Shortest Path\n"
                "✓ Path Reconstruction\n"
                "✓ Alternative Route"
            ),
            justify="left"
        ).pack(anchor="w")

        stats = ttk.LabelFrame(
            parent,
            text="System Statistics",
            padding=12
        )
        stats.pack(fill="x")

        self.stats_label = ttk.Label(stats, text="")
        self.stats_label.pack(anchor="w")

    def draw_map(self):
        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")

        self.canvas.create_text(
            20,
            18,
            anchor="w",
            text="Traffic-aware weighted graph",
            font=("Segoe UI", 11, "bold")
        )

        # Draw roads
        for u, v, distance, speed, road_id in self.graph.roads:
            x1, y1 = LOCATIONS[u]
            x2, y2 = LOCATIONS[v]

            condition = self.graph.traffic[road_id]

            dash = None
            if condition == "Moderate":
                dash = (8, 5)
            elif condition == "Heavy":
                dash = (3, 3)
            elif condition == "Blocked":
                dash = (12, 5)

            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#9aa0a6",
                width=7 if condition == "Blocked" else 5,
                dash=dash
            )

            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2

            self.canvas.create_rectangle(
                mx - 17,
                my - 9,
                mx + 17,
                my + 9,
                fill="white",
                outline=""
            )

            self.canvas.create_text(
                mx,
                my,
                text=road_id,
                font=("Segoe UI", 8, "bold")
            )

        # Highlight optimal route
        if self.active_route:
            path = self.active_route["path"]

            for a, b in zip(path, path[1:]):
                x1, y1 = LOCATIONS[a]
                x2, y2 = LOCATIONS[b]

                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#1565c0",
                    width=9
                )
                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill="#e3f2fd",
                    width=4
                )

        # Draw locations
        for name, (x, y) in LOCATIONS.items():
            on_route = (
                self.active_route
                and name in self.active_route["path"]
            )

            self.canvas.create_oval(
                x - 22,
                y - 22,
                x + 22,
                y + 22,
                fill="white",
                outline="#1565c0" if on_route else "#4a4f55",
                width=4 if on_route else 2
            )

            short_name = name.replace("Junction ", "J")

            self.canvas.create_text(
                x,
                y,
                text=short_name,
                font=("Segoe UI", 8, "bold")
            )

            self.canvas.create_text(
                x,
                y + 34,
                text=name,
                font=("Segoe UI", 8)
            )

        self.canvas.create_text(
            20,
            625,
            anchor="w",
            text=(
                "Traffic:  Normal | Moderate | Heavy | Blocked"
            ),
            font=("Segoe UI", 9)
        )

    def add_request(self):
        source = self.source_var.get()
        destination = self.destination_var.get()

        if source == destination:
            messagebox.showwarning(
                "Invalid Request",
                "Source and destination must be different."
            )
            return

        self.request_counter += 1

        request = {
            "id": self.request_counter,
            "priority": PRIORITY[self.priority_var.get()],
            "priority_name": self.priority_var.get(),
            "type": self.type_var.get(),
            "source": source,
            "destination": destination,
        }

        # Priority Queue:
        # lower number = higher emergency priority
        heapq.heappush(
            self.request_queue,
            (
                request["priority"],
                request["id"],
                request
            )
        )

        self.refresh_queue()
        self.update_dashboard()

        self.status_label.config(
            text=f"Emergency #{request['id']} added"
        )

    def dispatch_next(self):
        if not self.request_queue:
            messagebox.showinfo(
                "Queue Empty",
                "There are no pending emergency requests."
            )
            return

        _, _, request = heapq.heappop(self.request_queue)

        best = self.graph.dijkstra(
            request["source"],
            request["destination"]
        )

        if not best:
            self.active_route = None
            self.status_label.config(text="No available route")
            self.show_route_text(
                "No route is currently available.\n"
                "Try changing the traffic conditions."
            )
            self.refresh_queue()
            self.draw_map()
            return

        alternative = self.graph.alternative_route(
            request["source"],
            request["destination"],
            best
        )

        best["alternative"] = alternative
        best["request"] = request
        self.active_route = best

        self.show_result(best)
        self.refresh_queue()
        self.draw_map()
        self.update_dashboard()

        self.animate_route()

    def refresh_queue(self):
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)

        pending = sorted(
            self.request_queue,
            key=lambda x: (x[0], x[1])
        )

        for _, _, request in pending:
            self.queue_tree.insert(
                "",
                "end",
                values=(
                    request["priority_name"],
                    request["type"],
                    f"{request['source']} → {request['destination']}"
                )
            )

    def update_traffic(self):
        road = self.road_var.get()
        condition = self.traffic_var.get()

        self.graph.traffic[road] = condition

        self.draw_map()
        self.update_dashboard()

        self.status_label.config(
            text=f"{road} updated to {condition}"
        )

        if self.active_route:
            self.recalculate_current(
                self.active_route["request"]
            )

    def random_traffic(self):
        conditions = list(TRAFFIC_MULTIPLIER.keys())

        for road_id in self.graph.traffic:
            self.graph.traffic[road_id] = random.choices(
                conditions,
                weights=[55, 25, 15, 5],
                k=1
            )[0]

        self.draw_map()
        self.update_dashboard()

        if self.active_route:
            self.recalculate_current(
                self.active_route["request"]
            )

        self.status_label.config(
            text="Traffic conditions randomized"
        )

    def clear_traffic(self):
        for road_id in self.graph.traffic:
            self.graph.traffic[road_id] = "Normal"

        self.draw_map()
        self.update_dashboard()

        if self.active_route:
            self.recalculate_current(
                self.active_route["request"]
            )

        self.status_label.config(
            text="All roads restored to Normal"
        )

    def recalculate_current(self, request):
        best = self.graph.dijkstra(
            request["source"],
            request["destination"]
        )

        if best:
            best["alternative"] = self.graph.alternative_route(
                request["source"],
                request["destination"],
                best
            )
            best["request"] = request
            self.active_route = best
            self.show_result(best)
        else:
            self.active_route = None
            self.status_label.config(
                text="Route unavailable"
            )

        self.draw_map()

    def show_route_text(self, text):
        self.route_text.config(state="normal")
        self.route_text.delete("1.0", "end")
        self.route_text.insert("1.0", text)
        self.route_text.config(state="disabled")

    def show_result(self, result):
        request = result["request"]

        self.status_label.config(
            text=(
                f"🚨 {request['type']} | "
                f"{request['priority_name']} Priority"
            )
        )

        route = "  →  ".join(result["path"])

        text = (
            f"REQUEST #{request['id']}\n"
            f"{request['source']} → {request['destination']}\n\n"
            f"OPTIMAL ROUTE\n"
            f"{route}\n\n"
            f"Roads: {', '.join(result['roads'])}"
        )

        self.show_route_text(text)

        self.distance_label.config(
            text=f"Distance: {result['distance']:.1f} km"
        )

        self.time_label.config(
            text=f"Estimated Time: {result['time']:.1f} min"
        )

        if result.get("alternative"):
            alt = result["alternative"]
            self.alt_label.config(
                text=(
                    f"Alternative: "
                    f"{alt['distance']:.1f} km / "
                    f"{alt['time']:.1f} min"
                )
            )
        else:
            self.alt_label.config(
                text="Alternative: Not available"
            )

    def update_dashboard(self):
        locations = len(self.graph.adj)
        roads = len(self.graph.roads)
        pending = len(self.request_queue)

        normal = sum(
            1 for x in self.graph.traffic.values()
            if x == "Normal"
        )

        blocked = sum(
            1 for x in self.graph.traffic.values()
            if x == "Blocked"
        )

        self.stats_label.config(
            text=(
                f"Locations: {locations}\n"
                f"Roads: {roads}\n"
                f"Pending Emergencies: {pending}\n"
                f"Normal Roads: {normal}\n"
                f"Blocked Roads: {blocked}"
            )
        )

    def animate_route(self):
        if not self.active_route:
            return

        self.animation_step = 0
        self.animate_step()

    def animate_step(self):
        if not self.active_route:
            return

        path = self.active_route["path"]

        if self.animation_step >= len(path):
            return

        self.draw_map()

        node = path[self.animation_step]
        x, y = LOCATIONS[node]

        self.canvas.create_oval(
            x - 9,
            y - 9,
            x + 9,
            y + 9,
            fill="#d32f2f",
            outline="white",
            width=2
        )

        self.canvas.create_text(
            x,
            y - 16,
            text="🚨",
            font=("Segoe UI Emoji", 13)
        )

        self.animation_step += 1
        self.root.after(650, self.animate_step)


if __name__ == "__main__":
    root = tk.Tk()
    app = EmergencyRouteApp(root)
    root.mainloop()
