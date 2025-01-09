#!/usr/bin/env python3
import sys
import subprocess
import sqlite3

def run(args):
    dzfiles = "dzfiles.txt"

    if len(args) > 1:
        dzfiles = args[1]

    con = None
    cur = None
    if len(args) > 2:
        dbfile = args[2]
        con = sqlite3.connect(dbfile)
        cur = con.cursor()

    if cur:
        cur.executescript("\n".join([
        "DROP TABLE IF EXISTS dz_nodes;",
        "DROP TABLE IF EXISTS dz_connections;",
        "DROP TABLE IF EXISTS dz_connection_remarks;",
        "DROP TABLE IF EXISTS dz_lines;",
        "DROP TABLE IF EXISTS dz_remarks;",
        "DROP TABLE IF EXISTS dz_hyperlinks;",
        "DROP TABLE IF EXISTS dz_tags;",
        "DROP TABLE IF EXISTS dz_graph_remarks;",
        "DROP TABLE IF EXISTS dz_flashcards;",
        "DROP TABLE IF EXISTS dz_file_ranges;",
        "DROP TABLE IF EXISTS dz_images;",
        "DROP TABLE IF EXISTS dz_audio;",
        "DROP TABLE IF EXISTS dz_textfiles;",
        "DROP TABLE IF EXISTS dz_pages;",
        "DROP TABLE IF EXISTS dz_todo;",
        "DROP TABLE IF EXISTS dz_noderefs;",
    ]))


    with open(dzfiles) as fp:
        for line in fp:
            args = ["dagzet"]
            args.extend(line[:-1].split())
            if cur:
                print(line[:-1])
                rc = subprocess.run(args, capture_output=True)
                #print(rc.stdout.decode())
                cur.executescript(rc.stdout.decode())
            else:
                subprocess.run(args)

if __name__ == "__main__":
    run(sys.argv)
