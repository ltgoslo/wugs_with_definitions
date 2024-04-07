# Word Usage Graphs enriched with cluster definitions
This is a dataset of word usage graphs (WUGs), where the existing WUGs for multiple languages are enriched with cluster labels functioning as sense definitions. 
They are generated from scratch by fine-tuned encoder-decoder language models. 
The resulting enriched datasets can be helpful for explainable semantic change modeling.

## Contents
- [`code/`](https://github.com/ltgoslo/wugs_with_definitions/tree/main/code): various scripts we used in preparing the datasets
- [`human_evaluation/`](https://github.com/ltgoslo/wugs_with_definitions/tree/main/human_evaluation): everything related to our evaluation efforts
- [`wug_labels/`](https://github.com/ltgoslo/wugs_with_definitions/tree/main/wug_labels): the cluster labels themselves, the main part.

We provide [cluster labels (sense definitions)](https://github.com/ltgoslo/wugs_with_definitions/tree/main/wug_labels) for the following WUGs:

- [Diachronic WUGs for English](https://zenodo.org/record/5544443) - English definitions
- [Diachronic WUGs for German](https://zenodo.org/record/5543723) - German and English definitions
- [NorDiaChange: Diachronic semantic change dataset for Norwegian](https://github.com/ltgoslo/nor_dia_change) (two subsets) - Norwegian and English definitions
- [RuDSI: Word sense induction dataset for Russian](https://github.com/kategavrishina/RuDSI) - Russian and English definitions

### Format
Every WUG dataset in the [`wug_labels/`](https://github.com/ltgoslo/wugs_with_definitions/tree/main/wug_labels) directory contains target word subdirectories, according to the original DWUG format.
Within each target word directory, we provide one file named `cluster_gloss.tsv`. It is a tab-separated dataframe with two columns:

- `cluster`: the numerical identifier of the cluster from the original WUG
- `gloss`: the definition generated for this cluster

The cluster labels should be used together with the [original word usage graphs](https://www.ims.uni-stuttgart.de/en/research/resources/experiment-data/wugs/) for the corresponding languages.
As a rule, one can find clusters assigned to every specific WUG usage (sentence) in the `clusters/` directory.

NB: some clusters are too small to generate a meaningful definition (less than 3 usages). 
In these cases, the definition is accordingly "Too few examples to generate a proper definition!".

## Citation
See details in the paper "[Enriching Word Usage Graphs with Cluster Definitions](https://arxiv.org/abs/2403.18024)" (LREC-COLING'2024) by Mariia Fedorova, Andrey Kutuzov, Nikolay Arefyev and Dominik Schlechtweg.

## Definition generation models:
- English: [mT0-Definition-En XL](https://huggingface.co/ltg/mt0-definition-en-xl)
- Norwegian: [mT0-Definition-No XL](https://huggingface.co/ltg/mt0-definition-no-xl)
- Russian: [mT0-Definition-Ru XL](https://huggingface.co/ltg/mt0-definition-ru-xl)
