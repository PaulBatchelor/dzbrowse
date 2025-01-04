import sys
import re

def run(filepath, filename):
    fp = open(filepath)
    sql = "CREATE TABLE IF NOT EXISTS dz_textfiles(id INTEGER PRIMARY KEY, filename TEXT, linum INTEGER, data TEXT);\n"
    sql += "BEGIN;\n"
    for (i, line) in enumerate(fp):
        sql += "INSERT INTO dz_textfiles(filename, linum, data) "
        sql += "VALUES("
        sql += f"'{filename}', "
        sql += f"{i + 1}, "
        sql += f"'{re.sub("'","''", line[:-1])}'"
        sql += ");\n"
        #print(i + 1, filename, line)
        continue
    sql += "END;\n"

    print(sql)

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
