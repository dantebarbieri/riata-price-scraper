from bs4 import BeautifulSoup
import json
import pandas as pd
import pygsheets
import re
import requests

gc = pygsheets.authorize(service_file='./creds.json')

sh = gc.open('Riata Historic Prices')

wks = sh[0]

URL = "https://riata.securecafe.com/onlineleasing/riata1/floorplans"
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")

startRow = 2
try:
    with open('/home/azureuser/record-count.cfg') as f:
        text = f.read()
        if len(text) > 0 and text.strip().isdigit():
            startRow = int(text)
except(FileNotFoundError):
    pass

jsonKeysRE = re.compile(r'^(\s*)(\w+):', re.MULTILINE)

scripts = soup.find_all("script")
for script in scripts:
    if "var pageData" in script.text:
        pageData = script.text.split(" = ")[1].strip()[:-1]
        fixedPageData = re.sub(jsonKeysRE, r'\1"\2":', pageData)
        # print(fixedPageData)
        js = json.loads(fixedPageData)

print("name", "beds", "baths", "sqft", "lowPrice", "highPrice", "availableDate", "unitCount", "unitList", sep="\t")
df = pd.DataFrame()
dates = []
names = []
beds = []
baths = []
sqfts = []
lowPrices = []
highPrices = []
availableDates = []
unitCounts = []
unitLists = []
for floorplan in js["floorplans"]:
    print(floorplan["name"], floorplan["beds"], floorplan["baths"], floorplan["sqft"], floorplan["lowPrice"], floorplan["highPrice"], floorplan["availableDate"], len(floorplan["unitList"]), floorplan["unitList"], sep="\t")
    dates.append(pd.Timestamp.now())
    names.append(floorplan['name'])
    beds.append(floorplan['beds'])
    baths.append(floorplan['baths'])
    sqfts.append(floorplan['sqft'])
    lowPrices.append(floorplan['lowPrice'])
    highPrices.append(floorplan['highPrice'])
    availableDates.append(floorplan['availableDate'])
    unitCounts.append(len(floorplan["unitList"]))
    unitLists.append(floorplan['unitList'])

df['date'] = dates
df['name'] = names
df['beds'] = beds
df['baths'] = baths
df['sqft'] = sqfts
df['lowPrice'] = lowPrices
df['highPrice'] = highPrices
df['availableDate'] = availableDates
df['unitCount'] = unitCounts
df['unitList'] = unitLists

wks.set_dataframe(df,(startRow,1), copy_head=False, extend=True)

with open('/home/azureuser/record-count.cfg', 'w') as f:
    f.write(str(startRow + len(js["floorplans"])))