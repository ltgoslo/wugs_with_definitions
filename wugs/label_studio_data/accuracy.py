import argparse
from collections import Counter
import json
import logging
import os

import pandas as pd
from sklearn.metrics import accuracy_score

logging.basicConfig(level=logging.INFO)
METHODS = {
    "en": (
        "glossreader_v1",
        "mt0-definition-en-xl",
        "lesk",
    ),
    "de": (
        "mt0-definition-en-xl",
        "glossreader_v1",
    ),
    "no1": (
        "mt0-definition-no-xl",
    ),
    "no2": (
        "mt0-definition-no-xl",
    ),
    "ru_ru": (
        "mt0-definition-ru-xl",
    ),
}
CLUSTER_NUMBER_COLUMN = 'cluster'
DWUGS = {
    "en": "dwug_en",
    "de": "dwug_de",
    "no1": "nor_dia_change/subset1",
    "no2": "nor_dia_change/subset2",
    "ru": "RuDSIfixed",
}
WORDS_MAPPING = {
    "Engpass": "Engpaß",
    "Fuss": "Fuß",
    "Missklang": "Mißklang",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Count accuracy for enriching wugs gold data',
    )
    parser.add_argument(
        "--input_path",
        help="path to an exported label studio project",
    )
    parser.add_argument(
        "--lang",
        help="languages",
        choices=("en", "de", "no1", "no2", "ru_ru")
    )
    parser.add_argument(
        "--gloss_repo",
        default=os.path.expanduser("~/PycharmProjects/gloss-annotator"),
        help="path to the gloss-annotator repository"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    annotations_path = os.path.expanduser(args.input_path)
    with open(annotations_path, "r", encoding="utf8") as f:
        annotations = json.load(f)
    lang = args.lang.split("_")[0]
    gloss_repo = args.gloss_repo
    predictions_folder = os.path.join(gloss_repo, "predictions")
    annotations_dict = {}
    for sample in annotations:
        # TODO don't uppercase my_text
        word_gloss = sample["data"]["my_text"]
        cluster_1 = sample["data"]["variants"][0]["value"]
        cluster_2 = sample["data"]["variants"][1]["value"]

        sample_annotations = sample['annotations']
        for annotation in sample_annotations:
            cluster_true = annotation['result'][0]["value"]["choices"][0]
            annotations_dict[(word_gloss, cluster_1, cluster_2)] = cluster_true

    for method in METHODS[args.lang]:
        y_true, y_pred = [], []
        for word in os.listdir(os.path.join(predictions_folder,
                                        f"{method}/dwug_{lang}")):
            predictions_path = os.path.join(predictions_folder,
                                        f"{method}/dwug_{lang}/{word}/cluster_gloss.tsv")

            mapping_path = os.path.join(gloss_repo, f"wugs/label_studio_data/mappings/{lang}/{word}.tsv")
            try:
                mapping = pd.read_csv(mapping_path, sep="\t").astype(str)
            except FileNotFoundError:  # no annotation for this word e.g. if all its clusters are -1 etc.
                continue
            clusters_and_definitions = pd.read_csv(predictions_path, sep="\t")
            clusters_and_definitions[CLUSTER_NUMBER_COLUMN] = \
                clusters_and_definitions[CLUSTER_NUMBER_COLUMN].astype(str)
            clusters_and_definitions = clusters_and_definitions[
                clusters_and_definitions[CLUSTER_NUMBER_COLUMN] != "-1"]

            for row in clusters_and_definitions.iterrows():
                cluster_1, definition = row[1][CLUSTER_NUMBER_COLUMN], row[1]["gloss"]
                word_gloss = f"{word.upper()}: <b>{definition.upper()}</b>"
                cluster_2 = mapping[mapping[CLUSTER_NUMBER_COLUMN] == cluster_1]["wrong_cluster"]
                if cluster_2.shape[0]:  # maybe cluster with < 3 usages
                    cluster_2 = cluster_2.iloc[0]
                else:
                    continue
                cluster_true = annotations_dict.get((word_gloss, cluster_1, cluster_2))
                if cluster_true is None:
                    cluster_true = annotations_dict.get(
                        (word_gloss, cluster_2, cluster_1))
                y_true.append(cluster_true)
                y_pred.append(cluster_1)
        accuracy = accuracy_score(y_true, y_pred)
        logging.info(f"{len(y_true)} clusters")
        logging.info(
            f"Accuracy {method}: {round(accuracy * 100, 2)}",
        )
        answers_counter = Counter(y_true)
        none_metric = round((answers_counter["-2"] / len(y_true)) * 100, 2)
        logging.info(
            f"{method}, definitions that describe none of the clusters {none_metric}")
        both_metric = round((answers_counter["-3"] / len(y_true)) * 100, 2)
        logging.info(
            f"{method}, definitions that describe both clusters {both_metric}")


if __name__ == '__main__':
    main()
