#! /usr/bin/env python3
import import_code

def run(top):
    with open("codefiles.txt") as fp:
        for line in fp:
            file, path = line.split()[:2]
            file = f"{top}/{file}"
            import_code.run(file, path)

if __name__ == "__main__":
    import sys
    top = "."
    if len(sys.argv) > 1:
        top = sys.argv[1]
    run(top)
