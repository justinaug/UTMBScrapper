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
    obj["BibNumber"] = raw_xml["doss"] if "doss" in raw_xml.attrs else ""
    obj["Surname"] = raw_xml["nom"] if "nom" in raw_xml.attrs else ""
    obj["FirstNames"] = raw_xml["prenom"] if "prenom" in raw_xml.attrs else ""
    obj["Gender"] = raw_xml["sx"] if "sx" in raw_xml.attrs else ""
    obj["Country"] = raw_xml["cio"] if "cio" in raw_xml.attrs else ""
    obj["TotalTime"] = raw_xml["tps"] if "tps" in raw_xml.attrs else ""
    obj["Category"] = raw_xml["cat"] if "cat" in raw_xml.attrs else ""
    update_category_count(raw_xml["cat"])
    obj["CategoryPosition"] = category_count[raw_xml["cat"]] if "cat" in raw_xml.attrs else ""
    return obj

def update_category_count(category):
    global category_count
    if category in category_count:
        category_count[category] += 1  # Increment value by 1
    else:
        category_count[category] = 1  # Add element with a value of 1

def scrape_checkpoints(raw_xml):
    points = {}
    for p in raw_xml.find_all('points')[0].find_all('p'):
        if p["idpt"] == '0':
            points[p["idpt"]] = "Start"
        else:
            points[p["idpt"]] = p["n"]
    return points


race_results_url = "https://livetrail.net/histo/uts_2024/teteCourse.php?course=100m&cat=scratch&mode=full"
ind_racer_url = "https://livetrail.net/histo/uts_2024/coureur.php?rech="
page = requests.get(race_results_url)
print(page.content)

soup = BeautifulSoup(page.text, "lxml-xml")
invalid_url_text = soup.find(string="requete1 invalide") # love the french
if invalid_url_text:
    print("Invalid Race Results URL: " + race_results_url)
    quit()

data = {}
counter = 1
category_count = {}

points = scrape_checkpoints(soup)

print(points)

for c in soup.find_all('c'):
    try:
        if c["doss"] is not None:
            print(counter)
            useful_details = extract_details(c)
            page = requests.get(ind_racer_url + c["doss"])
            soup2 = BeautifulSoup(page.text, "lxml-xml")
            # handle if the racer cannot be found - Could be a bad url
            valid_url_attr = soup2.find("fiche")  # love the french
            if not valid_url_attr:
                print("Invalid Racer Results URL: " + ind_racer_url + c["doss"])
                useful_details["UTMB"] = "ERR"
                for p in points:
                    useful_details[p] = "ERR"
            else:
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

with open('UTS_2024_100m.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

df = pd.DataFrame(data).T

df.columns = list(data[next(iter(data))].keys())

excel_file = "UTS_2024_100m.xlsx"  # Replace with your desired Excel file name
df.to_excel(excel_file, index=False)

print(f"JSON data has been successfully exported to {excel_file}")
