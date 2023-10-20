#! /bin/env python3

import sys
import pandas as pd
import krippendorff

data = pd.read_csv(sys.argv[1], sep="\t")

print(data)


reordered_data = [
    data.annotator0.values,
    data.annotator1.values,
    data.annotator2.values,
]

agr = krippendorff.alpha(
    reliability_data=reordered_data, level_of_measurement="nominal"
)

print(f"Krippendorff alpha nominal agreement: {agr:0.3f}")
