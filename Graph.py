class Graph:
    """Graph class for representing the MRT and LRT network."""

    def __init__(self):
        self.edges = {}  # u -> v -> (minutes, meters)
        self.stations = set()

    def add_edge(self, u, v, minutes, meters):
        """Add a bidirectional edge between stations u and v."""
        self.stations.add(u)
        self.stations.add(v)

        if u not in self.edges:
            self.edges[u] = {}
        if v not in self.edges:
            self.edges[v] = {}

        self.edges[u][v] = (minutes, meters)
        self.edges[v][u] = (minutes, meters)

    def shortest_path(self, src, dst):
        """Find the shortest path from src to dst using Dijkstra's algorithm."""
        import heapq

        if src not in self.stations or dst not in self.stations:
            return [], 0, 0

        # Priority queue: (total_minutes, current_station, path)
        heap = [(0, src, [src])]
        visited = set()

        while heap:
            total_min, current, path = heapq.heappop(heap)

            if current == dst:
                # Calculate total distance in meters
                total_m = 0
                for i in range(len(path) - 1):
                    total_m += self.edges[path[i]][path[i+1]][1]
                return path, total_min, total_m

            if current in visited:
                continue

            visited.add(current)

            for neighbor, (minutes, meters) in self.edges.get(current, {}).items():
                if neighbor not in visited:
                    heapq.heappush(heap, (total_min + minutes, neighbor, path + [neighbor]))

        return [], 0, 0  # No path found

    def render_svg(self, path=None):
        """Generate SVG representation of the graph with optional path highlighting."""
        # This is a simplified version - you might want to customize the SVG generation
        # based on your specific needs and coordinates of the stations

        # Sample coordinates (you'll need to replace these with actual coordinates)
        station_coords = {
            # MRT-3 Stations
            "North Avenue": (100, 100),
            "Quezon Avenue": (150, 100),
            "GMA Kamuning": (200, 100),
            "Araneta Center-Cubao": (250, 100),
            "Santolan": (300, 100),
            "Ortigas": (350, 100),
            "Shaw Boulevard": (400, 100),
            "Boni": (450, 100),
            "Guadalupe": (500, 100),
            "Buendia": (550, 100),
            "Ayala": (600, 100),
            "Magallanes": (650, 100),
            "Taft Avenue": (700, 100),

            # LRT-1 Stations
            "Roosevelt": (100, 200),
            "Balintawak": (150, 200),
            "Monumento": (250, 200),
            "Blumentritt": (300, 200),
            "Tayuman": (350, 200),
            "Bambang": (400, 200),
            "Doroteo Jose": (450, 200),
            "Carriedo": (500, 200),
            "Central Terminal": (550, 200),
            "United Nations": (600, 200),
            "Pedro Gil": (650, 200),
            "Quirino": (700, 200),
            "Vito Cruz": (750, 200),
            "Gil Puyat": (800, 200),
            "Libertad": (850, 200),
            "EDSA": (900, 200),
            "Baclaran": (950, 200),

            # LRT-2 Stations
            "Recto": (450, 50),
            "Legarda": (500, 50),
            "Pureza": (550, 50),
            "V. Mapa": (600, 50),
            "J. Ruiz": (650, 50),
            "Gilmore": (700, 50),
            "Betty Go-Belmonte": (750, 50),
            "Araneta Center-Cubao": (800, 50),
            "Anonas": (850, 50),
            "Katipunan": (900, 50),
            "Santolan": (950, 50)
        }
        # Define line colors
        colors = {
            'MRT-3': '#FFD700',  # Gold
            'LRT-1': '#FF0000',  # Red
            'LRT-2': '#6F2DA8'   # Purple
        }

        # Define which stations belong to which line
        line_stations = {
            'MRT-3': [
                "North Avenue", "Quezon Avenue", "GMA Kamuning", "Araneta Center-Cubao",
                "Santolan", "Ortigas", "Shaw Boulevard", "Boni", "Guadalupe",
                "Buendia", "Ayala", "Magallanes", "Taft Avenue"
            ],
            'LRT-1': [
                "Roosevelt", "Balintawak", "Monumento", "Blumentritt", "Tayuman",
                "Bambang", "Doroteo Jose", "Carriedo", "Central Terminal",
                "United Nations", "Pedro Gil", "Quirino", "Vito Cruz",
                "Gil Puyat", "Libertad", "EDSA", "Baclaran"
            ],
            'LRT-2': [
                "Recto", "Legarda", "Pureza", "V. Mapa", "J. Ruiz",
                "Gilmore", "Betty Go-Belmonte", "Araneta Center-Cubao",
                "Anonas", "Katipunan", "Santolan"
            ]
        }

        # Create SVG content
        svg = [
            '<svg width="1200" height="600" xmlns="http://www.w3.org/2000/svg">',
            '  <rect width="100%" height="100%" fill="#1e1e2e"/>'  # Dark background
        ]

        # Draw connections (lines) first
        for line, stations in line_stations.items():
            for i in range(len(stations) - 1):
                u, v = stations[i], stations[i+1]
                if u in station_coords and v in station_coords:
                    x1, y1 = station_coords[u]
                    x2, y2 = station_coords[v]
                    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                              f'stroke="{colors[line]}" stroke-width="4" />')

        # Draw stations
        for station, (x, y) in station_coords.items():
            # Highlight stations in the path
            is_in_path = path and station in path
            fill = '#38bdf8' if is_in_path else '#555'  # Blue if in path, gray otherwise

            svg.append(f'<circle cx="{x}" cy="{y}" r="8" fill="{fill}" '
                      f'data-station="{station}" class="station" />')

            # Add station label
            svg.append(f'<text x="{x + 12}" y="{y + 5}" fill="white" font-size="12">{station}</text>')

        # Highlight the path if provided
        if path:
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                if u in station_coords and v in station_coords:
                    x1, y1 = station_coords[u]
                    x2, y2 = station_coords[v]
                    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                              f'stroke="#38bdf8" stroke-width="8" stroke-opacity="0.5" />')

        svg.append('</svg>')
        return '\n'.join(svg)


def create_atlas_graph():
    """Create and initialize the MRT/LRT graph with stations and connections."""
    graph = Graph()

    # MRT-3 Line (North Avenue to Taft Avenue)
    mrt3_stations = [
        "North Avenue", "Quezon Avenue", "GMA Kamuning", "Araneta Center-Cubao",
        "Santolan", "Ortigas", "Shaw Boulevard", "Boni", "Guadalupe",
        "Buendia", "Ayala", "Magallanes", "Taft Avenue"
    ]

    # LRT-1 Line (Roosevelt to Baclaran)
    lrt1_stations = [
        "Roosevelt", "Balintawak", "Monumento", "Blumentritt", "Tayuman",
        "Bambang", "Doroteo Jose", "Carriedo", "Central Terminal",
        "United Nations", "Pedro Gil", "Quirino", "Vito Cruz",
        "Gil Puyat", "Libertad", "EDSA", "Baclaran"
    ]

    # LRT-2 Line (Recto to Santolan)
    lrt2_stations = [
        "Recto", "Legarda", "Pureza", "V. Mapa", "J. Ruiz",
        "Gilmore", "Betty Go-Belmonte", "Araneta Center-Cubao",
        "Anonas", "Katipunan", "Santolan"
    ]

    # Add connections for MRT-3 (approx 2 minutes between stations, 1km apart)
    for i in range(len(mrt3_stations) - 1):
        graph.add_edge(mrt3_stations[i], mrt3_stations[i+1], 2, 1000)

    # Add connections for LRT-1 (approx 2 minutes between stations, 1km apart)
    for i in range(len(lrt1_stations) - 1):
        graph.add_edge(lrt1_stations[i], lrt1_stations[i+1], 2, 1000)

    # Add connections for LRT-2 (approx 2 minutes between stations, 1km apart)
    for i in range(len(lrt2_stations) - 1):
        graph.add_edge(lrt2_stations[i], lrt2_stations[i+1], 2, 1000)

    # Add transfer stations (connections between different lines)
    # Araneta Center-Cubao: MRT-3 <-> LRT-2
    graph.add_edge("Araneta Center-Cubao (MRT-3)", "Araneta Center-Cubao (LRT-2)", 5, 200)

    # Doroteo Jose: LRT-1 <-> LRT-2 (via Recto)
    graph.add_edge("Doroteo Jose", "Recto", 5, 200)

    # EDSA: LRT-1 <-> MRT-3 (via Taft Avenue)
    graph.add_edge("EDSA", "Taft Avenue", 5, 200)

    return graph

# Create a global instance of the graph
atlas_graph = create_atlas_graph()

