from bs4 import BeautifulSoup
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

desired_floorplans = [
    "oak-renovated",
    "cedar-renovated",
    "magnolia-renovated",
    "sage-renovated",
    "aster-renovated",
    "laurel-renovated",
]

gc = pygsheets.authorize(service_file='./creds.json')

sh = gc.open('Riata Unit Prices')

wks = sh[0]

startRow = 2
try:
    with open('/home/azureuser/unit-count.cfg') as f:
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

print("name", "unit", "price", "available", sep="\t")
df = pd.DataFrame()
dates = []
names = []
units = []
prices = []
availabilities = []
for floorplan in desired_floorplans:
    URL = f"https://riata.com/floorplans/{floorplan}/"
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    rows = soup.find_all("tr", class_="check-availability__row--with-exterior-actions")
    for row in rows:
        apt = re.sub(r'\s+', '', row.find("td", class_="check-availability__cell--unit").text)
        price = row.find("td", class_="check-availability__cell--price").text.strip()
        numprice = int(re.sub(r'[$,]', '', price))
        available = row.find("td", class_="check-availability__cell--availability").text.strip()
        print(floorplan, apt, price, available, sep="\t")
        dates.append(pd.Timestamp.now())
        names.append(floorplan)
        units.append(apt)
        prices.append(price)
        availabilities.append(available)
        for email, limits in thresholds.items():
            for name, limit in limits.items():
                if name.lower() in floorplan.lower() and numprice < limit:
                    print(f"Sending an email from {sender_email} to {email} about {floorplan} which is {price}/mo which is below their limit of ${limit}/mo.")
                    subject = f'Riata Unit Price Alert | {floorplan} at {apt} is {price}/mo which is below your limit of ${limit}/mo'
                    contents = f'{floorplan} unit {apt} is starting at {price}/mo which is below your limit of ${limit}/mo. The earliest available date is {available}. For more information, go to {URL}.'
                    yag.send(email, subject, contents)

df['date'] = dates
df['name'] = names
df['unit'] = units
df['price'] = prices
df['available'] = availabilities

wks.set_dataframe(df,(startRow,1), copy_head=False, extend=True)

with open('/home/azureuser/unit-count.cfg', 'w') as f:
    f.write(str(startRow + len(dates)))