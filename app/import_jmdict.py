import xml.etree.ElementTree as ET
from db import get_connection

tree = ET.parse("data/JMdict_e")
root = tree.getroot()

conn = get_connection()
cursor = conn.cursor()

for entry in root.findall("entry"):

    word = None
    reading = None

    k_ele = entry.find("k_ele")
    if k_ele is not None:
        keb = k_ele.find("keb")
        if keb is not None:
            word = keb.text

    r_ele = entry.find("r_ele")
    if r_ele is not None:
        reb = r_ele.find("reb")
        if reb is not None:
            reading = reb.text

    if not word and not reading:
        continue

    cursor.execute(
        "INSERT INTO dictionary_entries(word, reading) VALUES(%s,%s)",
        (word, reading)
    )

    entry_id = cursor.lastrowid

    for sense in entry.findall("sense"):
        for gloss in sense.findall("gloss"):
            cursor.execute(
                "INSERT INTO dictionary_meanings(entry_id, meaning) VALUES(%s,%s)",
                (entry_id, gloss.text)
            )

conn.commit()
cursor.close()
conn.close()
