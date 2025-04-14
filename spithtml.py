import codecs
import json
from http.server import HTTPServer




data = open("robophotos.json")
mydata = json.load(data)
html = "<html>"
print(html)

f= open('GFG.html', 'w')

html_template="""
<html> 
<head>
</head>

<body> 
<p>Hello World! </p> 
  
</body> 
</html> 
"""
f.write(html_template)
f.close
file=codecs.open("new.html",'r','utf-8')


print(file.read()) 