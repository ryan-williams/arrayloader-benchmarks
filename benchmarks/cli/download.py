from subprocess import check_output

import cellxgene_census
from click import option
from utz import err

from benchmarks import COLLECTION_ID
from benchmarks.census import download_datasets, get_dataset_ids
from benchmarks.cli.base import cli


DEFAULT_OUT_ROOT = "data"


@cli.command()
@option('-c', '--collection-id', default=COLLECTION_ID, help=f"Census collection ID to slice datasets from; default: {COLLECTION_ID}")
@option('-d', '--out-root', default=DEFAULT_OUT_ROOT, help=f"Directory to save sliced data into; default: {DEFAULT_OUT_ROOT}")
@option('-e', '--end', default=7, help='Slice datasets from `collection_id` ending at this index')
@option('-f', '--force', is_flag=True, help='rm existing out_dir before writing')
@option('-n', '--out-dir-name', 'out_dir', help="Basename under -d/--out-root to save sliced subset to; default: `census-benchmark_{start}:{end}`")
@option('-s', '--start', default=2, help='Slice datasets from `collection_id` starting from this index')
@option('-u', '--census-uri', help="Optional Census URI override, default is determined by -V/--census-version")
@option('-v', '--n-vars', default=20_000, help='Slice the first `n_vars` vars')
@option('-V', '--census-version', default="2023-12-15")
def download(collection_id, out_root, force, end, out_dir, start, census_uri, n_vars, census_version):
    """Slice and export cellxgene-census datasets to a local directory."""
    if out_dir is None:
        suffix = "" if start is None and end is None else f"_{start or ''}:{end or ''}"
        out_dir = f'{out_root}/census-benchmark{suffix}'
    else:
        out_dir = f"{out_root}/{out_dir}"
        err(f"Downloading to {out_dir}")

    census = cellxgene_census.open_soma(uri=census_uri, census_version=census_version)
    dataset_ids = get_dataset_ids(census, collection_id)
    print(f'Found {len(dataset_ids)} total datasets: {dataset_ids[:10]}')
    experiment = census["census_data"]["homo_sapiens"]
    download_datasets(experiment, dataset_ids, out_dir, start=start, end=end, n_vars=n_vars, rm=force)
    h_size = check_output(['du', '-sh', out_dir]).decode().split('\t')[0]
    print(f"{out_dir}: {h_size}")
