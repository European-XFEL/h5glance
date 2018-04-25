import sys
from .generate import make_document

def main():
    filename = sys.argv[1]

    with open("test_output.html", 'w') as f:
        f.write(str(make_document(filename)))
