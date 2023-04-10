from bs4 import BeautifulSoup
import json
import pandas as pd
import pygsheets
import re
import requests
import yagmail

thresholds = {
    "contact@dantebarbieri.dev": {
        "": 1350 # All
    },
    "anjalicutiesegu@gmail.com": {
        "": 1350 # All
    }
}

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

sender_email = "dantevbarbieri@gmail.com"
email_password = ""
try:
    with open('/home/azureuser/email_password') as f:
        email_password = f.read()
except(FileNotFoundError):
    pass

yag = yagmail.SMTP(sender_email, email_password)

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
    if "Renovated" in floorplan["name"]:
        for email, limits in thresholds.items():
            for name, limit in limits.items():
                if name in floorplan["name"] and floorplan["lowPrice"] < limit:
                    print(f"Sending an email from {sender_email} to {email} about {floorplan['name']} which is ${floorplan['lowPrice']}/mo which is below their limit of ${limit}/mo.")
                    subject = f'Riata Price Alert {floorplan["name"]} is ${floorplan["lowPrice"]}/mo which is below your limit of ${limit}/mo'
                    contents = f'{floorplan["name"]} ({floorplan["sqft"]} sq. ft.) with {floorplan["beds"]} bed(s) and {floorplan["baths"]} bath(s) is starting at ${floorplan["lowPrice"]}/mo which is below your limit of ${limit}/mo. The high price is ${floorplan["highPrice"]}/mo. The earliest available date is {floorplan["availableDate"]} (THIS MAY NOT MATCH THE DATE OF THE UNIT WITH THE LOWEST PRICE!!). There are {len(floorplan["unitList"])} units available. The unit list is {floorplan["unitList"]}. For more information, go to {URL}. Apply today at https://riata.com/.'
                    yag.send(email, subject, contents)

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