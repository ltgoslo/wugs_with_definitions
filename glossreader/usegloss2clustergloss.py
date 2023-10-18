import fire
import pandas as pd
import os
from pathlib import Path
from typing import Literal
import csv


def load_glossreader_preds(fpreds):
    df = pd.concat([pd.read_json(p) for p in Path('./').glob(fpreds)],
                   ignore_index=True)

    df = df.explode('glosses', ignore_index=True)  # convert a list of topk glosses into topk rows
    df = pd.concat([df.drop(columns=['glosses']),
                    pd.json_normalize(df.glosses)], axis=1)  # glosses column -> synset/gloss/similarity columns

    df['rank'] = df.groupby('id').similarity.rank(method='first', ascending=False)
    df['reciprocal_rank'] = 1. / df['rank']
    df['synset_gloss'] = df.synset + ' ' + df.gloss
    return df


def load_clusters(ds):
    cdf = pd.concat([pd.read_csv(p, sep='\t') for p in Path(f'./wugs/{ds}').glob('clusters/opt/*.csv')],
                    ignore_index=True)
    return cdf


def predict(preds_root, ds, topk, prediction: Literal['synset_gloss', 'gloss'],
            by: Literal['similarity', 'reciprocal_rank', 'count']):

    fpreds = f'{preds_root}/{ds}/*/glosses_uses_*.json'
    fpaths = list(Path('./').glob(fpreds))
    if len(fpaths) == 0:
        print('No files found matching the pattern:', fpreds)
        exit(1)
    ftypes = {p.name for p in fpaths}

    for ftype in ftypes:
        fpreds = f'{preds_root}/{ds}/*/{ftype}'
        df = load_glossreader_preds(fpreds)
        cdf = load_clusters(ds)
        mdf = df.merge(cdf, left_on='id', right_on='identifier', how='right').drop(columns=['identifier'])
        assert mdf.gloss.isnull().sum() == 0, 'For some uses no glosses were found in the predictions'

        gdf = mdf[mdf['rank'] <= topk].groupby(['lemma', 'cluster'])
        if by == 'count':
            rdf = gdf.apply(lambda r: r.groupby(prediction).agg({'id': 'nunique'}).idxmax()).rename(
                columns={'id': 'gloss'}).reset_index()
        else:
            rdf = gdf.apply(lambda r: r.groupby(prediction).agg({by: 'sum'}).idxmax()).rename(
                columns={by: 'gloss'}).reset_index()

        for w in rdf.lemma.unique():
            outpath = fpreds.replace('*', w)
            split = outpath.split('/')
            outpath = os.path.join(split[0], f'clusterglosses-topk_{topk}-by_{by}-predction_{prediction}', split[-1].replace('.json', ''), *split[1:-1], 'cluster_gloss.tsv')
            print(outpath)
            outpath = Path(outpath)
            outpath.parent.mkdir(parents=True, exist_ok=True)
            rdf[rdf.lemma == w].drop(columns=['lemma']).to_csv(outpath, index=False, sep='\t')


fire.Fire(predict)
