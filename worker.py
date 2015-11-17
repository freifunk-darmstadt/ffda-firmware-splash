#!/usr/bin/env python2
from __future__ import print_function
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict, OrderedDict
from itertools import groupby
from operator import itemgetter
import yaml
import os
import sys
import re

prefix = 'gluon-ffda-'
branches = ['stable', 'beta', 'experimental']
types = ['sysupgrade', 'factory']

# load router models lookup table
models_file = open('models.yml', 'r')
models = yaml.load(models_file)
models_file.close()


def natural_sort(list, key=lambda s:s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
            convert = lambda text: int(text) if text.isdigit() else text
            return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    list.sort(key=sort_key)

# setup data foo
class FirmwareInfoContainer(object):
    def __init__(self):
        # create nested defaultdict
        self.data = defaultdict(lambda: list())

    def insert(self, branch, type, vendor, model, revision, filename):
        self.data[branch].append({'type': type, 'vendor': vendor, 'model': model, 'revision': revision, 'filename': filename})

    def group(self):
        for branch in self.data:
            # first group by model
            tmp = OrderedDict()
            for model, imageiter in groupby(sorted(self.data[branch], key=itemgetter('vendor', 'model')), key=itemgetter('model')):
                images = [image for image in imageiter]
                tmp[model] = {'vendor': images[0]['vendor'], 'model': images[0]['model']}
                # then group by image type
                for imgtype, typeiter in groupby(sorted(images, key=lambda x: x['type']), key=itemgetter('type')):
                    revisions = [rev for rev in typeiter]
                    natural_sort(revisions, key=lambda x: x['revision'])
                    tmp[model][imgtype] = revisions
            self.data[branch] = tmp

    def get(self):
        return self.data

# read available images
db = FirmwareInfoContainer()
versions = {}

# pattern to parse version, model, extension from filename
fn_pattern = re.compile("%s(?P<version>[\d.]+-?(\d*))-(?P<model>[a-z0-9-+\.]+)?\.[a-z]{3}" % prefix)

for branch in branches:
    for image_type in types:
        for _, _, files in os.walk('./target/%s/%s' % (branch, image_type)):
            files = sorted(files)
            for image_file in files:
                # would be great if we could just parse the manifest, but we have it only for sysupgrades atm
                if image_file.endswith('manifest') or image_file.endswith("SUMS"):
                    continue

                # parse info from filename
                try:
                    file_info = fn_pattern.match(image_file)

                    version = file_info.group('version')
                    model = file_info.group('model').replace('-sysupgrade', '')
                except AttributeError:
                    print("error parsing filename %s" % image_file)
                    continue

                # match info with data from models.yaml
                try:
                    model_info = models[model]
                except KeyError:
                    print("models.yaml: no model info for %s from %s" % (model, image_file), file=sys.stderr)
                    continue

                db.insert(branch, image_type, model_info['vendor'],
                          model_info['model'], model_info['revision'], image_file)
                versions[branch] = version

db.group()

# templating
env = Environment()
env.loader = FileSystemLoader('templates')
template = env.get_template('template.html')

print(template.render(branches=branches, versions=versions, db=db.get()))
