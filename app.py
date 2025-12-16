# stdlib
import os
import sqlite3
import threading

# flask
from flask import (
    Flask, request, render_template,
    redirect, url_for, g, jsonify, session, Blueprint
)

# content
import markdown
import bleach

from StackQueue import *
from Graph import *
from TreeBTBST import *
from Sorting import *
from Auth import *
from db import get_db

app = Flask(__name__)
app.secret_key = "visual-sorting"
DATABASE = os.environ.get("DATABASE_PATH", "feed.db")

ALLOWED_TAGS = [
    "h1","h2","h3","p","strong","em",
    "ul","li","hr","code","pre","blockquote"
]

def md_to_safe_html(md_text: str) -> str:
    return bleach.clean(
        markdown.markdown(
            md_text or "",
            extensions=["fenced_code", "tables"]
        ),
        tags=[
            "h1","h2","h3",
            "p","strong","em",
            "ul","ol","li",
            "hr",
            "code","pre","blockquote"
        ],
        strip=True
    )


import random

ARRAY_SIZE = 20
MIN_VALUE = 5
MAX_VALUE = 95

def random_array():
    return [random.randint(MIN_VALUE, MAX_VALUE) for _ in range(ARRAY_SIZE)]

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    dir_name = os.path.dirname(DATABASE)
    if dir_name:  # only create folder if there is a directory
        os.makedirs(dir_name, exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    # PRAGMAS
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA foreign_keys=ON;")

    # -------------------------
    # BASE SCHEMA
    # -------------------------
    if os.path.exists("schema.sql"):
        with open("schema.sql") as f:
            cur.executescript(f.read())
    else:
        # Fallback minimal schema
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password TEXT,
            oauth_provider TEXT,
            oauth_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            caption TEXT NOT NULL,
            post_type TEXT NOT NULL DEFAULT 'text',
            up INTEGER NOT NULL DEFAULT 0,
            down INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER,
            comment TEXT NOT NULL,
            parent_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)

    # -------------------------
    # MIGRATIONS
    # -------------------------

    # comments.parent_id
    cur.execute("PRAGMA table_info(comments)")
    cols = [r[1] for r in cur.fetchall()]
    if "parent_id" not in cols:
        try:
            cur.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER")
        except Exception:
            pass

    # attachments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
    );
    """)

    # posts.user_id
    cur.execute("PRAGMA table_info(posts)")
    post_cols = [r[1] for r in cur.fetchall()]
    if "user_id" not in post_cols:
        try:
            cur.execute("ALTER TABLE posts ADD COLUMN user_id INTEGER")
        except Exception:
            pass

    # -------------------------
    # INDEXES
    # -------------------------
    cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_posts_title ON posts(title)")

    conn.commit()
    conn.close()

# -------------------------
# FEED / SEARCH LOGIC
# -------------------------
def get_feed_stack():
    db = get_db()

    rows = db.execute("""
        SELECT p.*, u.username
        FROM posts p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.id DESC
    """).fetchall()

    stack = Stack()

    for r in rows:
        caption_md = r["caption"] or ""

        post = {
            "id": r["id"],
            "user_id": r["user_id"],
            "title": r["title"],
            # keep markdown ONLY if you need editing later
            "caption": caption_md,
            # ALWAYS use this for display
            "caption_html": md_to_safe_html(caption_md),
            "author": r["username"] or "Anonymous",
            "post_type": r["post_type"],
            "up": r["up"] or 0,
            "down": r["down"] or 0,
        }

        # latest comment
        latest = db.execute(
            "SELECT comment, created_at FROM comments WHERE post_id=? ORDER BY id DESC LIMIT 1",
            (r["id"],)
        ).fetchone()

        post["latest_comment"] = latest["comment"] if latest else None
        post["latest_comment_time"] = latest["created_at"] if latest else None

        # attachments
        atts = db.execute(
            "SELECT id, filename, path FROM attachments WHERE post_id=? ORDER BY id ASC",
            (r["id"],)
        ).fetchall()

        post["attachments"] = [
            {
                "id": a["id"],
                "filename": a["filename"],
                "url": a["path"]
            } for a in atts
        ]

        stack.push(post)

    return stack.to_list()


def perform_bst_search(keyword):
    posts = get_feed_stack()
    bst = BST()
    for post in posts:
        title = post.get("title", "") or ""
        bst.insert(title)
    return bst.dfs_search(keyword)


# -------------------------
# ROUTES
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register_page():
    """User registration page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not username or not email or not password:
            return render_template("register.html", error="All fields are required.")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.")

        db = get_db()
        user = User.create_local(db, username, email, password)

        if not user:
            return render_template("register.html", error="Username or email already exists.")

        # Auto-login after registration
        AuthManager.login_user(user)
        return redirect(url_for("lectures"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    """User login page."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("login.html", error="Username and password required.")

        db = get_db()
        user = User.authenticate(db, username, password)

        if not user:
            return render_template("login.html", error="Invalid username or password.")

        AuthManager.login_user(user)
        return redirect(url_for("lectures"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    """Logout the current user."""
    AuthManager.logout_user()
    return redirect(url_for("login_page"))


@app.route("/oauth/github", methods=["GET"])
def oauth_github_login():
    """Initiate GitHub OAuth flow (simplified for demo)."""
    # In production, use a proper OAuth library (authlib, requests-oauthlib)
    # For now, create a demo OAuth user
    db = get_db()
    github_id = request.args.get("code", "github_demo")
    user = User.create_oauth(db, "github", github_id, f"github_{github_id[:8]}", f"{github_id}@github.local")
    AuthManager.login_user(user)
    return redirect(url_for("lectures"))


@app.route("/oauth/google", methods=["GET"])
def oauth_google_login():
    """Initiate Google OAuth flow (simplified for demo)."""
    # In production, use a proper OAuth library (authlib, requests-oauthlib)
    # For now, create a demo OAuth user
    db = get_db()
    google_id = request.args.get("code", "google_demo")
    user = User.create_oauth(db, "google", google_id, f"google_{google_id[:8]}", f"{google_id}@google.local")
    AuthManager.login_user(user)
    return redirect(url_for("lectures"))


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        keyword = request.form.get("search", "") or ""

        db = get_db()
        sql_results = db.execute("""
            SELECT id, title, caption 
            FROM posts
            WHERE title LIKE ? OR caption LIKE ?
            ORDER BY id DESC
        """, (f"%{keyword}%", f"%{keyword}%")).fetchall()

        results = []
        for r in sql_results:
            cid = r["id"]
            title = r["title"] or ""
            caption = r["caption"] or ""
            max_value = caption if caption.strip() else "None"

            # related_count: naive heuristic using first word of title
            related_count = 0
            if title.strip():
                first_word = title.strip().split()[0]
                q = db.execute(
                    "SELECT COUNT(*) as c FROM posts WHERE (title LIKE ? OR caption LIKE ?) AND id != ?",
                    (f"%{first_word}%", f"%{first_word}%", cid)
                ).fetchone()
                related_count = q["c"] if q is not None else 0

            results.append({
                "id": cid,
                "title": title,
                "caption": caption,
                "max_value": max_value,
                "related_count": related_count
            })
        # attach latest comment for each result (if present)
        for item in results:
            try:
                latest = db.execute("SELECT comment FROM comments WHERE post_id=? ORDER BY id DESC LIMIT 1",
                                    (item['id'],)).fetchone()
                item['latest_comment'] = latest['comment'] if latest else None
            except Exception:
                item['latest_comment'] = None

        return jsonify(results)
    # default homepage load
    posts = get_feed_stack()
    return render_template("index.html", posts=posts, current_user=get_current_user_context())


@app.route("/search_posts")
def search_posts():
    q = request.args.get("q", "").strip()
    db = get_db()

    rows = db.execute("""
        SELECT id, title, caption
        FROM posts
        WHERE title LIKE ? OR caption LIKE ?
        ORDER BY id DESC
    """, (f"%{q}%", f"%{q}%")).fetchall()

    results = []

    for r in rows:
        caption_md = r["caption"] or ""

        results.append({
            "id": r["id"],
            "title": r["title"] or "",
            "caption_html": md_to_safe_html(caption_md),  # 
            "related_count": 0
        })

    # attach latest comment
    for item in results:
        latest = db.execute(
            "SELECT comment FROM comments WHERE post_id=? ORDER BY id DESC LIMIT 1",
            (item["id"],)
        ).fetchone()
        item["latest_comment"] = latest["comment"] if latest else None

    return jsonify(results)



@app.route("/lectures", methods=["GET", "POST"])
def lectures():
    if request.method == "POST":
        db = get_db()
        db.execute("""
            INSERT INTO posts(title, caption, author, post_type, up, down)
            VALUES (?, ?, ?, ?, 0, 0)
        """, (
            request.form.get("title"),
            request.form.get("caption"),
            request.form.get("author", "Anonymous"),
            request.form.get("post_type", "regular")
        ))
        db.commit()
        return redirect(url_for("lectures"))

    db_posts = get_feed_stack()

    interactive_posts = [
        {
            "id": -1,
            "title": "Queue Interactive Demo",
            "caption": "Real-time enqueue/dequeue visualization.",
            "up": 0,
            "down": 0
        },
        {
            "id": -2,
            "title": "Stack Interactive Demo",
            "caption": "Push/pop to see LIFO behavior.",
            "up": 0,
            "down": 0
        },
        {
            "id": -3,
            "title": "Tree Interactive Demo",
            "caption": "Add nodes to grow a general tree.",
            "up": 0,
            "down": 0
        },
        {
            "id": -4,
            "title": "Binary Tree Interactive Demo",
            "caption": "Insert left/right nodes manually.",
            "up": 0,
            "down": 0
        },
        {
            "id": -5,
            "title": "Binary Search Tree Interactive Demo",
            "caption": "Automatic BST insertion.",
            "up": 0,
            "down": 0
        }
    ]

    final_posts = interactive_posts + db_posts
    # Enrich regular posts with two helper fields:
    # - max_value: show the post's caption (or 'None')
    # - related_count: number of other posts that share a keyword from this title
    db = get_db()
    for post in final_posts:
        try:
            if post.get("id", 0) > 0:
                # max_value: use caption or 'None'
                post["max_value"] = post.get("caption") or "None"

                # related_count: use the first word of the title to find related posts
                title = (post.get("title") or "").strip()
                if title:
                    first_word = title.split()[0]
                    q = db.execute(
                        "SELECT COUNT(*) as c FROM posts WHERE (title LIKE ? OR caption LIKE ?) AND id != ?",
                        (f"%{first_word}%", f"%{first_word}%", post["id"])
                    ).fetchone()
                    post["related_count"] = q["c"] if q is not None else 0
                else:
                    post["related_count"] = 0
            else:
                # interactive placeholders: show N/A
                post["max_value"] = "N/A"
                post["related_count"] = 0
        except Exception:
            post["max_value"] = post.get("caption") or "None"
            post["related_count"] = 0

    return render_template("lectures.html", posts=final_posts, current_user=get_current_user_context())


def get_caption_from_db(id):
    # Connect to your database
    import sqlite3
    conn = sqlite3.connect('feed.db')  # replace with your DB file
    cursor = conn.cursor()

    # Fetch caption
    cursor.execute("SELECT caption FROM captions WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


@app.route("/lecture/<int:id>")
def lecture(id):
    caption_md = get_caption_from_db(id)

    caption_html = bleach.clean(
        markdown.markdown(
            caption_md,
            extensions=["fenced_code", "tables"]
        ),
        tags=[
            "h1","h2","h3",
            "p","strong","em",
            "ul","ol","li",
            "hr",
            "code","pre","blockquote"
        ],
        strip=True
    )

    return render_template(
        "lecture.html",
        caption_html=caption_html
    )


@app.route("/create_post", methods=["POST"])
def create_post():
    if not AuthManager.is_authenticated():
        return jsonify({"ok": False, "error": "login_required"}), 401

    db = get_db()
    user = AuthManager.get_current_user(db)
    if not user:
        return jsonify({"ok": False, "error": "user_not_found"}), 401

    title = request.form.get("title")
    caption = request.form.get("caption")
    post_type = request.form.get("post_type", "regular")

    cur = db.cursor()
    cur.execute("""
        INSERT INTO posts(user_id, title, caption, post_type, up, down)
        VALUES (?, ?, ?, ?, 0, 0)
    """, (user.id, title, caption, post_type))
    db.commit()
    post_id = cur.lastrowid

    # handle uploaded attachments (form field 'attachments', multiple allowed)
    try:
        files = request.files.getlist('attachments') if request.files else []
    except Exception:
        files = []

    if files:
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        for f in files:
            if not f or f.filename == '':
                continue
            safe_name = f"{uuid.uuid4().hex}_{escape_text(f.filename)}"
            dest = os.path.join(upload_dir, safe_name)
            try:
                f.save(dest)
                db.execute("INSERT INTO attachments (post_id, filename, path) VALUES (?, ?, ?)",
                           (post_id, f.filename, dest))
            except Exception:
                pass
        db.commit()

    return redirect(url_for("lectures"))


@app.route('/comments/add', methods=['POST'])
def comments_add():
    db = get_db()
    # support both form and JSON
    post_id = request.form.get('post_id') or request.json.get('post_id')
    comment = request.form.get('comment') or request.json.get('comment')
    parent_id = request.form.get('parent_id') or request.json.get('parent_id')
    author = request.form.get('author') or request.json.get('author') or 'Anonymous'

    try:
        post_id_int = int(post_id)
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid post id'})

    if not comment:
        return jsonify({'ok': False, 'error': 'empty comment'})

    # Keep whitespace as-is (do not strip)
    db.execute("INSERT INTO comments (post_id, user_id, comment, parent_id) VALUES (?, NULL, ?, ?)",
               (post_id_int, comment, parent_id))
    db.commit()

    # return latest comment for convenience
    row = db.execute("SELECT id, comment, created_at FROM comments WHERE post_id=? ORDER BY id DESC LIMIT 1",
                     (post_id_int,)).fetchone()
    return jsonify({'ok': True, 'comment': dict(row) if row else None})


@app.route('/posts/<int:post_id>/comments')
def comments_for_post(post_id):
    db = get_db()
    rows = db.execute(
        "SELECT id, post_id, user_id, comment, parent_id, created_at FROM comments WHERE post_id=? ORDER BY id ASC",
        (post_id,)).fetchall()
    results = [dict(r) for r in rows]
    return jsonify(results)


@app.route("/vote/<int:id>/<string:way>", methods=["POST"])
def vote(id, way):
    db = get_db()
    if way == "up":
        db.execute("UPDATE posts SET up = up + 1 WHERE id=?", (id,))
    else:
        db.execute("UPDATE posts SET down = down + 1 WHERE id=?", (id,))
    db.commit()
    row = db.execute("SELECT up, down FROM posts WHERE id=?", (id,)).fetchone()
    if row:
        return jsonify({"ok": True, "up": row[0], "down": row[1]})
    return jsonify({"ok": False}), 404


# schedule a cancellable delete from the UI (5 second delay)
def perform_delete(post_id):
    """Perform deletion using a fresh DB connection (safe from background threads)."""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass
    finally:
        try:
            pending_deletes.pop(post_id, None)
        except Exception:
            pass


@app.route("/delete/<int:id>", methods=["POST"])
def schedule_delete(id):
    global pending_deletes

    if not AuthManager.is_authenticated():
        return jsonify({"ok": False, "error": "login_required"}), 401

    db = get_db()
    current_user = AuthManager.get_current_user(db)

    # Check post ownership
    post = db.execute("SELECT user_id FROM posts WHERE id=?", (id,)).fetchone()
    if not post or post[0] != current_user.id:
        return jsonify({"ok": False, "error": "unauthorized"}), 403

    if id in pending_deletes:
        return jsonify({"ok": True, "pending": True})

    t = threading.Timer(5.0, perform_delete, args=(id,))
    pending_deletes[id] = t
    t.start()
    return jsonify({"ok": True, "scheduled": True})


@app.route('/delete/cancel/<int:id>', methods=['POST'])
def cancel_delete(id):
    global pending_deletes
    t = pending_deletes.pop(id, None)
    if t:
        try:
            t.cancel()
        except Exception:
            pass
        return jsonify({"ok": True, "cancelled": True})
    return jsonify({"ok": False, "error": "not_pending"}), 404


# Edit should accept the same form fields used by your modal (title, caption)
@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):
    if not AuthManager.is_authenticated():
        return jsonify({"ok": False, "error": "login_required"}), 401

    db = get_db()
    current_user = AuthManager.get_current_user(db)

    # Check post ownership
    post = db.execute("SELECT user_id FROM posts WHERE id=?", (id,)).fetchone()
    if not post or post[0] != current_user.id:
        return jsonify({"ok": False, "error": "unauthorized"}), 403

    # Your modal sets the form to post title, caption (no author field)
    title = request.form.get("title")
    caption = request.form.get("caption")

    # Only update fields that were provided
    if title is not None:
        db.execute("UPDATE posts SET title=? WHERE id=?", (title, id))
    if caption is not None:
        db.execute("UPDATE posts SET caption=? WHERE id=?", (caption, id))
    db.commit()
    return redirect(url_for("lectures"))


@app.route("/collaborators")
def collaborators_page():
    return render_template("collaborators.html")

# Queue endpoints
@app.route("/queue/enqueue", methods=["POST"])
def queue_enqueue():
    val = request.json.get("value", "").strip()
    if not val:
        return jsonify({"ok": False})
    queue.append(val)
    return jsonify({"ok": True, "svg": render_queue_svg()})


@app.route("/queue/dequeue", methods=["POST"])
def queue_dequeue():
    if queue:
        queue.pop(0)
    return jsonify({"ok": True, "svg": render_queue_svg()})


# Stack endpoints
@app.route("/stack/push", methods=["POST"])
def stack_push():
    val = request.json.get("value", "").strip()
    if not val:
        return jsonify({"ok": False})
    stack.append(val)
    return jsonify({"ok": True, "svg": render_stack_svg()})


@app.route("/stack/pop", methods=["POST"])
def stack_pop():
    if stack:
        stack.pop()
    return jsonify({"ok": True, "svg": render_stack_svg()})


# Generic tree endpoints
@app.route("/tree/insert", methods=["POST"])
def tree_insert_route():
    global tree_root, tree_roots
    val = request.json.get("value", "").strip()
    parent = request.json.get("parent")
    if not val:
        return jsonify({"ok": False})

    new_node = TreeNode(val)
    # If there are no roots yet, create a new root
    if not tree_roots:
        tree_roots.append(new_node)
        tree_root = tree_roots[0]
        return jsonify({"ok": True, "svg": render_tree_forest_svg(tree_roots)})

    def find_bfs_all(roots, v):
        for r in roots:
            q = [r]
            while q:
                n = q.pop(0)
                if n and (getattr(n, 'id', None) == v or str(n.val) == str(v)):
                    return n
                if n:
                    if n.left: q.append(n.left)
                    if n.right: q.append(n.right)
        return None

    if parent:
        pnode = find_bfs_all(tree_roots, parent)
        if pnode:
            if not pnode.left:
                pnode.left = new_node
            elif not pnode.right:
                pnode.right = new_node
            else:
                q = [pnode.left, pnode.right]
                placed = False
                while q and not placed:
                    n = q.pop(0)
                    if not n.left:
                        n.left = new_node;
                        placed = True;
                        break
                    if not n.right:
                        n.right = new_node;
                        placed = True;
                        break
                    q.extend([n.left, n.right])
        else:
            # parent not found -> create a new root
            tree_roots.append(new_node)
    else:
        # no parent -> create a new root (support multiple trees)
        tree_roots.append(new_node)

    return jsonify({"ok": True, "svg": render_tree_forest_svg(tree_roots)})


# BST endpoints
@app.route("/bst/insert", methods=["POST"])
def bst_insert_route():
    global bst_root
    val = request.json.get("value", "").strip()
    if not val:
        return jsonify({"ok": False})
    try:
        num = int(val)
    except:
        return jsonify({"ok": False, "error": "numeric only"})
    bst_root = bst_insert(bst_root, num)
    return jsonify({"ok": True, "svg": render_generic_tree_svg(bst_root)})


@app.route("/bst/search", methods=["POST"])
def bst_search_route():
    global bst_root
    val = request.json.get("value")
    try:
        num = int(val)
    except:
        return jsonify({"ok": False})

    found = bst_search(bst_root, num)
    return jsonify({"ok": True, "found": found})


@app.route("/bst/max", methods=["GET"])
def bst_max_route():
    global bst_root
    m = bst_find_max(bst_root)
    return jsonify({"ok": True, "max": m})


@app.route("/bst/height", methods=["GET"])
def bst_height_route():
    global bst_root
    h = bst_height(bst_root)
    return jsonify({"ok": True, "height": h})


@app.route("/bst/delete", methods=["POST"])
def bst_delete_route():
    global bst_root
    val = request.json.get("value")
    try:
        num = int(val)
    except:
        return jsonify({"ok": False})

    bst_root, detached = bst_detach(bst_root, num)
    response = {"ok": True, "svg": render_generic_tree_svg(bst_root)}
    if detached:
        # store detached subtree server-side so it can be reattached by token
        token = uuid.uuid4().hex
        pending_subtrees[token] = ('bst', detached)
        response["detached_svg"] = render_generic_tree_svg(detached)
        response["detached_root"] = detached.val
        response["token"] = token
    return jsonify(response)


@app.route('/tree/delete', methods=['POST'])
def tree_delete_route():
    global tree_roots
    node_id = request.json.get('id')
    if not node_id:
        return jsonify({'ok': False})

    def detach_by_id(root, target_id):
        if not root:
            return root, None
        if getattr(root, 'id', None) == target_id:
            return None, root
        if root.left:
            new_left, detached = detach_by_id(root.left, target_id)
            root.left = new_left
            if detached:
                return root, detached
        if root.right:
            new_right, detached = detach_by_id(root.right, target_id)
            root.right = new_right
            if detached:
                return root, detached
        return root, None

    detached = None
    new_roots = []
    for r in tree_roots:
        nr, d = detach_by_id(r, node_id)
        if d and getattr(r, 'id', None) == node_id:
            # root itself was detached; promote nothing (children handled by client)
            detached = d
            # skip adding this root
            continue
        if d:
            detached = d
        new_roots.append(nr)

    tree_roots[:] = [r for r in new_roots if r]
    # promote detached children to be new roots (each becomes its own tree)
    if detached:
        # for n-ary children use .children; fallback to left/right
        kids = []
        if getattr(detached, 'children', None):
            kids = [c for c in detached.children if c]
        else:
            if detached.left: kids.append(detached.left)
            if detached.right: kids.append(detached.right)

        for k in kids:
            tree_roots.append(k)

    resp = {'ok': True, 'svg': render_tree_forest_svg(tree_roots)}
    if detached:
        token = uuid.uuid4().hex
        pending_subtrees[token] = ('tree', detached)
        resp['detached_svg'] = render_tree_forest_svg([detached])
        resp['detached_root_id'] = getattr(detached, 'id', None)
        resp['token'] = token
    return jsonify(resp)


@app.route('/tree/reset', methods=['POST'])
def tree_reset():
    global tree_roots
    tree_roots.clear()
    return jsonify({"ok": True, "svg": render_tree_forest_svg(tree_roots)})


@app.route('/bt/delete', methods=['POST'])
def bt_delete_route():
    global bt_roots
    node_id = request.json.get('id')
    if not node_id:
        return jsonify({'ok': False})

    def detach_by_id(root, target_id):
        if not root:
            return root, None
        if getattr(root, 'id', None) == target_id:
            return None, root
        if root.left:
            new_left, detached = detach_by_id(root.left, target_id)
            root.left = new_left
            if detached:
                return root, detached
        if root.right:
            new_right, detached = detach_by_id(root.right, target_id)
            root.right = new_right
            if detached:
                return root, detached
        return root, None

    detached = None
    new_roots = []
    for r in bt_roots:
        nr, d = detach_by_id(r, node_id)
        if d and getattr(r, 'id', None) == node_id:
            detached = d
            continue
        if d:
            detached = d
        new_roots.append(nr)

    bt_roots[:] = [r for r in new_roots if r]
    # promote detached children to be roots
    if detached:
        kids = []
        if getattr(detached, 'children', None):
            kids = [c for c in detached.children if c]
        else:
            if detached.left: kids.append(detached.left)
            if detached.right: kids.append(detached.right)
        for k in kids:
            bt_roots.append(k)

    resp = {'ok': True, 'svg': render_bt_forest_svg(bt_roots)}
    if detached:
        token = uuid.uuid4().hex
        pending_subtrees[token] = ('bt', detached)
        resp['detached_svg'] = render_bt_forest_svg([detached])
        resp['detached_root_id'] = getattr(detached, 'id', None)
        resp['token'] = token
    return jsonify(resp)


@app.route('/reattach/<token>', methods=['POST'])
def reattach_subtree(token):
    global tree_root, bt_root, bst_root
    payload = request.get_json() or {}
    parent = payload.get('parent')

    item = pending_subtrees.pop(token, None)
    if not item:
        return jsonify({'ok': False, 'error': 'token_not_found'}), 404

    typ, node = item

    # helper to find node by id
    def find_by_id(root, tid):
        q = [root]
        while q:
            n = q.pop(0)
            if not n:
                continue
            if getattr(n, 'id', None) == tid:
                return n
            if getattr(n, 'left', None): q.append(n.left)
            if getattr(n, 'right', None): q.append(n.right)
        return None

    if typ == 'bst':
        # reinsert all values from detached subtree into bst_root
        def collect_vals(n, out):
            if not n: return
            out.append(n.val)
            collect_vals(n.left, out)
            collect_vals(n.right, out)

        vals = []
        collect_vals(node, vals)
        for v in vals:
            bst_root = bst_insert(bst_root, v)
        return jsonify({'ok': True, 'svg': render_generic_tree_svg(bst_root)})

    if typ == 'tree':
        # find parent across all tree roots
        def find_in_roots(roots, tid):
            for r in roots:
                q = [r]
                while q:
                    n = q.pop(0)
                    if not n:
                        continue
                    if getattr(n, 'id', None) == tid or str(n.val) == str(tid):
                        return n
                    # traverse both n.children (n-ary) and legacy left/right
                    if getattr(n, 'children', None):
                        q.extend([c for c in n.children if c])
                    else:
                        if n.left: q.append(n.left)
                        if n.right: q.append(n.right)
            return None

        if parent:
            p = find_in_roots(tree_roots, parent)
            if not p:
                return jsonify({'ok': False, 'error': 'parent_not_found'}), 404
            # attach under n-ary children if supported
            if getattr(p, 'children', None) is not None:
                p.children.append(node)
            else:
                if not p.left:
                    p.left = node
                elif not p.right:
                    p.right = node
                else:
                    q = [p.left, p.right]
                    placed = False
                    while q and not placed:
                        n = q.pop(0)
                        if not n.left:
                            n.left = node;
                            placed = True;
                            break
                        if not n.right:
                            n.right = node;
                            placed = True;
                            break
                        q.extend([n.left, n.right])
            # ensure edge_weights entries exist for any edges in the reattached subtree
            try:
                def collect_edges(n):
                    res = []
                    if not n: return res
                    if getattr(n, 'children', None):
                        for c in n.children:
                            res.append((getattr(n, 'id', ''), getattr(c, 'id', '')))
                            res.extend(collect_edges(c))
                    else:
                        if n.left:
                            res.append((getattr(n, 'id', ''), getattr(n.left, 'id', '')))
                            res.extend(collect_edges(n.left))
                        if n.right:
                            res.append((getattr(n, 'id', ''), getattr(n.right, 'id', '')))
                            res.extend(collect_edges(n.right))
                    return res

                for u, v in collect_edges(node):
                    if (u, v) not in edge_weights:
                        edge_weights[(u, v)] = 1
            except Exception:
                pass
            return jsonify({'ok': True, 'svg': render_tree_forest_svg(tree_roots)})
        else:
            # no parent -> create a new root (support multiple trees)
            tree_roots.append(node)
            return jsonify({'ok': True, 'svg': render_tree_forest_svg(tree_roots)})

    if typ == 'bt':
        def find_in_roots(roots, tid):
            for r in roots:
                q = [r]
                while q:
                    n = q.pop(0)
                    if not n:
                        continue
                    if getattr(n, 'id', None) == tid or str(n.val) == str(tid):
                        return n
                    if getattr(n, 'children', None):
                        q.extend([c for c in n.children if c])
                    else:
                        if n.left: q.append(n.left)
                        if n.right: q.append(n.right)
            return None

        if parent:
            p = find_in_roots(bt_roots, parent)
            if not p:
                return jsonify({'ok': False, 'error': 'parent_not_found'}), 404
            # attach respecting n-ary children if present
            if getattr(p, 'children', None) is not None:
                p.children.append(node)
            else:
                if not p.left:
                    p.left = node
                elif not p.right:
                    p.right = node
                else:
                    q = [p.left, p.right]
                    placed = False
                    while q and not placed:
                        n = q.pop(0)
                        if not n.left:
                            n.left = node;
                            placed = True;
                            break
                        if not n.right:
                            n.right = node;
                            placed = True;
                            break
                        q.extend([n.left, n.right])
            # if the detached subtree contains children, transfer any edge_weights entries into graph edge_weights keyed by ids
            try:
                def collect_edges(n):
                    res = []
                    if not n: return res
                    if getattr(n, 'children', None):
                        for c in n.children:
                            res.append((getattr(n, 'id', ''), getattr(c, 'id', '')))
                            res.extend(collect_edges(c))
                    else:
                        if n.left:
                            res.append((getattr(n, 'id', ''), getattr(n.left, 'id', '')))
                            res.extend(collect_edges(n.left))
                        if n.right:
                            res.append((getattr(n, 'id', ''), getattr(n.right, 'id', '')))
                            res.extend(collect_edges(n.right))
                    return res

                for u, v in collect_edges(node):
                    if (u, v) not in edge_weights:
                        edge_weights[(u, v)] = 1
            except Exception:
                pass
            return jsonify({'ok': True, 'svg': render_bt_forest_svg(bt_roots)})
        else:
            # no parent -> add as new root
            bt_roots.append(node)
            return jsonify({'ok': True, 'svg': render_bt_forest_svg(bt_roots)})

    return jsonify({'ok': False, 'error': 'unknown_type'}), 400

@app.route('/graph/svg')
def graph_svg():
    return jsonify({"ok": True, "svg": render_graph_svg()})

def render_graph_svg():
    # simple circular layout
    if not graph_vertices:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="800" height="400"></svg>'
    width = 800
    height = 400
    cx = width // 2
    cy = height // 2
    r = min(cx, cy) - 80
    n = len(graph_vertices)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    coords = {}
    for i, v in enumerate(graph_vertices):
        angle = 2 * 3.14159 * i / max(1, n)
        x = int(cx + r * (0.9 * __import__('math').cos(angle)))
        y = int(cy + r * (0.9 * __import__('math').sin(angle)))
        coords[v['id']] = (x, y)

    # draw edges
    for (u, v), w in graph_edges.items():
        if u not in coords or v not in coords: continue
        x1, y1 = coords[u]
        x2, y2 = coords[v]
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#fff" stroke-width="{1 + (w - 1)}"/>')
        if w > 1:
            parts.append(
                f'<text x="{(x1 + x2) // 2}" y="{(y1 + y2) // 2}" font-size="14" text-anchor="middle" fill="#fff">{w}</text>')

    # draw vertices
    for v in graph_vertices:
        x, y = coords[v['id']]
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="20" fill="#7bd389" stroke="#fff" data-id="{v["id"]}" data-val="{escape_text(v.get("label", ""))}"/>')
        parts.append(
            f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-size="14" fill="#000">{escape_text(v.get("label", ""))}</text>')

    parts.append('</svg>')
    return ''.join(parts)


@app.route('/graph/add-vertex', methods=['POST'])
def graph_add_vertex():
    label = (request.json.get('label') or '').strip()
    if not label:
        return jsonify({'ok': False})
    vid = uuid.uuid4().hex
    graph_vertices.append({'id': vid, 'label': label})
    return jsonify({'ok': True, 'svg': render_graph_svg(), 'id': vid})


@app.route('/graph/delete-vertex', methods=['POST'])
def graph_delete_vertex():
    vid = request.json.get('id')
    if not vid: return jsonify({'ok': False})
    global graph_vertices, graph_edges
    graph_vertices[:] = [v for v in graph_vertices if v['id'] != vid]
    # remove edges touching vid
    keys = [k for k in graph_edges.keys()]
    for k in keys:
        if vid in k:
            graph_edges.pop(k, None)
    return jsonify({'ok': True, 'svg': render_graph_svg()})


@app.route('/graph/add-edge', methods=['POST'])
def graph_add_edge():
    u = request.json.get('u')
    v = request.json.get('v')
    directed = request.json.get('directed', False)
    if not u or not v: return jsonify({'ok': False})
    # collapse parallel edges by increasing weight
    graph_edges[(u, v)] = graph_edges.get((u, v), 0) + 1
    if not directed:
        graph_edges[(v, u)] = graph_edges.get((v, u), 0) + 1
    return jsonify({'ok': True, 'svg': render_graph_svg()})


@app.route('/graph/set-weight', methods=['POST'])
def graph_set_weight():
    u = request.json.get('u')
    v = request.json.get('v')
    w = int(request.json.get('weight') or 1)
    if not u or not v: return jsonify({'ok': False})
    graph_edges[(u, v)] = w
    return jsonify({'ok': True, 'svg': render_graph_svg()})


@app.route('/graph/reset', methods=['POST'])
def graph_reset():
    graph_vertices.clear()
    graph_edges.clear()
    return jsonify({'ok': True, 'svg': render_graph_svg()})

@app.route("/atlas")
def atlas():
    return render_template("atlas.html")

@app.route("/atlas/svg")
def atlas_svg():
    # Get the base SVG content (without any highlighted path)
    try:
        return atlas_graph.render_svg()
    except Exception as e:
        print(f"Error rendering SVG: {str(e)}")
        return "<svg width='1200' height='600' xmlns='http://www.w3.org/2000/svg'><text x='20' y='30' fill='red'>Error loading map. Please check server logs.</text></svg>"

@app.route("/atlas/route", methods=["POST"])
def atlas_route():

    data = request.json
    src, dst = data["src"], data["dst"]
    path, total_min, total_m = atlas_graph.shortest_path(src, dst)
    return jsonify({
        "path": path,
        "minutes": total_min,
        "meters": total_m,
        "svg": atlas_graph.render_svg(path)
    })

@app.route('/eleccirc')
def eleccirc():
    """Electrical circuit designer page."""
    return render_template('eleccirc.html')

@app.route("/bt/add-left", methods=["POST"])
def bt_add_left():
    global bt_root, bt_roots
    data = request.get_json(silent=True) or {}
    val = (data.get("value") or request.form.get("value") or "").strip()
    parent = data.get("parent") or request.form.get("parent")
    if not val:
        return jsonify({"ok": False})

    if not bt_roots:
        node = TreeNode(val)
        bt_roots.append(node)
        bt_root = bt_roots[0]
        return jsonify({"ok": True, "svg": render_bt_forest_svg(bt_roots)})

    def find_bfs_all(roots, v):
        for r in roots:
            q = [r]
            while q:
                n = q.pop(0)
                if not n:
                    continue
                try:
                    if getattr(n, 'id', None) == v or str(n.val) == str(v):
                        return n
                except Exception:
                    pass
                if n.left: q.append(n.left)
                if n.right: q.append(n.right)
        return None

    if parent:
        p = find_bfs_all(bt_roots, parent)
        if p:
            if not p.right:
                p.right = TreeNode(val)
            else:
                q = [p.right]
                placed = False
                while q and not placed:
                    n = q.pop(0)
                    if not n.left:
                        n.left = TreeNode(val);
                        placed = True;
                        break
                    if not n.right:
                        n.right = TreeNode(val);
                        placed = True;
                        break
                    q.extend([n.left, n.right])
        else:
            bt_roots.append(TreeNode(val))
    else:
        first = bt_roots[0]
        if not first.left:
            first.left = TreeNode(val)
        else:
            bt_roots.append(TreeNode(val))

    return jsonify({"ok": True, "svg": render_bt_forest_svg(bt_roots)})


@app.route("/bt/add-right", methods=["POST"])
def bt_add_right():
    global bt_root, bt_roots
    data = request.get_json(silent=True) or {}
    val = (data.get("value") or request.form.get("value") or "").strip()
    parent = data.get("parent") or request.form.get("parent")
    if not val:
        return jsonify({"ok": False})
    if not bt_roots:
        # create first root
        node = TreeNode(val)
        bt_roots.append(node)
        bt_root = bt_roots[0]
        return jsonify({"ok": True, "svg": render_bt_forest_svg(bt_roots)})

    # helper: search across all roots by id or value
    def find_bfs_all(roots, v):
        for r in roots:
            q = [r]
            while q:
                n = q.pop(0)
                if not n:
                    continue
                try:
                    if getattr(n, 'id', None) == v or str(n.val) == str(v):
                        return n
                except Exception:
                    pass
                if n.left: q.append(n.left)
                if n.right: q.append(n.right)
        return None

    if parent:
        p = find_bfs_all(bt_roots, parent)
        if p:
            if not p.left:
                p.left = TreeNode(val)
            else:
                q = [p.left]
                placed = False
                while q and not placed:
                    n = q.pop(0)
                    if not n.left:
                        n.left = TreeNode(val);
                        placed = True;
                        break
                    if not n.right:
                        n.right = TreeNode(val);
                        placed = True;
                        break
                    q.extend([n.left, n.right])
        else:
            # parent not found -> create new root
            bt_roots.append(TreeNode(val))
    else:
        # no parent -> attempt to insert under first root's right if empty, else create new root
        first = bt_roots[0]
        if not first.right:
            first.right = TreeNode(val)
        else:
            bt_roots.append(TreeNode(val))
    return jsonify({"ok": True, "svg": render_bt_forest_svg(bt_roots)})


@app.route("/bt/reset", methods=["POST"])
def bt_reset():
    global bt_root
    global bt_roots
    bt_roots.clear()
    return jsonify({"ok": True, "svg": render_bt_forest_svg(bt_roots)})


@app.route("/bt/add-root", methods=["POST"])
def bt_add_root():
    global bt_roots
    data = request.get_json(silent=True) or {}
    val = (data.get("value") or request.form.get("value") or "").strip()
    if not val:
        return jsonify({"ok": False})
    node = TreeNode(val)
    bt_roots.append(node)
    return jsonify({"ok": True, "svg": render_bt_forest_svg(bt_roots)})

sorting_bp = Blueprint("sorting", __name__)


def get_state(name, default):
    if name not in session:
        session[name] = default
    return session[name]


# =====================
# BUBBLE SORT
# =====================
@sorting_bp.route("/bubble/reset", methods=["POST"])
def bubble_reset():
    session["bubble"] = {
        "arr": random_array(),
        "i": 0,
        "j": 0,
        "done": False
    }
    return jsonify(array=session["bubble"]["arr"], highlight=[])


@sorting_bp.route("/bubble/step", methods=["POST"])
def bubble_step_route():
    s = get_state("bubble", {
        "arr": random_array(),
        "i": 0,
        "j": 0,
        "done": False
    })

    s, highlight, done = bubble_step(s)
    session["bubble"] = s
    return jsonify(array=s["arr"], highlight=highlight, done=done)


# =====================
# MERGE SORT
# =====================
@sorting_bp.route("/merge/reset", methods=["POST"])
def merge_reset():
    arr = random_array()
    session["merge"] = {
        "steps": [(arr.copy(), [])] + merge_sort_steps(arr),
        "idx": 0
    }
    return jsonify(array=arr, highlight=[])

@sorting_bp.route("/merge/step", methods=["POST"])
def merge_step():
    s = get_state("merge", {"steps": [], "idx": 0})

    if s["idx"] >= len(s["steps"]):
        return jsonify(done=True)

    arr, highlight = s["steps"][s["idx"]]
    s["idx"] += 1
    session["merge"] = s

    return jsonify(array=arr, highlight=highlight, done=False)


# =====================
# QUICK SORT
# =====================
@sorting_bp.route("/quick/reset", methods=["POST"])
def quick_reset():
    arr = random_array()
    session["quick"] = {
        "steps": [(arr.copy(), [])] + quick_sort_steps(arr),
        "idx": 0
    }
    return jsonify(array=arr, highlight=[])

@sorting_bp.route("/quick/step", methods=["POST"])
def quick_step():
    s = get_state("quick", {"steps": [], "idx": 0})

    if s["idx"] >= len(s["steps"]):
        return jsonify(done=True)

    arr, highlight = s["steps"][s["idx"]]
    s["idx"] += 1
    session["quick"] = s
    return jsonify(array=arr, highlight=highlight, done=False)

@sorting_bp.route("/insertion/reset", methods=["POST"])
def insertion_reset():
    arr = random_array()
    session["insertion"] = {
        "steps": insertion_sort_steps(arr),
        "idx": 0
    }
    return jsonify(array=arr, highlight=[])


@sorting_bp.route("/insertion/step", methods=["POST"])
def insertion_step():
    s = get_state("insertion", {"steps": [], "idx": 0})

    if s["idx"] >= len(s["steps"]):
        return jsonify(done=True)

    arr, highlight = s["steps"][s["idx"]]
    s["idx"] += 1
    session["insertion"] = s
    return jsonify(array=arr, highlight=highlight, done=False)

@sorting_bp.route("/selection/reset", methods=["POST"])
def selection_reset():
    arr = random_array()
    session["selection"] = {
        "steps": selection_sort_steps(arr),
        "idx": 0
    }
    return jsonify(array=arr, highlight=[])


@sorting_bp.route("/selection/step", methods=["POST"])
def selection_step():
    s = get_state("selection", {"steps": [], "idx": 0})

    if s["idx"] >= len(s["steps"]):
        return jsonify(done=True)

    arr, highlight = s["steps"][s["idx"]]
    s["idx"] += 1
    session["selection"] = s
    return jsonify(array=arr, highlight=highlight, done=False)

app.register_blueprint(sorting_bp, url_prefix="/sorting")

# RUN
if __name__ == "__main__":
    init_db()
    app.run(debug=True)