from os import makedirs
from os.path import join, basename, dirname
from subprocess import CalledProcessError

from click import option, argument
from papermill import execute_notebook
from utz import err, sh

from benchmarks.cli.base import cli
from benchmarks.cli.dataset_slice import DatasetSlice
from benchmarks.data_loader.paths import NB_PATH, NB_DIR, DEFAULT_PQT_PATH


DEFAULT_MARKER_SIZE_ANCHOR = '65536=10'


@cli.command()
@option('-a', '--marker-size-anchor', help=f'String, of the form "<block_size>=<marker_size>" (default "{DEFAULT_MARKER_SIZE_ANCHOR}"); determines marker-size scaling vs. block_size')
@option('-A', '--no-default-marker-annotations', is_flag=True, help="Don't add default marker annotations to the plot")
@option('-D', '--dataset-slice', callback=lambda ctx, param, value: DatasetSlice.parse(value) if value else None, help="Filter to DB entries matching this URI")
@option('-h', '--hostname-rgx', help='Filter to DB entries matching this hostname regex')
@option('-i', '--instance-type', help='Optional: filter to DB entries run on this EC2 `instance_type`')
@option('-n', '--max-batches', type=int, default=0, help='Optional: filter to DB entries with this `max_batch` set')
@option('-o', '--out-dir', help='Directory (under -O/--out-root) to write the executed notebook – and associated plot data – to')
@option('-O', '--no-open', is_flag=True, help="Don't attempt to `open` the generated HTML plot")
@option('-r', '--out-root', default=NB_DIR, help=f'Output "root" directory, default: {NB_DIR}')
@option('-s', '--since', help="Filter to DB entries run since this datetime (inclusive)")
@option('--s3/--no-s3', is_flag=True, default=None, help="If set, filter to DB entries run against S3, or run locally")
@option('--annotation-text', help="Add a text annotation to the plot")
@option('--ann-offset', help="List passed to `utz.plots.title`; first elem is title, subsequent elems are subtitle lines")
@option('--ann-arrow-offset', help="Position text annotation relative to default markers' mean position; x-axis (max. memory usage) is log-scale, so is multiplied.")
@option('--ann-size', help="Pad the arrow start around each default marker; x-axis (max. memory usage) is log-scale, so is multiplied.")
@argument('db_path', default=DEFAULT_PQT_PATH)
def data_loader_nb(
        db_path,
        no_default_marker_annotations,
        marker_size_anchor,
        dataset_slice: DatasetSlice,
        hostname_rgx,
        instance_type,
        max_batches,
        out_dir: str,
        no_open,
        out_root,
        since,
        s3,
        annotation_text,
        ann_offset,
        ann_arrow_offset,
        ann_size,
):
    nb_path = NB_PATH
    if not out_dir:
        if dataset_slice:
            out_dir = f'{dataset_slice}'
            if max_batches:
                out_dir += f'_{max_batches}'
        else:
            raise ValueError('Must provide -o/--out-dir or -d/--dataset-slice')
    out_dir = join(out_root, out_dir)
    out_nb_path = join(out_dir, basename(nb_path))

    if s3 is True:
        uri_rgx = f'^s3://.*{dataset_slice}'
    elif s3 is False:
        uri_rgx = f'^data/.*{dataset_slice}'
    else:
        uri_rgx = None

    parameters = dict(
        db_path=db_path,
        marker_size_anchor=marker_size_anchor,
        hostname_rgx=hostname_rgx,
        instance_type=instance_type,
        out_dir=out_dir,
        show='png',
        max_batches=max_batches,
        since=since,
        sorted_datasets=dataset_slice.sorted_datasets,
        start_idx=dataset_slice.start,
        end_idx=dataset_slice.end,
        uri_rgx=uri_rgx,
        annotate_defaults=not no_default_marker_annotations,
    )
    if annotation_text: parameters['annotation_text'] = annotation_text
    if ann_offset: parameters['ann_offset'] = ann_offset
    if ann_arrow_offset: parameters['ann_arrow_offset'] = ann_arrow_offset
    if ann_size: parameters['ann_size'] = ann_size

    err(f"Running papermill: {nb_path} {out_nb_path}")
    err(f"{parameters=}")
    makedirs(dirname(out_nb_path), exist_ok=True)
    execute_notebook(
        nb_path,
        out_nb_path,
        parameters=parameters,
    )
    sh('juq', 'papermill-clean', '-i', out_nb_path)
    if not no_open:
        try:
            sh('open', join(out_dir, 'speed_vs_mem_1.html'))
        except CalledProcessError:
            pass
