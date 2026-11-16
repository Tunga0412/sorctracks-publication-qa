"""Package only the aggregate and minimal isolated-rehearsal landing files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from public_data_reader import FIVE,public_constant

PUBLIC_FILES=('index.html','sorctracks_tool.html','robots.txt')

def package(source,destination):
    source=source.resolve();destination=destination.absolute()
    if destination.exists() or destination.resolve().is_relative_to(source):
        raise ValueError('Artifact must be a new directory outside the source')
    if (source/'CNAME').exists():
        raise ValueError('Rehearsal must not bind a custom domain')
    raw={}
    for name in PUBLIC_FILES:
        path=source/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Public input is missing or not a regular file')
        raw[name]=path.read_bytes()
    html=raw['sorctracks_tool.html']
    if not 1<=len(html)<=16*1024*1024:
        raise ValueError('Historical aggregate size is outside bound')
    text=html.decode('utf-8')
    for key in FIVE:
        if type(public_constant(text,key)) is not dict:
            raise ValueError('Invalid aggregate object')
    if b'Isolated publication rehearsal' not in raw['index.html']:
        raise ValueError('Rehearsal label is missing')
    if raw['robots.txt']!=b'User-agent: *\nDisallow: /\n':
        raise ValueError('Rehearsal search exclusion differs')
    # Every check precedes creation of the deployment artifact. Never upload
    # the checkout, automation, workflows or other files discovered at runtime.
    destination.mkdir()
    for name,body in raw.items():
        (destination/name).write_bytes(body)
        if (destination/name).read_bytes()!=body:
            raise ValueError('Artifact changed public bytes')
    if set(p.name for p in destination.iterdir())!=set(PUBLIC_FILES):
        raise ValueError('Unexpected artifact member')
    return {'aggregate_sha256':hashlib.sha256(html).hexdigest(),
            'aggregate_bytes':len(html),'artifact_files':list(PUBLIC_FILES),
            'scope':'PUBLIC_STRUCTURE_AND_EXACT_BYTES_NOT_SOURCE_ACCURACY'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(package(args.source,args.output),sort_keys=True))
