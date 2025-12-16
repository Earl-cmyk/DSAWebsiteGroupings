class Graph:
    def __init__(self):
        self.edges = {}
        self.stations = set()

    def add_edge(self, u, v, minutes, meters):
        self.stations.add(u)
        self.stations.add(v)
        self.edges.setdefault(u, {})[v] = (minutes, meters)
        self.edges.setdefault(v, {})[u] = (minutes, meters)

    def shortest_path(self, src, dst):
        import heapq

        if src not in self.stations or dst not in self.stations:
            return [], 0, 0

        heap = [(0, src, [src])]
        visited = set()

        while heap:
            mins, cur, path = heapq.heappop(heap)
            if cur == dst:
                meters = sum(self.edges[path[i]][path[i+1]][1] for i in range(len(path) - 1))
                return path, mins, meters
            if cur in visited:
                continue
            visited.add(cur)
            for nxt, (m, _) in self.edges.get(cur, {}).items():
                if nxt not in visited:
                    heapq.heappush(heap, (mins + m, nxt, path + [nxt]))

        return [], 0, 0

    def render_svg(self, path=None):
        station_coords = {
            "North Avenue": (100, 120),
            "Quezon Avenue": (160, 120),
            "GMA Kamuning": (220, 120),
            "Araneta Center-Cubao": (280, 120),
            "Santolan": (340, 120),
            "Ortigas": (400, 120),
            "Shaw Boulevard": (460, 120),
            "Boni": (520, 120),
            "Guadalupe": (580, 120),
            "Buendia": (640, 120),
            "Ayala": (700, 120),
            "Magallanes": (760, 120),
            "Taft Avenue": (820, 120),

            "Roosevelt": (100, 260),
            "Balintawak": (160, 260),
            "Monumento": (220, 260),
            "Blumentritt": (280, 260),
            "Tayuman": (340, 260),
            "Bambang": (400, 260),
            "Doroteo Jose": (460, 260),
            "Carriedo": (520, 260),
            "Central Terminal": (580, 260),
            "United Nations": (640, 260),
            "Pedro Gil": (700, 260),
            "Quirino": (760, 260),
            "Vito Cruz": (820, 260),
            "Gil Puyat": (880, 260),
            "Libertad": (940, 260),
            "EDSA": (1000, 260),
            "Baclaran": (1060, 260),

            "Recto": (460, 60),
            "Legarda": (520, 60),
            "Pureza": (580, 60),
            "V. Mapa": (640, 60),
            "J. Ruiz": (700, 60),
            "Gilmore": (760, 60),
            "Betty Go-Belmonte": (820, 60),
            "Anonas": (880, 60),
            "Katipunan": (940, 60),
            "Marikina-Pasig": (1000, 60),
            "Antipolo": (1060, 60)
        }

        lines = {
            "MRT-3": ("#FFD700", [
                "North Avenue", "Quezon Avenue", "GMA Kamuning", "Araneta Center-Cubao",
                "Santolan", "Ortigas", "Shaw Boulevard", "Boni", "Guadalupe",
                "Buendia", "Ayala", "Magallanes", "Taft Avenue"
            ]),
            "LRT-1": ("#FF0000", [
                "Roosevelt", "Balintawak", "Monumento", "Blumentritt", "Tayuman",
                "Bambang", "Doroteo Jose", "Carriedo", "Central Terminal",
                "United Nations", "Pedro Gil", "Quirino", "Vito Cruz",
                "Gil Puyat", "Libertad", "EDSA", "Baclaran"
            ]),
            "LRT-2": ("#6F2DA8", [
                "Recto", "Legarda", "Pureza", "V. Mapa", "J. Ruiz",
                "Gilmore", "Betty Go-Belmonte", "Araneta Center-Cubao",
                "Anonas", "Katipunan", "Marikina-Pasig", "Antipolo"
            ])
        }

        svg = [
            '<svg width="3000" height="1600" viewBox="0 0 3000 1600" xmlns="http://www.w3.org/2000/svg">',
            '<rect width="100%" height="100%" fill="#0b1220"/>'
        ]


        for _, (color, stations) in lines.items():
            for i in range(len(stations) - 1):
                a, b = stations[i], stations[i + 1]
                if a in station_coords and b in station_coords:
                    x1, y1 = station_coords[a]
                    x2, y2 = station_coords[b]
                    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>')

        if path:
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                if a in station_coords and b in station_coords:
                    x1, y1 = station_coords[a]
                    x2, y2 = station_coords[b]
                    svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#38bdf8" stroke-width="8" stroke-opacity="0.6" stroke-linecap="round"/>')

        for name, (x, y) in station_coords.items():
            active = path and name in path
            svg.append(f'<circle cx="{x}" cy="{y}" r="8" class="station{" locked" if active else ""}" data-station="{name}"/>')
            parts = name.split(" ")
            mid = max(1, len(parts) // 2)
            line1 = " ".join(parts[:mid])
            line2 = " ".join(parts[mid:])
            is_top = (hash(name) % 2 == 0)
            base_y = y - 18 if is_top else y + 30

            svg.append(f'''
            <text x="{x}" y="{base_y}"
                text-anchor="middle"
                class="station-label">
                <tspan x="{x}" dy="0">{line1}</tspan>
                <tspan x="{x}" dy="12">{line2}</tspan>
            </text>
            ''')
        svg.append('</svg>')
        return '\n'.join(svg)


def create_atlas_graph():
    g = Graph()

    mrt3 = [
        "North Avenue", "Quezon Avenue", "GMA Kamuning", "Araneta Center-Cubao",
        "Santolan", "Ortigas", "Shaw Boulevard", "Boni", "Guadalupe",
        "Buendia", "Ayala", "Magallanes", "Taft Avenue"
    ]

    lrt1 = [
        "Roosevelt", "Balintawak", "Monumento", "Blumentritt", "Tayuman",
        "Bambang", "Doroteo Jose", "Carriedo", "Central Terminal",
        "United Nations", "Pedro Gil", "Quirino", "Vito Cruz",
        "Gil Puyat", "Libertad", "EDSA", "Baclaran"
    ]

    lrt2 = [
        "Recto", "Legarda", "Pureza", "V. Mapa", "J. Ruiz",
        "Gilmore", "Betty Go-Belmonte", "Araneta Center-Cubao",
        "Anonas", "Katipunan", "Marikina-Pasig", "Antipolo"
    ]

    for line in (mrt3, lrt1, lrt2):
        for i in range(len(line) - 1):
            g.add_edge(line[i], line[i + 1], 2, 1000)

    g.add_edge("Doroteo Jose", "Recto", 5, 200)
    g.add_edge("EDSA", "Taft Avenue", 5, 200)
    g.add_edge("Araneta Center-Cubao", "Araneta Center-Cubao", 0, 0)

    return g


atlas_graph = create_atlas_graph()

PIXELS_PER_KM = 120

def scaled_x(start, distances):
    x = start
    out = []
    for m in distances:
        out.append(x)
        x += (m / 1000) * PIXELS_PER_KM
    return out
