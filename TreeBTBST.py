import uuid

queue = []
stack = []
tree_root = None
tree_roots = []
bst_root = None
bt_roots = []
graph_vertices = []
graph_edges = {}
edge_weights = {}
pending_deletes = {}
pending_subtrees = {}

class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None
        # support n-ary children for general Tree demo
        self.children = []
        try:
            self.id = str(uuid.uuid4())
        except Exception:
            self.id = None

def escape_text(text):
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))

def render_queue_svg():
    width = max(300, 120 * max(1, len(queue)))
    height = 120
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for i, val in enumerate(queue):
        x = 20 + i * 120
        parts.append(f'<rect x="{x}" y="30" width="100" height="60" rx="8" fill="#4cc9ff" stroke="#fff"/>')
        parts.append(
            f'<text x="{x + 50}" y="65" font-size="18" text-anchor="middle" fill="#000">{escape_text(val)}</text>')
    parts.append('</svg>')
    return "".join(parts)


def render_stack_svg():
    width = 200
    height = max(120, 80 * len(stack) + 20)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for i, val in enumerate(reversed(stack)):
        y = 20 + i * 80
        parts.append(f'<rect x="40" y="{y}" width="120" height="60" rx="8" fill="#90f1a9" stroke="#fff"/>')
        parts.append(
            f'<text x="100" y="{y + 36}" font-size="18" text-anchor="middle" fill="#000">{escape_text(val)}</text>')
    parts.append('</svg>')
    return "".join(parts)


def render_generic_tree_svg(root):
    if not root:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="800" height="200"></svg>'

    width, height = 1000, 600
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']

    def traverse(node, x, y, level, span=200):
        if not node:
            return
        # determine children (support both children list and legacy left/right)
        childs = []
        if getattr(node, 'children', None):
            childs = [c for c in node.children if c]
        else:
            if node.left: childs.append(node.left)
            if node.right: childs.append(node.right)

        n = len(childs)
        gap = span // max(1, n)
        start_x = x - (gap * (n - 1)) / 2

        for i, ch in enumerate(childs):
            cx = int(start_x + i * gap)
            cy = y + 100
            # edge weight lookup
            w = edge_weights.get((getattr(node, 'id', ''), getattr(ch, 'id', '')), 1)
            parts.append(f'<line x1="{x}" y1="{y}" x2="{cx}" y2="{cy}" stroke="#fff" stroke-width="{1 + (w - 1)}"/>')
            if w > 1:
                mx = (x + cx) // 2
                my = (y + cy) // 2
                parts.append(f'<text x="{mx}" y="{my}" font-size="14" text-anchor="middle" fill="#fff">{w}</text>')
            traverse(ch, cx, cy, level + 1, max(60, span // 2))

        # include data-id and data-val attributes so client-side can bind click handlers
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="25" fill="#f8c537" stroke="#fff" data-id="{getattr(node, "id", "")}" data-val="{escape_text(node.val)}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 5}" font-size="18" text-anchor="middle" fill="#000">{escape_text(node.val)}</text>')

    traverse(root, width // 2, 60, 1, 400)
    parts.append('</svg>')
    return "".join(parts)


def render_tree_forest_svg(roots):
    # render multiple general trees stacked vertically
    if not roots:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 200" width="1000" height="200"></svg>'
    width = 1000
    per_h = 260
    total_h = per_h * len(roots)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" viewBox="0 0 {width} {total_h}">']

    def traverse(node, x, y, level, span=200):
        if not node:
            return
        childs = []
        if getattr(node, 'children', None):
            childs = [c for c in node.children if c]
        else:
            if node.left: childs.append(node.left)
            if node.right: childs.append(node.right)

        n = len(childs)
        gap = span // max(1, n)
        start_x = x - (gap * (n - 1)) / 2

        for i, ch in enumerate(childs):
            cx = int(start_x + i * gap)
            cy = y + 100
            parts.append(f'<line x1="{x}" y1="{y}" x2="{cx}" y2="{cy}" stroke="#fff"/>')
            traverse(ch, cx, cy, level + 1, max(60, span // 2))

        parts.append(
            f'<circle cx="{x}" cy="{y}" r="25" fill="#f8c537" stroke="#fff" data-id="{getattr(node, "id", "")}" data-val="{escape_text(node.val)}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 5}" font-size="20" text-anchor="middle" fill="#000">{escape_text(node.val)}</text>')

    for i, root in enumerate(roots):
        y0 = 40 + i * per_h
        traverse(root, width // 2, y0, 1)

    parts.append('</svg>')
    return ''.join(parts)


# ----------------------
# BST helpers
# ----------------------
def bst_insert(node, val):
    if not node:
        return TreeNode(val)
    # prevent duplicate values: if equal, do nothing
    if val == node.val:
        return node
    if val < node.val:
        node.left = bst_insert(node.left, val)
    else:
        node.right = bst_insert(node.right, val)
    return node


# ----------------------
# MANUAL BINARY TREE
# ----------------------
bt_root = None


def render_binary_tree_svg(root):
    if not root:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 400" width="1000" height="400"></svg>'

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="500" viewBox="0 0 1000 500">']

    def walk(node, x, y, spread):
        if not node:
            return

        if node.left:
            lx = x - spread
            ly = y + 100
            w = edge_weights.get((getattr(node, 'id', ''), getattr(node.left, 'id', '')), 1)
            parts.append(f'<line x1="{x}" y1="{y}" x2="{lx}" y2="{ly}" stroke="white" stroke-width="{1 + (w - 1)}"/>')
            if w > 1:
                parts.append(
                    f'<text x="{(x + lx) // 2}" y="{(y + ly) // 2}" font-size="14" text-anchor="middle" fill="#fff">{w}</text>')
            walk(node.left, lx, ly, spread // 2)

        if node.right:
            rx = x + spread
            ry = y + 100
            w = edge_weights.get((getattr(node, 'id', ''), getattr(node.right, 'id', '')), 1)
            parts.append(f'<line x1="{x}" y1="{y}" x2="{rx}" y2="{ry}" stroke="white" stroke-width="{1 + (w - 1)}"/>')
            if w > 1:
                parts.append(
                    f'<text x="{(x + rx) // 2}" y="{(y + ry) // 2}" font-size="14" text-anchor="middle" fill="#fff">{w}</text>')
            walk(node.right, rx, ry, spread // 2)

        parts.append(
            f'<circle cx="{x}" cy="{y}" r="25" fill="#ff6b6b" stroke="white" data-id="{node.id}" data-val="{escape_text(node.val)}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-size="18" fill="black">{escape_text(node.val)}</text>')

    walk(root, 500, 50, 200)
    parts.append('</svg>')
    return "".join(parts)


def render_bt_forest_svg(roots):
    # render multiple binary trees stacked vertically
    if not roots:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 200" width="1000" height="200"></svg>'
    width = 1000
    per_h = 300
    total_h = per_h * len(roots)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" viewBox="0 0 {width} {total_h}">']

    def walk(node, x, y, spread):
        if not node:
            return
        if node.left:
            lx = x - spread
            ly = y + 100
            w = edge_weights.get((getattr(node, 'id', ''), getattr(node.left, 'id', '')), 1)
            parts.append(f'<line x1="{x}" y1="{y}" x2="{lx}" y2="{ly}" stroke="white" stroke-width="{1 + (w - 1)}"/>')
            if w > 1:
                parts.append(
                    f'<text x="{(x + lx) // 2}" y="{(y + ly) // 2}" font-size="14" text-anchor="middle" fill="#fff">{w}</text>')
            walk(node.left, lx, ly, spread // 2)
        if node.right:
            rx = x + spread
            ry = y + 100
            w = edge_weights.get((getattr(node, 'id', ''), getattr(node.right, 'id', '')), 1)
            parts.append(f'<line x1="{x}" y1="{y}" x2="{rx}" y2="{ry}" stroke="white" stroke-width="{1 + (w - 1)}"/>')
            if w > 1:
                parts.append(
                    f'<text x="{(x + rx) // 2}" y="{(y + ry) // 2}" font-size="14" text-anchor="middle" fill="#fff">{w}</text>')
            walk(node.right, rx, ry, spread // 2)
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="25" fill="#ff6b6b" stroke="white" data-id="{getattr(node, "id", "")}" data-val="{escape_text(node.val)}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-size="18" fill="black">{escape_text(node.val)}</text>')

    for i, root in enumerate(roots):
        y0 = 50 + i * per_h
        walk(root, width // 2, y0, 200)

    parts.append('</svg>')
    return ''.join(parts)


class BST:
    def __init__(self):
        self.root = None

    def insert(self, data):
        # data expected as string
        new = Node(data)
        if not self.root:
            self.root = new
            return

        cur = self.root
        while True:
            if data < cur.node:
                if cur.left:
                    cur = cur.left
                else:
                    cur.left = new
                    return
            else:
                if cur.right:
                    cur = cur.right
                else:
                    cur.right = new
                    return

    def dfs_search(self, word):
        if not word:
            return []
        results = []
        w = word.lower()

        def walk(node):
            if not node:
                return
            try:
                if w in node.node.lower():
                    results.append(node.node)
            except Exception:
                pass
            walk(node.left)
            walk(node.right)

        walk(self.root)
        return results

def bst_search(node, val):
    if not node:
        return False
    if node.val == val:
        return True
    elif val < node.val:
        return bst_search(node.left, val)
    else:
        return bst_search(node.right, val)


def bst_find_max(node):
    if not node:
        return None
    while node.right:
        node = node.right
    return node.val


def bst_height(node):
    if not node:
        return 0
    return 1 + max(bst_height(node.left), bst_height(node.right))


def bst_delete(node, val):
    if not node:
        return None

    if val < node.val:
        node.left = bst_delete(node.left, val)
    elif val > node.val:
        node.right = bst_delete(node.right, val)
    else:
        # Case 1: No child
        if not node.left and not node.right:
            return None

        # Case 2: One child
        if not node.left:
            return node.right
        if not node.right:
            return node.left

        # Case 3: Two children
        temp = bst_find_max(node.left)
        node.val = temp
        node.left = bst_delete(node.left, temp)

    return node


def bst_detach(node, val):
    """Detach the node with value `val` from the tree and return (new_tree_root, detached_node).
    If not found, (node, None) is returned."""
    if not node:
        return node, None

    if val < node.val:
        detached = node
        return node, detached
        if not node.left and not node.right:
            return None, detached

        if not node.left:
            return node.right, detached
        if not node.right:
            return node.left, detached

        # two children: replace with max from left
        temp_val = bst_find_max(node.left)
        node.val = temp_val
        node.left = bst_delete(node.left, temp_val)
        return node, detached

        # two children: replace with max from left
        temp_val = bst_find_max(node.left)
        node.val = temp_val
        node.left = bst_delete(node.left, temp_val)
        return node, detached

