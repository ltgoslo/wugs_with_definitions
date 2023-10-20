import argparse
from collections import defaultdict
import json
import logging
import os

import pandas as pd

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
    correct_answers = defaultdict(list)
    both = defaultdict(int)
    none = defaultdict(int)
    lang = args.lang.split("_")[0]
    gloss_repo = args.gloss_repo
    predictions_folder = os.path.join(gloss_repo, "predictions")
    for sample in annotations:
        # TODO don't uppercase my_text
        word = sample["data"]["my_text"].split(": ")[0].lower()
        gloss = sample["data"]["my_text"][len(word) + 2:].replace("<b>",
                                                                  "").replace(
            "</b>", "")
        methods_with_this_gloss, clusters_pred = [], []
        for method in METHODS[args.lang]:
            predictions_path = os.path.join(predictions_folder,
                                            f"{method}/dwug_{lang}/{word}/cluster_gloss.tsv")
            if not os.path.exists(predictions_path):
                word = word[0].upper() + word[1:]
                word = WORDS_MAPPING.get(word, word)
                predictions_path = os.path.join(predictions_folder,
                                                f"{method}/dwug_{lang}/{word}/cluster_gloss.tsv")
            clusters_and_definitions = pd.read_csv(predictions_path, sep="\t")
            clusters_and_definitions[CLUSTER_NUMBER_COLUMN] = \
                clusters_and_definitions[CLUSTER_NUMBER_COLUMN].astype(str)
            clusters_and_definitions = clusters_and_definitions[
                clusters_and_definitions[CLUSTER_NUMBER_COLUMN] != "-1"]

            cluster_pred = clusters_and_definitions[
                clusters_and_definitions.gloss.str.lower() == gloss.lower()
                ]
            if cluster_pred.shape[0] > 0:
                methods_with_this_gloss.append(method)
                clusters_pred.append(
                    cluster_pred[
                        CLUSTER_NUMBER_COLUMN].unique().tolist())  # TODO assert without unique

        sample_annotations = sample['annotations']
        for annotation in sample_annotations:
            cluster_true = annotation['result'][0]["value"]["choices"][0]
            for method, clusters in zip(methods_with_this_gloss,
                                        clusters_pred):
                logging.info(method)
                logging.info(cluster_true)
                logging.info(clusters)
                number_of_clusters_predicted = len(clusters)
                correct_answers[method].append(
                    int(cluster_true in clusters) / number_of_clusters_predicted,
                )
                if cluster_true == "-3":
                    both[method] += 1
                elif cluster_true == "-2":
                    none[method] += 1

    for method, v in correct_answers.items():
        number_of_annotations = len(v)
        accuracy = sum(v) / number_of_annotations
        logging.info(
            f"Accuracy {method}: {round(accuracy * 100, 2)} on {number_of_annotations} annotations",
        )
        none_metric = round((none[method] / number_of_annotations) * 100, 2)
        logging.info(
            f"{method}, definitions that describe none of the clusters {none_metric}")
        both_metric = round((both[method] / number_of_annotations) * 100, 2)
        logging.info(
            f"{method}, definitions that describe both clusters {both_metric}")


if __name__ == '__main__':
    main()
