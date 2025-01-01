#!/usr/bin/env python3
import sqlite3
from pprint import pprint
import json
import re
import sys

def shortname(namespace, name):
    return re.sub("^" + namespace + "/", "", name)

def create_connections(db, nodes):
    connections = {}
    def insert_connections(rows):
        for left, right in rows:
            assert(left is not None)
            if left not in connections:
                connections[left] = {}
            assert(right is not None)
            connections[left][right] = True
    for nid in nodes.keys():
        rows = db.execute(" ".join([
            f"SELECT left, right FROM dz_connections",
            f"WHERE left == {nid}",
        ]))
        insert_connections(rows)
        rows = db.execute(" ".join([
            f"SELECT left, right FROM dz_connections",
            f"WHERE right == {nid}",
        ]))
        insert_connections(rows)
    return connections

def lookup_name_from_id(db, nid):
    rows = db.execute(f"SELECT name FROM dz_nodes WHERE id == {nid}")
    name = None
    for row in rows:
        name = row[0]
    return name

def get_connection_remarks(db, left, right):
    rows = db.execute("SELECT remarks FROM " +
        "dz_connection_remarks " +
        f"WHERE left == {left} AND " +
        f"right == {right} LiMIT 1")
    cr = None
    for row in rows:
        cr = json.loads(row[0])
    return cr


def generate_node_data(nodes, connections, path, db, nid):
    def get_reference():
        rows = db.execute(
            "SELECT filename, linum FROM dz_noderefs " +
            f"WHERE node = {nid} LIMIT 1;"
        )

        ref = None

        for row in rows:
            ref = {}
            ref['filename'] = row[0]
            ref['linum'] = row[1]

        return ref

    def get_lines():
        rows = db.execute(
            "SELECT lines FROM dz_lines " +
            f"WHERE node = {nid} LIMIT 1;"
        )

        lines = None
        for row in rows:
            lines = row[0]

        lines = json.loads(lines) if lines else None

        return lines

    def get_hyperlink():
        rows = db.execute(
            "SELECT hyperlink FROM dz_hyperlinks " +
            f"WHERE node = {nid} LIMIT 1;"
        )

        hyperlink = None
        for row in rows:
            hyperlink = row[0]

        return hyperlink

    def get_tags():
        rows = db.execute(
            "SELECT tag FROM dz_tags " +
            f"WHERE node = {nid};"
        )

        tags = None
        for row in rows:
            if tags is None:
                tags = []
            tags.append(row[0])

        return tags
    
    def get_comments():
        if nid not in nodes:
            return None
        nodename = nodes[nid]
        rows = db.execute(
            "SELECT " +
            "logs.day, " +
            "logs.time, " +
            "logs.title, " +
            "logs.comment, " +
            "logtags.logid, " +
            "substr(logtags.tag,4) as dznode " +
            "FROM logtags " +
            "INNER JOIN logs on logs.rowid = logtags.logid " +
            "WHERE tag LIKE 'dz:%'" +
            "AND dznode IS '" + nodename + "' " +
            "ORDER BY day ASC, time ASC" +
            ";"
        )

        comments = None

        for row in rows:
            day, time, title, comment, logid, dznode = row
            title = re.sub(r"\s*#[\w/_.:-]*", "", title)
            if comments is None:
                comments = []
            comments.append({
                "day": day,
                "time": time,
                "title": title,
                "comment": comment,
                "logid": logid,
                "dznode": dznode,
            })

        return comments
    
    def get_file_ranges():
        rows = db.execute(
            "SELECT filename, start, end FROM dz_file_ranges " +
            f"WHERE node == {nid} LIMIT 1"
        )

        franges = None
        for row in rows:
            filename, start, end = row
            franges = {
                "filename": filename,
                "start": int(start),
                "end": int(end),
            }

        return franges

    children = []
    node = {}
    lines = get_lines()
    remarks = None
    hyperlink = get_hyperlink()
    reference = get_reference()
    flashcard = None
    tags = get_tags()
    file_ranges = get_file_ranges()

    children = get_children(connections, nid)
    parents = get_parents(connections, nid)

    comments = get_comments()
    node["children"]= []
    node["parents"]= []

    for parent in parents:
        val = None
        if parent in nodes:
            val = shortname(path, nodes[parent])
        else:
            val = lookup_name_from_id(db, parent)
        node["parents"].append(val)

    for child in children:
        nodename = None
        if child in nodes:
            nodename = shortname(path, nodes[child])
        else:
            nodename = lookup_name_from_id(db, child)

        val = nodename

        cr = get_connection_remarks(db, child, nid)

        if cr:
            val = {
                "name": nodename,
                "remarks": cr
            }


        node["children"].append(val)

    if nid in nodes:
        node["name"] = shortname(path, nodes[nid])
    else:
        node["name"] = lookup_name_from_id(db, nid)

    if lines:
        node["lines"] = lines
    if remarks:
        node["remarks"] = remarks

    if hyperlink: 
        node["hyperlink"] = hyperlink

    node["nid"] = nid

    if reference:
        node["reference"] = reference
    
    if flashcard:
        node["flashcard"] = flashcard

    if tags:
        node["tags"] = tags

    if comments:
        node["comments"] = comments

    if file_ranges:
        node["file_ranges"] = file_ranges

    return node, children

def get_top_nodes(nodes, connections):
    top_nodes = []
    def any_local_nodes(receiving_nodes):
        for nid in receiving_nodes:
            if nid in nodes:
                return True
        return False

    for nid in nodes:
        if nid not in connections or any_local_nodes(connections[nid]) == False:
            top_nodes.append(nid)
    
    return top_nodes

def get_children(connections, nid):
    children = []
    for left, rcons in connections.items():
        for right in rcons:
            if right == nid:
                children.append(left)
    return children

def get_parents(connections, nid):
    if nid not in connections:
        return []

    parents = []

    for right in connections[nid]:
        parents.append(right)

    return parents

def childtree(nodes, connections, namespace, nid, db, xnodes):
    tree = []
    tree_nodes = []

    external_node = False
    node_name = None
    if nid not in nodes:
        external_node = True
        xnode_name = lookup_name_from_id(db, nid)
        assert(xnode_name is not None)
        xnodes[xnode_name] = nid
        node_name = xnode_name

    if external_node == False:
        node_name = shortname(namespace, nodes[nid])

    children = get_children(connections, nid)
    tree.append(node_name)

    for child in children:
        append_tree(tree_nodes, nodes, connections, namespace, child, db, xnodes)
    
    if len(tree_nodes) == 0:
        tree = tree[0]
    else:
        tree.append(tree_nodes)
    return tree

def append_tree(tree, nodes, connections, namespace, nid, db, xnodes):
    newtree = childtree(nodes, connections, namespace, nid, db, xnodes)
    tree.append(newtree)

def generate_tree(nodes, connections, namespace, db):
    tree = []
    xnodes = {}

    top_nodes = get_top_nodes(nodes, connections)

    for top in top_nodes:
        append_tree(tree, nodes, connections, namespace, top, db, xnodes)

    return tree, xnodes

def node_object(db, path, nodes, subgraphs):
    obj = {}
    traversed = set()
    connections = create_connections(db, nodes)
    nodelist = []

    def traverse_node(nid):
        if nid not in traversed:
            traversed.add(nid)
            node, children = generate_node_data(
                nodes,
                connections,
                path,
                db,
                nid
            )
            nodelist.append(node)
            return children
        return []

    def traverse_children(children):
        for child in children:
            traverse_node(child)

    # skipping topsort for now, is it actually needed?
    for nid in nodes:
        if nid not in traversed:
            children_nids = traverse_node(nid)
            if len(children_nids) > 0:
                traverse_children(children_nids)                


    tree, xnodes = generate_tree(nodes, connections, path, db)
    obj["nodes"] = nodelist
    obj["namespace"] = path
    obj["tree"] = tree
    obj["remarks"] = []
    obj["subgraphs"] = subgraphs
    return obj

def generate_page_data(db, h, lookup, namespace, pglist, data_files):
    nodes = {}
    subgraphs = []
    namespace = namespace or []
    pglist = pglist or {}

    for name, children in h.items():
        nchildren = len(children)
        if nchildren > 0:
            subgraphs.append(name)
            namespace.append(name)
            generate_page_data(db, children, lookup, namespace, pglist, data_files)

            # subgraph may sometimes be a node

            fullpath = name
            if len(namespace) > 0:
                fullpath = "/".join(namespace)

            if fullpath in lookup:
                nid = lookup[fullpath]
                nodes[nid] = fullpath
            namespace.pop()
        else:
            fullpath = name
            if len(namespace) > 0:
                fullpath = "/".join(namespace) + "/" + name
            
            nid = lookup[fullpath]
            nodes[nid] = fullpath

    nspath = "/".join(namespace)
    print(nspath)
    obj = node_object(db, nspath, nodes, subgraphs)
    data_files.write(nspath, obj)

class DataFiles:
    def __init__(self, keyfile="data_keys", contentsfile="data_contents"):
        self.keys = open(keyfile, "w")
        self.contents = open(contentsfile, "w")
        self.offset = 0

    def close(self):
        self.keys.close()
        self.contents.close()

    def write(self, key, data):
        data_str = json.dumps(data)
        self.keys.write(":".join(("/" + key, str(self.offset), str(len(data_str)))) + "\n")
        self.offset += len(data_str)
        self.contents.write(data_str)

def generate(dbpath, keyfile="data_keys", contentsfile="data_contents"):
    db = sqlite3.connect(dbpath)

    cur = db.cursor()

    rows = cur.execute(" ".join([
        "SELECT name, id, position FROM dz_nodes",
        "ORDER BY name ASC",
    ]))

    h = {}
    lookup = {}

    for row in rows:
        name, idnum, _ = row
        names = name.split('/')
        top = h
        for nm in names:
            if nm not in top:
                top[nm] = {}
            top = top[nm]
        lookup[name] = idnum


    data_files = DataFiles(keyfile, contentsfile)
    generate_page_data(cur, h, lookup, None, None, data_files)
    data_files.close()

# generate("../recurse/a.db")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} dz_databse.db")
        exit(1)
    argv = sys.argv
    dbfile = argv[1]
    keyfile = argv[2] if len(argv) >= 3 else "data_keys"
    contentsfile = argv[3] if len(argv) >= 4 else "data_contents"
    generate(dbfile, keyfile, contentsfile)
