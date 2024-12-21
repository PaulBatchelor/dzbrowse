import sqlite3
from pprint import pprint
import json
import re

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

def generate_node_data(nodes, connections, path, db, nid):
    children = []
    node = {}
    lines = None
    remarks = None
    hyperlink = None
    reference = None
    flashcard = None

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
        node.reference = reference
    
    if flashcard:
        node.flashcard = flashcard


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
    def __init__(self):
        self.keys = open("data_keys", "w")
        self.contents = open("data_contents", "w")
        self.offset = 0

    def close(self):
        self.keys.close()
        self.contents.close()

    def write(self, key, data):
        data_str = json.dumps(data)
        self.keys.write(":".join(("/" + key, str(self.offset), str(len(data_str)))) + "\n")
        self.offset += len(data_str)
        self.contents.write(data_str)

def generate(dbpath):
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


    data_files = DataFiles()
    generate_page_data(cur, h, lookup, None, None, data_files)
    data_files.close()

generate("../recurse/a.db")