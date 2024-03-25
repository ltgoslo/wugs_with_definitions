# Word Usage Graphs enriched with cluster definitions
This is a dataset of word usage graphs (WUGs), where the existing WUGs for multiple languages are enriched with cluster labels functioning as sense definitions. 
They are generated from scratch by fine-tuned encoder-decoder language models. 

See details in the paper "Enriching Word Usage Graphs with Cluster Definitions" (LREC-COLING'2024) by Mariia Fedorova, Andrey Kutuzov, Nikolay Arefyev and Dominik Schlechtweg.

We hope that the resulting enriched datasets can be helpful for moving on to explainable semantic change modeling.

## Contents
- `code/`: various scripts we used in preparing the datasets
- `human_evaluation/`: everything related to our evaluation efforts
- `wug_labels/`: the cluster labels themselves, the main part.

The cluster labels should be used together with the [original word usage graphs](https://www.ims.uni-stuttgart.de/en/research/resources/experiment-data/wugs/) for the corresponding languages.

## Definition generation models:
- English: [mT0-Definition-En XL](https://huggingface.co/ltg/mt0-definition-en-xl)
- Norwegian: [mT0-Definition-No XL](https://huggingface.co/ltg/mt0-definition-no-xl)
- Russian: [mT0-Definition-Ru XL](https://huggingface.co/ltg/mt0-definition-ru-xl)
