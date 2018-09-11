"""Command line h5glance-html interface for writing and serving HTML views of HDF5
"""
import argparse
import h5py
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys
import threading
import webbrowser

from .generate import make_document

def main(argv=None):
    ap = argparse.ArgumentParser(prog="h5glance",
                                 description="View HDF5 file structure in HTML")
    ap.add_argument("input", help="HDF5 file to view", type=Path)
    ap.add_argument("-w", "--write", metavar="HTML_FILE",
                    help="Write output to HTML file.")
    args = ap.parse_args(argv)

    if not args.input.is_file():
        print("Not a file:", args.input)
        sys.exit(2)
    elif not h5py.is_hdf5(args.input):
        print("Not an HDF5 file:", args.input)
        sys.exit(2)

    if args.write:
        with open("test_output.html", 'w') as f:
            f.write(str(make_document(args.input)))
            return

    serve(args.input)

def serve(h5path):
    class H5ViewHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/":
                return self.send_error(404)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(make_document(h5path)).encode('utf-8'))

    server = HTTPServer(('localhost', 0), H5ViewHandler)
    url = "http://{}:{}/".format(server.server_name, server.server_port)
    print("Serving on", url)
    t = threading.Timer(0.5, webbrowser.open_new_tab, args=(url,))
    t.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
