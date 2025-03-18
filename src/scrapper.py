import collections
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
import requests
import lxml

def extract_details(raw_xml):
    global category_count
    obj ={}
    obj["Surname"] = raw_xml["nom"]
    obj["FirstNames"] = raw_xml["prenom"]
    obj["Gender"] = raw_xml["sx"]
    try:
        obj["Country"] = raw_xml["cio"]
    except Exception as e:
        obj["Country"] = ""
    obj["TotalTime"] = raw_xml["tps"]
    obj["Category"] = raw_xml["cat"]
    update_category_count(raw_xml["cat"])
    obj["CategoryPosition"] = category_count[raw_xml["cat"]]
    return obj
def update_category_count(category):
    global category_count
    if category in category_count:
        category_count[category] += 1  # Increment value by 1
    else:
        category_count[category] = 1  # Add element with a value of 1

# TODO
# UTMB index - done
# splits
# where they came overall
# where they came in their age category
race_results_url = "https://livetrail.net/histo/uts_2023/teteCourse.php?course=50k&cat=scratch&mode=full"
ind_racer_url = "https://livetrail.net/histo/uts_2023/coureur.php?rech="
page = requests.get(race_results_url)
print(page.content)

soup = BeautifulSoup(page.text, "lxml")
data = {}
counter = 1
category_count = {}

points = {}
for p in soup.find_all('points')[0].find_all('p'):
    if p["idpt"] == '0':
        points[p["idpt"]] = "Start"
    else:
        points[p["idpt"]] = p["n"]

print(points)

for c in soup.find_all('c'):
    try:
        if c["doss"] is not None:
            print(counter)
            useful_details = extract_details(c)
            page = requests.get(ind_racer_url + c["doss"])
            soup2 = BeautifulSoup(page.text, "lxml")
            try:
                for palm in soup2.find_all('palm'):
                    useful_details["UTMB"] = palm["cote"]
            except Exception as e:
                useful_details["UTMB"] = ""
            for e in soup2.find_all('e'):
                try:
                    if e["idpt"] is not None:
                        useful_details[points[e["idpt"]]] = e["tps"]
                except Exception as e:
                    pass

            useful_details["OverallPosition"] = counter
            data[c["doss"]] = useful_details
            time.sleep(0.05)
            counter +=1
    except Exception as e:
        continue

with open('UTS_2023.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

df = pd.DataFrame(data).T

df.columns = list(data[next(iter(data))].keys())

excel_file = "UTS_2023.xlsx"  # Replace with your desired Excel file name
df.to_excel(excel_file, index=False)

print(f"JSON data has been successfully exported to {excel_file}")
