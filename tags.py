from pprint import pprint
def generate_tag_page(db, tag):
    rows = db.execute(
        "SELECT dz_nodes.name from dz_tags " +
        "INNER JOIN dz_nodes on dz_nodes.id = dz_tags.node " +
        f"WHERE dz_tags.tag is '{tag}';"
               )
    html = []
    html += ["<html>"]
    html += ["<head>"]
    html += ["</head>"]
    html += ["<body>"]
    html += [f"<h1>Nodes with tag {tag}</h1>"]
    for row in rows:
        node = row[0]
        html += [f"<p><a href=\"\">{node}</a></p>"]

    html += ["</body>"]
    html += ["</html>"]

    return "\n".join(html)

def generate_tag_index(db):
    rows = db.execute("SELECT distinct(tag), count(*) FROM dz_tags GROUP by tag ORDER BY tag");
    
    html = []
    html += ["<html>"]
    html += ["<head>"]
    html += ["</head>"]
    html += ["<body>"]
    html += [f"<h1>Tags</h1>"]
    for row in rows:
        tag, count = row
        html += [f"<p><a href=\"\">{tag} ({count})</a></p>"]

    html += ["</body>"]
    html += ["</html>"]

    return "\n".join(html)

if __name__ == "__main__":
    import sqlite3
    db = sqlite3.connect("../recurse/a.db")
    cur = db.cursor()

    # print(generate_tag_page(db, "sqlite"))
    print(generate_tag_index(db))

    db.close()