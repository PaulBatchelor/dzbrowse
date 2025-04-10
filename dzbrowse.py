#! /usr/bin/env python3
from pprint import pprint
import json
import re
import html as htmllib

def render_subgraph(subgraphs, namespace=""):
    html = ""
    html += "<ul>"
    node_url = "/dz/"
    if len(namespace) > 0:
        node_url += namespace + "/"
    subgraphs.sort()
    for sg in subgraphs:
        html += f"<li><a href=\"{node_url + sg}\">{sg}</a></li>\n"
    html += "</ul>"
    return html

def abbreviate_node(namespace, nodepath):
    return re.sub("^" + namespace + "/", "", nodepath)

def nodelink(namespace, nodepath):
    node_url = "#" + nodepath
    if "/" in nodepath:
        path_segments = nodepath.split("/")
        node_url = "/dz/"
        node_url += "/".join(path_segments[0:len(path_segments) - 1])
        node_url += "#" + path_segments[-1]
    return f"<a href=\"{node_url}\">{abbreviate_node(namespace, nodepath)}</a>"

def treelink(namespace, nodepath):
    # treename = abbreviate_node(namespace, nodepath)
    return f"<li>{nodelink(namespace, nodepath)}</li>\n"

def render_nodetree(nodetree, namespace):
    html = ""
    html += "<ul>"
    for tree in nodetree:
        if isinstance(tree, str):
            # treename = re.sub("^" + namespace + "/", "", tree)
            html += treelink(namespace, tree)
        else:
            html += treelink(namespace, tree[0])
            html += render_nodetree(tree[1], namespace + "/" + tree[0])

    html += "</ul>"
    return html

def is_local_node(node):
    return "/" not in node['name']


def path_to_link(curnamespace, path, subgraph=False):
    def localize(path):
        if "/" not in path:
            path = "/".join(curnamespace.split("/")[:-1]) + "/" + path
        return path
    def mklink(path, name, remarks=None):
        path_parts = path.split("/")

        sep = "#"

        if subgraph:
            sep = "/"

        path_plus_key="/".join(path_parts[:-1]) + sep + path_parts[-1]
        link = f"<a href=\"/dz/{path_plus_key}\">{name}</a>"

        if remarks:
            link += " ("
            link += " ".join(remarks)
            link += ")"
        return link
    if isinstance(path, str):
        return mklink(localize(path), abbreviate_node(curnamespace, path))
    return mklink(localize(path['name']), abbreviate_node(curnamespace, path['name']), path['remarks'])

def render_card(node, namespace):
    html = ""

    html += "<table>\n"
    html += "<tbody>\n"

    basename = node['name'].split("/")[-1]
    html += "<tr>\n"
    html += "<th scope=\"row\" colspan=2>\n"
    html += f"<a id='{basename}'>"
    html += f"<a href='#{basename}'>"
    html += f"{basename}\n"
    html += f"</a>"
    html += f"</a>"
    html += "</th>\n"
    html += "</tr>\n"

    curnamespace = namespace + "/" + node['name']

    def lines(params):
        return ("content", " ".join(params))

    def children(params):
        childlinks = []
        for p in params:
            childlinks.append(path_to_link(curnamespace, p))
        return ("children", ", ".join(childlinks))

    def parents(params):
        parentlinks = []
        for p in params:
            parentlinks.append(path_to_link(curnamespace, p))

        return ("parents", ", ".join(parentlinks))

    def remarks(params):
        return ("remarks", " ".join(params))

    def hyperlink(params):
        url = f"<a href=\"{params}\">{params}</a>"
        return ("hyperlink", url)

    def reference(params):
        return ("location", f"{params['filename']}:{params['linum']}")

    def flashcard(params):
        return ("flashcard",
                f"<p>front: {' '.join(params['front'])}</p>" +
                f"<p>back: {' '.join(params['back'])}</p>")

    def tags(params):
        taglinks = []
        for tag in params:
            taglinks += [f"<a href=\"/tag/{tag}\">{tag}</a>"]
        return ("tags", ", ".join(taglinks))

    def file_ranges(params):
        filename = params["filename"]
        start = params["start"]
        end = params["end"]
        linerange = ""

        if start >= 0:
            linerange = f":{start}"
            if end >=0:
                linerange += f"-{end}"

        out = filename + linerange

        if "code" in params:
            snippet = ""
            snippet += "<details>\n"
            snippet += f"<summary>{filename + linerange}</summary>\n"
            snippet += "<pre><code>"
            snippet += htmllib.escape("\n".join(params["code"]))
            snippet += "</code></pre>"
            snippet += "</details>\n"
            out = snippet

        return ("File Range", out)

    def subgraph(params):
        return (
            "subgraph",
            path_to_link(namespace, curnamespace, subgraph=True)
        )

    attributes = {
        "reference": reference,
        "lines": lines,
        "children": children,
        "parents": parents,
        "remarks": remarks,
        "hyperlink": hyperlink,
        "flashcard": flashcard,
        "tags": tags,
        "file_ranges": file_ranges,
        "subgraph": subgraph,
    }
    html += "<tr>\n"
    html += "<th>\n"
    html += "path\n"
    html += "</th>\n"
    html += "<td>\n"
    html += f"{curnamespace}\n"
    html += "</td>\n"
    html += "</tr>\n"

    for attr, atfun in attributes.items():
        if attr in node:
            html += "<tr>\n"
            label, content = atfun(node[attr])
            html += "<th>\n"
            html += label + "\n"
            html += "</th>\n"
            html += "<td>\n"
            html += content + "\n"
            html += "</td>\n"
            html += "</tr>\n"

    if "comments" in node:
        html += "<tr>\n"
        html += "<th scope=\"row\" colspan=2>\n"
        html += f"Comments\n"
        html += "</th>\n"
        html += "</tr>\n"
        for comment in node["comments"]:
            html += "<tr>\n"
            html += "<td>\n"
            html += f"<p>{comment['day']} {comment['time']}</p>\n"
            html += "</td>\n"
            html += "<td>\n"
            html += f"<p>{comment['title']}"
            if len(comment["comment"]) > 0:
                html += "</p>\n"
                for cmt in comment["comment"]:
                    html += "<p>"
                    html += cmt
                    html += "</p>\n"
            html += "</p>\n"
            html += "</td>\n"
            html += "</tr>\n"

    html += "</tbody>\n"
    html += "</table>\n"
    return html

def render_node_cards(nodes, namespace):
    html = ""
    for node in nodes:
        if is_local_node(node):
            html += render_card(node, namespace)
    return html

def render_remarks(blob):
    html = ""
    if 'remarks' in blob:
        html += "<h2>Summary</h2>\n"
        html += f"<p>{' '.join(blob['remarks'])}</p>\n"

    return html

def render_url(namespace):
    path_segments = []
    namespace = "dz/" + namespace
    curpath = []
    for segment in namespace.split("/"):
        curpath.append(segment)
        path_link = f"<a href=\"/{'/'.join(curpath)}\">{segment}</a>"
        path_segments.append(path_link)
    return " / ".join(path_segments)

def generate_page(path, data_keys, data_content):
    data_content.seek(data_keys[path][0])
    blob = json.loads(data_content.read(data_keys[path][1]))
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="/style.css" rel="stylesheet"/>
        <title>{blob['namespace']}</title>
    </head>
    <body>
        <h1>{blob['namespace']}</h1>
        {render_url(blob['namespace'])}
        {render_remarks(blob)}
        <h2>Subgraphs</h2>
        {render_subgraph(blob['subgraphs'], blob['namespace'])}
        <h2>Node Tree</h2>
        {render_nodetree(blob['tree'], blob['namespace'])}
        <h2>Nodes</h2>
        {render_node_cards(blob['nodes'], blob['namespace'])}
    </body>
    </html>
    """
    return template

def open_data_files(keyfile, contentsfile):
    data_keys = {}
    with open(keyfile) as fp:
        for line in fp:
            row = line.split(":")
            data_keys[row[0]] = [int(row[1]), int(row[2])]

    data_content = open(contentsfile)
    return data_keys, data_content

# for testing purposes...
if __name__ == "__main__":
    import sys
    data_keys, data_content  = open_data_files("data_keys", "data_contents")
    path = sys.argv[1]
    print(generate_page(path, data_keys, data_content))
    data_content.close()
