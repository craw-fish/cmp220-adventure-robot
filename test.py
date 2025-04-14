import json
from http.server import HTTPServer


data = open("robophotos.json")
mydata = json.load(data)
html = "<html>"
for robo in mydata:
    print(robo["robot"])
    html += """</a>    
    <a href="Roboblog1.html">
        <button>
            About Me
        </button>"""
    
html += "</html>"

print(html)