import http.server
import requests
from urllib.parse import unquote, parse_qs
import os
import threading
from socketserver import ThreadingMixIn

memory = {}

form = '''<!DOCTYPE html>
<head>
        <link rel="stylesheet" href="/style.css"/>
        <title>Martha's Bookmarks</title>
</head>
<body>
    <div class="back">

    </div>
        
    <div class="content">
        <h1>Martha's Bookmarks</h1>
        <br>
        <br>
        <form method="POST">
            <label>Long URI:</label>
            <input name="longuri" required >
            <br>
            <br>
            <label>Short name:</label>
            <input name="shortname" required>
            <br>
            <br>
            <button type="submit">Save</button>
        </form>
        
        <br>
        <br>
        
         <label>URIs I know about:</label>
            <br>
            <br>
            <pre>{}</pre>
         
    
    </div>
</body>
'''

style = '''
* {
    margin: 0;
    padding: 0;
    text-decoration: none; 
}

body {
    color: white;
    font-family: Verdana, Geneva, sans-serif;
}

.back {
    position: fixed;
    height: 100%;
    width: 100%;
    background: linear-gradient(90deg, hsla(333, 100%, 53%, 1) 0%, hsla(33, 94%, 57%, 1) 100%);
    z-index: -1;
}

.content {
    text-align: center;
    padding: 0;
    margin: 0;
    position: absolute;
    top: 50%;
    left: 50%;
   -ms-transform: translate(-50%, -50%);
    transform: translate(-50%, -50%);
    padding: 2rem;
    border: white solid 0.2rem;
}

h1 {
    font-size: 6rem;
    font-weight: lighter;
    white-space: nowrap;
}

label {
    font-size: 2rem;
}

input {
    background-color: Transparent;
    color: white;
    border: white solid 0.2rem;
    font-size: 2rem;
    padding: 10px;
    outline: none;
}

button {
    background-color: Transparent;
    color: white;
    border: white solid 0.2rem;
    font-size: 2rem;
    padding: 10px;
    -webkit-appearance: none;
    -moz-appearance: none;
}

button:active {
    outline: none;
    padding: 15px;
    margin: -5px;
}

button:focus {
    outline: none;
}

.truncate {
    width: 65rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

div {
    margin-bottom: 1rem;
}

'''


def CheckURI(uri, timeout=5):

    try: 
        r = requests.get(uri, timeout = timeout)

        return r.status_code == 200
    
    except requests.RequestException:

        return False 

class ThreadHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    "This is an HTTPServer that supports thread-based concurrency."

class Shortener(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        name = unquote(self.path[1:])

        if name == "style.css" :
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()

            self.wfile.write(style.encode())
        
        elif name:
            if name in memory:
                self.send_response(303)
                self.send_header('Location', memory[name])
                self.end_headers()
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("I don't know '{}'.".format(name).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            known = "<br><br>".join('''<form method="POST"><label> <div class="truncate">{} : {}</div> <input type="hidden" name="delete" value="true" > <input type="hidden" name="longuri" value={} > <input  type="hidden" name="shortname" value={} > <button style="font-size: 1rem;" >Delete</button></label></form>'''.format(key, memory[key] ,memory[key] , key)
                              for key in sorted(memory.keys()))
            self.wfile.write(form.format(known).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)

        if "longuri" not in params or "shortname" not in params:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Form fields missing".encode())
            return

        longuri = params["longuri"][0]
        shortname = params["shortname"][0]

        if "delete" in params:
            del memory[shortname]
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
            return

        if CheckURI(longuri):
            memory[shortname] = longuri

            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Couldn't fetch URI '{}'. Sorry!".format(longuri).encode())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server_address = ('', port)
    httpd = ThreadHTTPServer(server_address, Shortener)
    httpd.serve_forever()