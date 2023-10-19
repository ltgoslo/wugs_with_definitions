import argparse
from collections import defaultdict
from copy import copy
import csv
from glob import glob
import json
import logging
import os
import random

import pandas as pd

logging.basicConfig(level=logging.INFO)

CLUSTER_NUMBER_COLUMN = 'cluster'
EXAMPLE_COLUMN = 'context'
WORD_COLUMN = 'word'

parser = argparse.ArgumentParser(
    description='Prepare dataset for label studio',
)
parser.add_argument("--lang", default="en")
parser.add_argument(
    "--gloss_repo",
    default=os.path.expanduser("~/PycharmProjects/gloss-annotator"),
    help="path to the gloss-annotator repository"
)
parser.add_argument(
    "--out_path",
    default=os.path.expanduser("wugs/label_studio_data/"),
)

METHODS = {
    "en": (
        "glossreader_v1",
        "mt0-definition-en-xl",
        "lesk",
    ),
    "en_test": (
        "pilot_glmlarge_wordnet_l1norm_top3",
        "pilot_flan-t5-definition-en-xl",
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
    )
}
DWUGS = {
    "en": "dwug_en",
    "de": "dwug_de",
    "no1": "nor_dia_change/subset1",
    "no2": "nor_dia_change/subset2",
    "ru": "RuDSIfixed",
}


def sample_random_uses(
        this_cluster,
        cluster_number,
        clusters_list,
        uses_list,
):
    """
    Sample random uses for a cluster
    :param this_cluster: rows from joined dwug table for the current cluster
    :param cluster_number: current cluster number
    :param clusters_list: list of cluster numbers
    :param uses_list: list of uses for each cluster
    :return: list of cluster numbers, list of uses for each cluster
    """
    if this_cluster.shape[0] > 2:
        choiced_contexts_ids = random.sample(
            [i for i in range(this_cluster.shape[0])],
            k=min(this_cluster.shape[0], 5),
        )
        contexts = []
        for id_ in choiced_contexts_ids:
            row = this_cluster.iloc[id_]
            start, end = row["indexes_target_token"].split(":")
            start, end = int(start), int(end)
            example = row[EXAMPLE_COLUMN]
            contexts.append(
                f"- {example[:start]}<b>{example[start:end]}</b>{example[end:]}",
            )
        clusters_list.append(cluster_number)
        uses_list.append('<br>'.join(contexts) + "<hr>")
    return clusters_list, uses_list


def join_dwug_tables(
        dwug_path,
        word,
        clusters_minus_1,
        joined_dwug_tables_dict,
):
    """
    Join dwug uses and clusters tables, remove -1
    :param dwug_path: path to the dwug folder
    :param word: the word in dwug
    :param clusters_minus_1: number of clusters labeled -1
    :param joined_dwug_tables_dict: dict to save joined tables
    :return: number of clusters labeled -1, dict of joined tables by word
    """
    try:
        word_uses = pd.read_csv(
            os.path.join(dwug_path, "data", word, "uses.csv"), sep="\t",
            quoting=csv.QUOTE_NONE,
        )
    except FileNotFoundError:
        word_uses = pd.read_csv(
            os.path.join(dwug_path, "data", word, "uses.tsv"), sep="\t",
            quoting=csv.QUOTE_NONE,
        )

    clusters_dir = os.path.join(dwug_path, "clusters/opt")
    if not os.path.exists(clusters_dir):  # no opt in RuDSI data
        clusters_dir = os.path.join(dwug_path, "clusters")
    try:
        word_clusters = pd.read_csv(
            os.path.join(clusters_dir, f"{word}.csv"),
            sep="\t",
            quoting=csv.QUOTE_NONE,
        )
    except FileNotFoundError:
        word_clusters = pd.read_csv(
            os.path.join(clusters_dir, f"{word}.tsv"),
            sep="\t",
            quoting=csv.QUOTE_NONE,
        )

    word_clusters.dropna(inplace=True)
    word_clusters = word_uses.join(
        word_clusters.set_index("identifier"), on="identifier",
    )
    if "Ru" in dwug_path:
        word_clusters.dropna(subset=[CLUSTER_NUMBER_COLUMN], inplace=True)  # nan in clusters appears after join in RuDSI

    word_clusters[CLUSTER_NUMBER_COLUMN] = word_clusters[
        CLUSTER_NUMBER_COLUMN
    ].astype(int).astype(str) # to int because of nans in Ru

    clusters_minus_1 += word_clusters[
        word_clusters[CLUSTER_NUMBER_COLUMN] == "-1"
        ].shape[0]
    word_clusters = word_clusters[
        word_clusters[CLUSTER_NUMBER_COLUMN] != "-1"
        ]
    joined_dwug_tables_dict[word] = word_clusters
    return clusters_minus_1, joined_dwug_tables_dict


def get_random_uses(
        word_clusters_with_uses,
        two_use_cluster,
        one_use_clusters,
        one_clusters,
        mapping_dir,
        word,
):
    """
    Select random another cluster for each cluster and get random uses for it
    :param word_clusters_with_uses: joined dwug tables for the current word
    :param two_use_cluster: how many clusters has 2 uses only
    :param one_use_clusters: how many clusters has 1 uses only
    :param one_clusters: how many senses has 1 cluster only
    :return: stats of clusters and uses, dict of random uses by clusters
    """
    random_uses = {}
    clusters_list, contexts_list_html = [], []
    wrong_clusters_list = []
    unique_clusters = word_clusters_with_uses[
        CLUSTER_NUMBER_COLUMN
    ].unique().tolist()
    for cluster_number in unique_clusters:
        this_cluster = word_clusters_with_uses[
            word_clusters_with_uses[CLUSTER_NUMBER_COLUMN] == cluster_number
            ]
        if this_cluster.shape[0] == 2:
            two_use_cluster += 1
        if this_cluster.shape[0] == 1:
            one_use_clusters += 1
        clusters_list, contexts_list_html = sample_random_uses(
            this_cluster,
            cluster_number,
            clusters_list,
            contexts_list_html,
        )
    contexts_df = pd.DataFrame(
        {
            CLUSTER_NUMBER_COLUMN: clusters_list,
            EXAMPLE_COLUMN: contexts_list_html,
        },
    )
    if contexts_df.shape[0] > 1:
        clusters_list = list(set(clusters_list))
        for cluster_number in clusters_list:  # < 2 uses removed
            not_this_cluster = contexts_df[
                contexts_df[CLUSTER_NUMBER_COLUMN] != cluster_number
                ]
            this_cluster_uses = contexts_df[
                contexts_df[CLUSTER_NUMBER_COLUMN] == cluster_number
                ]
            not_this_cluster_sample = not_this_cluster.sample(
                n=1,
            ).iloc[0]
            this_cluster_sample = this_cluster_uses.sample(
                n=1,
            ).iloc[0]
            wrong_clusters_list.append(
                not_this_cluster_sample[CLUSTER_NUMBER_COLUMN],
            )
            random_uses[cluster_number] = [
                {
                    "value": str(not_this_cluster_sample[CLUSTER_NUMBER_COLUMN]),
                    "html": not_this_cluster_sample[EXAMPLE_COLUMN],
                },
                {
                    "value": str(cluster_number),
                    "html": this_cluster_sample[EXAMPLE_COLUMN],
                }
            ]
        mapping_df = pd.DataFrame(
            {
                CLUSTER_NUMBER_COLUMN: clusters_list,
                "wrong_cluster": wrong_clusters_list,
            },
        )
        mapping_df.to_csv(
            f"{mapping_dir}/{word}.tsv",
            sep="\t",
            index=False,
        )
    else:
        one_clusters += 1

    return two_use_cluster, one_use_clusters, one_clusters, random_uses


def get_word_clusters(predictions_folder, args):
    """
    Join uses and clusters tables from a dwug
    :param predictions_folder: path to the folder with predictions by word
    :param args: command line args
    :return: dict of joined dwug tables by word, dict of random uses by word
    """
    lang = args.lang.split("_")[0]
    dwug_path = os.path.expanduser(
        f"{args.gloss_repo}/wugs/{DWUGS[lang]}/",
    )
    # track how many samples are removed and why
    clusters_minus_1, one_use_clusters, two_use_cluster = 0, 0, 0
    one_clusters = 0

    random_uses_path = os.path.join(
        os.path.expanduser(args.out_path),
        "random_uses",
        f"random_uses-{lang}.json"
    )
    mapping_dir = os.path.join(args.out_path, f"mappings/{lang}")
    if not os.path.exists(mapping_dir):
        os.mkdir(mapping_dir)
    joined_dwug_tables_dict, random_uses_dict = {}, {}
    for word_path in glob(predictions_folder):
        word = os.path.split(word_path)[-1]
        clusters_minus_1, joined_dwug_tables_dict = join_dwug_tables(
            dwug_path,
            word,
            clusters_minus_1,
            joined_dwug_tables_dict,
        )
        if not os.path.exists(random_uses_path):
            word_clusters_with_uses = joined_dwug_tables_dict[word]
            two_use_cluster, one_use_clusters, one_clusters, random_uses = get_random_uses(
                word_clusters_with_uses,
                two_use_cluster,
                one_use_clusters,
                one_clusters,
                mapping_dir,
                word,
            )
            random_uses_dict[word] = random_uses

    if not os.path.exists(random_uses_path):
        with open(random_uses_path, "w", encoding="utf8") as f:
            json.dump(random_uses_dict, f)
    else:
        with open(random_uses_path, "r", encoding="utf8") as f:
            random_uses_dict = json.load(f)
    logging.info(f"Number of clusters labeled with -1: {clusters_minus_1}")
    logging.info(f"Number of singleton clusters: {one_use_clusters}")
    logging.info(f"Number of clusters with two uses: {two_use_cluster}")
    logging.info(
        f"Number of words where one cluster only remained after removing singletons, -1: {one_clusters}",
    )
    return joined_dwug_tables_dict, random_uses_dict


def check_common_definitions_for_different_words(
        definition,
        all_definitions,
        all_definitions_by_word,
        word,
        predictions_folder,
):
    if definition != "Too few examples to generate a proper definition!":
        if definition not in all_definitions:
            all_definitions.add(definition)
            all_definitions_by_word[word].add(definition)
        else:
            words = [word]
            for word_key, word_definitions in all_definitions_by_word.items():
                if (word_key != word) and (definition in word_definitions):
                    words.append(word_key)

            if len(words) > 1:
                logging.info(
                    f"Common definition {definition} for words {words} by {predictions_folder}",
                )
    return all_definitions, all_definitions_by_word


def get_definitions_predicted_for_cluster(
        clusters_and_definitions,
        all_definitions,
        all_definitions_by_word,
        word,
        predictions_folder,
        random_use,
):
    definitions, clusters_list, contexts_html_list, contexts_list = [], [], [], []
    for row in clusters_and_definitions.iterrows():
        cluster_number, definition = row[1]

        all_definitions, all_definitions_by_word = check_common_definitions_for_different_words(
            definition,
            all_definitions,
            all_definitions_by_word,
            word,
            predictions_folder,
        )
        cluster_number = str(cluster_number)
        if random_use.get(cluster_number) is not None:
            definitions.append(definition)
            contexts_html_list.append(random_use[cluster_number])
    return definitions, contexts_html_list


def convert_to_label_studio_format(
        definitions,
        contexts_html_list,
        other_methods_word_definitions,
        word,
        label_data,
        word_definitions_dict,
):
    seen_definitions = []
    for definition, contexts in zip(
            definitions,
            contexts_html_list,
    ):
        if (definition not in seen_definitions) and (
                definition not in other_methods_word_definitions
        ):
            seen_definitions.append(definition)
            cluster_data = {}
            cluster_data["data"] = {
                "my_text": f"{word.upper()}: <b>{definition.upper()}</b>"
            }

            cluster_data["data"]["variants"] = copy(contexts)
            random.shuffle(cluster_data["data"]["variants"])
            cluster_data["data"]["variants"].extend(
                [
                    {"value": "-2",
                     "html": '<b>This definition describes none of the clusters</b><hr>'},
                    {"value": "-3",
                     "html": '<b>This definition fits both clusters</b><hr>'},
                ],
            )
            assert len(cluster_data["data"]["variants"]) == 4
            label_data.append(cluster_data)
    word_definitions_dict[word].append(set(seen_definitions))
    return label_data, word_definitions_dict


def pass_folder(
        predictions_folder: str,
        label_data: list,
        joined_dwug_tables_dict: dict,
        word_definitions_dict: dict,
        random_uses_dict: dict,
):
    """
    Collects predictions from a system's folder
    :param predictions_folder: path to a system's prediction folder
    :param label_data: resulting data in label studio format
    :param joined_dwug_tables_dict: dict of joined dwug tables by word
    :param word_definitions_dict: dict to track if other systems generated
        the same definition for the same word
    :return: data to markup updated with predictions from this system,

    """
    # track if the same definitions were generated for different words
    all_definitions, all_definitions_by_word = set(), defaultdict(set)
    for word_path in glob(predictions_folder):
        word = os.path.split(word_path)[-1]

        # track if other systems generated the same definition for
        # the same word to avoid repetitive annotation tasks
        other_methods_word_definitions = set()
        for definitions_set in word_definitions_dict[word]:
            other_methods_word_definitions = other_methods_word_definitions.union(
                definitions_set,
            )

        predicted_definitions = pd.read_csv(
            os.path.join(word_path, "cluster_gloss.tsv"),
            sep="\t",
        )
        predicted_definitions[CLUSTER_NUMBER_COLUMN] = \
            predicted_definitions.cluster.astype(str)
        predicted_definitions = predicted_definitions[
            predicted_definitions.cluster != "-1"]

        if predicted_definitions.shape[0] > 1:
            random_use = random_uses_dict.get(word)
            if (random_use is not None) and random_use:
                definitions, contexts_html_list = get_definitions_predicted_for_cluster(
                    predicted_definitions,
                    all_definitions,
                    all_definitions_by_word,
                    word,
                    predictions_folder,
                    random_use,
                )
                label_data, word_definitions_dict = convert_to_label_studio_format(
                    definitions,
                    contexts_html_list,
                    other_methods_word_definitions,
                    word,
                    label_data,
                    word_definitions_dict
                )
    return label_data, word_definitions_dict


def main():
    label_data = []
    args = parser.parse_args()
    predictions_folder = os.path.join(args.gloss_repo, "predictions")
    lang = args.lang.split("_")[0]
    joined_dwug_tables_dict, random_uses_dict = get_word_clusters(
        os.path.join(
            predictions_folder,
            f"{METHODS[args.lang][0]}/dwug_{lang}/*",
        ),
        args,
    )
    word_definitions_dict = defaultdict(list)

    for method in METHODS[args.lang]:
        label_data, word_definitions_dict = pass_folder(
            os.path.join(
                predictions_folder,
                f"{method}/dwug_{lang}/*",
            ),
            label_data,
            joined_dwug_tables_dict,
            word_definitions_dict,
            random_uses_dict,
        )

    logging.info(f"{len(label_data)} examples to annotate in total")
    random.shuffle(label_data)
    if not os.path.exists(args.out_path):
        os.mkdir(args.out_path)
    with open(
            os.path.expanduser(
                f"{args.out_path}/label-studio-{args.lang}.json"),
            "w",
            encoding="utf8",
    ) as f:
        json.dump(label_data, f)
    with open(
            os.path.expanduser(
                f"{args.out_path}/label-studio-{args.lang}-test.json"),
            "w",
            encoding="utf8",
    ) as f:
        json.dump(label_data[:15], f)


if __name__ == '__main__':
    main()
