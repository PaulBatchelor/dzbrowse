#!/usr/bin/env python3
import sys
import re
import json
from pprint import pprint

def parse(filename):
    lines = None
    with open(filename) as fp:
        lines = fp.readlines()
    p = re.compile(r"^@([^ ]*)(\s+(.*))?")
    blocks = []
    p_ex = re.compile(r"^#! (.*)")
    blkpos = -1
    for line in lines:
        m = p.match(line)
        if m:
            blkpos += 1
            newblock = {
                "name": m.group(1),
                "title": m.group(2) or "",
                "lines": [],
                "ex": [],
            }
            blocks.append(newblock)
            continue
        if blkpos >= 0 and len(line) > 1:
            m = p_ex.match(line)
            if m:
                cmd = m.group(1)
                blocks[blkpos]["ex"].append(cmd)
                continue
            blocks[blkpos]["lines"].append(line[:-1])

    return blocks


def escape_sql(sql):
    return re.sub("'", "''", sql)

def extract_tags(title):
    tags = []

    for word in title.split():
        if word[0] == "#":
            tags.append(word[1:])

    return tags

def generate_sql(blocks):
    sql = ""
    sql += "BEGIN;\n";
    sql += '\n'.join((
        "CREATE TABLE IF NOT EXISTS logs(",
        "day TEXT, ",
        "time TEXT, ",
        "title TEXT, ",
        "comment TEXT, ",
        "position INTEGER, ",
        "category TEXT);",
        "CREATE TABLE IF NOT EXISTS dayblurbs(",
        "day TEXT, ",
        "title TEXT, ",
        "blurb TEXT); ",
        "CREATE TABLE IF NOT EXISTS logtags(",
        "logid INTEGER, ",
        "tag TEXT); ",
    ))

    p_day = re.compile(r"^(\d\d\d\d-\d\d-\d\d)(#.*)?")
    p_time = re.compile(r"^(\d\d:\d\d)")

    curday = None
    pos = 0
    category = ""

    def sqltag(tag):
        s = "INSERT INTO logtags(logid, tag) "
        s += f"VALUES ((SELECT max(rowid) from logs), '{tag}');\n"
        return s

    pnode = None
    for block in blocks:
        r = p_day.match(block["name"])
        if r:
            if r.group(2):
                category = r.group(2)[1:]
            else:
                category = ""
            curday = r.group(1)
            sql += "INSERT INTO dayblurbs(day, title, blurb) "
            sql += f"VALUES ('"
            sql += f"{curday}', "
            sql += f"'{escape_sql(block["title"])}', "
            sql += f"'{' '.join(map(escape_sql, block["lines"]))}');\n"
            pos = 1

            continue

        if p_time.match(block["name"]):
            if curday is None:
                raise Exception("No day selected")
            sql += "INSERT INTO logs(day, time, title, comment, position, category) "
            sql += "VALUES ("
            sql += f"'{curday}', "
            sql += f"'{block["name"]}', "
            sql += f"'{escape_sql(block["title"])}', "
            sql += f"'{' '.join(map(escape_sql, block["lines"]))}', "
            sql += f"{pos}, "
            sql += f"'{category}'"
            sql += ");\n"
            pos += 1


            for tag in extract_tags(block["title"]):
                sql += sqltag(tag)

            for cmd in block["ex"]:
                args = cmd.split()
                if args[0] == "dz":
                    if args[1][0] == "$" and pnode:
                        tail = ""
                        if len(args[1]) > 1:
                            tail = args[1][1:]
                        sql += sqltag("dz:" + pnode + tail)
                    else: 
                        sql += sqltag("dz:" + args[1])
                        pnode = args[1]

                continue

            continue
    sql += "COMMIT;\n";


    return sql

def run(filename, use_stdout = True):
    blocks = parse(filename)
    sql = generate_sql(blocks)
    if use_stdout:
        print(sql)
    else:
        return sql


if __name__ == "__main__":
    run(sys.argv[1])
