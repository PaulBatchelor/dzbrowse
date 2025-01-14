#! /usr/bin/env python3
import import_code

def run(top, codefiles="codefiles.txt"):
    with open(codefiles) as fp:
        for line in fp:
            file, path = line.split()[:2]
            file = f"{top}/{file}"
            import_code.run(file, path)

if __name__ == "__main__":
    import sys
    top = "."
    codefiles="codefiles.txt"
    if len(sys.argv) > 1:
        top = sys.argv[1]

    if len(sys.argv) > 2:
        codefiles = sys.argv[2]

    run(top,codefiles=codefiles)
