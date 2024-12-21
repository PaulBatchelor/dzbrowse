import sqlite3
from pprint import pprint
import json

def node_object(db, path, nodes, subgraphs):
    obj = {}

    obj["nodes"] = []
    obj["namespace"] = path
    obj["tree"] = []
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
    generate_page_data(db, h, lookup, None, None, data_files)
    data_files.close()

generate("../recurse/a.db")