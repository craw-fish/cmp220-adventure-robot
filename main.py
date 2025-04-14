import pandas as pd

from http.server import BaseHTTPRequestHandler



url="http://localhost:5001/snapshots/AdK5Kywr4eMCvA2immSYEQ.png"
url="./robophotos.json"
df= pd.read_json(url)
print(df.info())
class RobotRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.lower().startswith("/robophotos,json"):
            self.do_robot_details()
        else:
            self.do_main_roboIndex()
    def do_main_index(self):
        with open('templates/roboIndex.html') as index_file:
            template= index_file.read()
            robots=self.fetch_photo_url
            robot_list_html=""
            for robot in robots:
                robot_list_html+="<li>"
               


#todo: 
#1- figure out how to decipher json(pandas read json or look at code from last semester)
#2- what do I need from the data? 
#3- how do I get what I need from the data?
#4- how do I bundle the data to be sent to my html?
#5- how do I send the data to the html
