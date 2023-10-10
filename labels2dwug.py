import argparse
import os
from os import path
import pandas as pd
import csv

# Quick and dirty conversion of the original ACL'23 sense label maps
# to the LREC paper format

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=str,
        help="tsv file with labels",
    )
    parser.add_argument(
        "--output_path",
        required=True,
        type=str,
    )
    args = parser.parse_args()

    df = pd.read_csv(args.source, delimiter="\t", quoting=csv.QUOTE_NONE)

    cluster_labels = {}

    for _, row in df.iterrows():
        word = row.Targets + "_nn"
        cluster = int(row.Clusters)
        label = row.Definitions
        if word not in cluster_labels:
            cluster_labels[word] = {"cluster": [], "gloss": []}
        cluster_labels[word]["cluster"].append(cluster)
        cluster_labels[word]["gloss"].append(label)

    for target in cluster_labels:
        target_df = pd.DataFrame.from_dict(cluster_labels[target])
        target_directory = path.join(args.output_path, target)
        os.makedirs(target_directory)
        target_df.to_csv(path.join(target_directory, "cluster_gloss.tsv"), sep="\t",
                         quoting=csv.QUOTE_NONE, index=False)
    print(f"Saving to {args.output_path} done")
