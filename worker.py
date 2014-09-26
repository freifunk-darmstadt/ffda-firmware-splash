from jinja2 import Environment, FileSystemLoader
from collections import defaultdict, OrderedDict
from itertools import groupby
from operator import itemgetter
import json
import os
import sys
from pprint import PrettyPrinter

prefix = 'gluon-ffda-'
branches = ['stable', 'beta', 'experimental']
types = ['sysupgrade', 'factory']

# load router models lookup table
models_file = open('models.json', 'r')
models = json.load(models_file)
models_file.close()


pp = PrettyPrinter()

# setup data foo
class DataFoo(object):
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
db = DataFoo()
for branch in branches:
    for image_type in types:
        for _, _, files in os.walk('./target/%s/%s' % (branch, image_type)):
            files = sorted(files)
            for image_file in files:
                # would be great if we could just parse the manifest, but we have it only for sysupgrades atm
                if image_file.endswith('manifest'):
                    continue

                # TODO: can we make this beautifulz and shiny? *_*
                version = image_file.replace(prefix, '').split('-')[0]
                model = image_file.split('%s-' % version)[1].replace('-sysupgrade.bin', '').replace('.bin', '')
                filename = image_file

                tmp = {'model': model, 'version': version, 'filename': filename}

                try:
                    tmp = dict(tmp.items() + models[model].items())
                except KeyError:
                    print("Missing ModelInfo for %s" % model)
                    continue

                db.insert(branch, image_type, tmp['vendor'], tmp['model'], tmp['revision'], filename)

db.group()

#print json.dumps(db.get())

# templating
env = Environment()
env.loader = FileSystemLoader('templates')
template = env.get_template('template.html')

print(template.render(branches=branches, db=db.get()))
