#!/usr/bin/env python3
import logparse
import sys 
import sqlite3

logfiles = sys.argv[1]

con = sqlite3.connect("a.db")
cur = con.cursor()

cur.execute("DROP TABLE IF EXISTS dayblurbs;")
cur.execute("DROP TABLE IF EXISTS logs;")
cur.execute("DROP TABLE IF EXISTS logtags;")

with open(logfiles) as fp:
    for line in fp:
        print(line[:-1])
        sql = logparse.run(line[:-1], use_stdout = False)
        cur.executescript(sql)
        con.commit()

con.close()
