"""Simple Tkinter interface for traffic based route guidance."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from integration import (
    k_shortest_routes,
    load_road_links,
    predict_next_hourly_flow,
)


class RouteGuidanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Based Route Guidance")
        self.geometry("760x580")
        self.minsize(640, 460)
        self.network_path = tk.StringVar(value="data/boroondara_roads.csv")
        self.model_name = tk.StringVar(value="gru")
        self.origin = tk.StringVar()
        self.destination = tk.StringVar()
        self.flow_override = tk.StringVar()
        self.status = tk.StringVar(value="Choose a road network and enter an origin and destination.")
        self._build()

    def _build(self):
        panel = ttk.Frame(self, padding=16)
        panel.pack(fill="both", expand=True)
        panel.columnconfigure(1, weight=1)
        panel.rowconfigure(7, weight=1)

        ttk.Label(panel, text="Traffic Based Route Guidance", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
        )
        ttk.Label(panel, text="Road network CSV").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(panel, textvariable=self.network_path).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(panel, text="Browse…", command=self._browse).grid(row=1, column=2)

        ttk.Label(panel, text="Origin SCATS site").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(panel, textvariable=self.origin).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Label(panel, text="Destination SCATS site").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(panel, textvariable=self.destination).grid(row=3, column=1, sticky="ew", padx=8)

        ttk.Label(panel, text="Prediction model").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Combobox(panel, textvariable=self.model_name, values=("gru", "lstm", "tcn"), state="readonly").grid(
            row=4, column=1, sticky="w", padx=8
        )
        ttk.Label(panel, text="Traffic flow override (veh/hour, optional)").grid(
            row=5, column=0, sticky="w", pady=4
        )
        ttk.Entry(panel, textvariable=self.flow_override).grid(row=5, column=1, sticky="ew", padx=8)

        ttk.Button(panel, text="Find up to 5 routes", command=self._find_routes).grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=(10, 12)
        )
        self.results = tk.Text(panel, height=15, wrap="word", state="disabled", font=("Consolas", 10))
        self.results.grid(row=7, column=0, columnspan=3, sticky="nsew")
        ttk.Label(panel, textvariable=self.status, foreground="#555", wraplength=700).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(10, 0)
        )

    def _browse(self):
        selected = filedialog.askopenfilename(
            title="Select road network CSV",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if selected:
            self.network_path.set(selected)

    def _write_results(self, text: str):
        self.results.configure(state="normal")
        self.results.delete("1.0", "end")
        self.results.insert("1.0", text)
        self.results.configure(state="disabled")

    def _find_routes(self):
        try:
            origin = int(self.origin.get().strip())
            destination = int(self.destination.get().strip())
            links = load_road_links(self.network_path.get().strip())
            override = self.flow_override.get().strip()
            if override:
                flow = float(override)
                if flow < 0:
                    raise ValueError("Traffic flow cannot be negative.")
                hourly_flow = {link.traffic_site: flow for link in links}
                flow_source = f"manual override: {flow:g} vehicles/hour"
            else:
                flow = predict_next_hourly_flow(self.model_name.get())
                hourly_flow = {link.traffic_site: flow for link in links}
                flow_source = f"{self.model_name.get().upper()} prediction: {flow:.1f} vehicles/hour"

            routes = k_shortest_routes(links, origin, destination, hourly_flow, k=5)
            if not routes:
                self._write_results(f"No route found from {origin} to {destination}.")
            else:
                lines = [f"Traffic input: {flow_source}", "", "Routes ranked by estimated travel time:"]
                for index, route in enumerate(routes, start=1):
                    lines.append(
                        f"{index}. {' → '.join(map(str, route.path))}\n"
                        f"   Estimated travel time: {route.cost:.2f} minutes"
                    )
                self._write_results("\n".join(lines))
            self.status.set(
                "Times currently use the placeholder conversion in integration.py. "
                "Replace it with the course traffic-to-travel-time formula before reporting results."
            )
        except (ValueError, OSError, KeyError) as error:
            messagebox.showerror("Unable to find routes", str(error))
            self.status.set("Check the network file, endpoints, model checkpoint, and traffic data.")


def main():
    RouteGuidanceApp().mainloop()


if __name__ == "__main__":
    main()
