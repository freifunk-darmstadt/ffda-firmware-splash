from __future__ import print_function
from jinja2 import Environment, FileSystemLoader
from collections import defaultdict, OrderedDict
from itertools import groupby
from operator import itemgetter
import yaml
import os
import sys
from pprint import PrettyPrinter

prefix = 'gluon-ffda-'
branches = ['stable', 'beta', 'experimental']
types = ['sysupgrade', 'factory']

# load router models lookup table
models_file = open('models.yml', 'r')
models = yaml.load(models_file)
models_file.close()

# setup PrettyPrinter
pp = PrettyPrinter()


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
            for model, imageiter in groupby(sorted(self.data[branch]), key=itemgetter('model')):
                images = [image for image in imageiter]
                tmp[model] = {'vendor': images[0]['vendor'], 'model': images[0]['model']}
                # then group by image type
                for imgtype, typeiter in groupby(sorted(images, key=lambda x: x['type']), key=itemgetter('type')):
                    revisions = [rev for rev in typeiter]
                    tmp[model][imgtype] = revisions
            self.data[branch] = tmp

    def get(self):
        return self.data

# read available images
db = FirmwareInfoContainer()
versions = {}
for branch in branches:
    for image_type in types:
        for _, _, files in os.walk('./target/%s/%s' % (branch, image_type)):
            files = sorted(files)
            for image_file in files:
                # would be great if we could just parse the manifest, but we have it only for sysupgrades atm
                if image_file.endswith('manifest') or image_file.endswith("SUMS"):
                    continue

                # TODO: can we make this beautifulz and shiny? *_*
                version_margin = 0
                version = image_file.replace(prefix, '').split('-')[0]
                # TODO: dirty hack to support 0.6.0-[/d]* type versioning for experimental builds
                try:
                    release_date = int(image_file.split(version)[1].split('-')[1])
                    version = '%s-%s' % (version, release_date)
                except ValueError:
                    pass
                model = image_file.split('%s-' % version)[1].replace('-sysupgrade', '').replace('.bin', '').replace('.img', '')
                filename = image_file

                tmp = {'model': model, 'version': version, 'filename': filename}

                try:
                    tmp = dict(tmp.items() + models[model].items())
                except KeyError:
                    print("Missing ModelInfo for %s" % model, file=sys.stderr)
                    continue

                db.insert(branch, image_type, tmp['vendor'], tmp['model'], tmp['revision'], filename)
                versions[branch] = version

db.group()

#print json.dumps(db.get())

# templating
env = Environment()
env.loader = FileSystemLoader('templates')
template = env.get_template('template.html')

print(template.render(branches=branches, versions=versions, db=db.get()))
