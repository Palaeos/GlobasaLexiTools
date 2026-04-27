import pandas as pd
import csv

edited_frame = pd.read_csv('word-list.csv', index_col=0, sep=",", keep_default_na=False)

menalari_name = "word-list original.csv"

menalari_patch = "word-list patch.csv"

with open("./" + menalari_name, newline='') as menalari_file, open("./menaPatch.csv", newline='') as menalari_patch:
    menaWriter = csv.writer(menalari_patch, delimiter='\t', lineterminator='\n')

    menalariReader = csv.reader(menalari_file, delimiter=',', quotechar='"')

    for row in menalariReader:
        for entry in row:
