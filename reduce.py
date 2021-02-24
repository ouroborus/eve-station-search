import os
from jinja2 import Environment,FileSystemLoader

import yaml
from yaml import CLoader as Loader, CDumper as Dumper

import pickle as pickle

with open(r'config.yaml', Loader=yaml.FullLoader)as f:
  cfg = yaml.load(f)

with open('solarSystems.pickle','rb') as f:
  solarSystems = pickle.load(f)

with open('invNames.pickle','rb') as f:
  invNames = pickle.load(f)

with open('staStations.pickle','rb') as f:
  stations = pickle.load(f)

corporations = {}
regions = {}

for k,v in list(stations.items()):
  if v['corporationID'] in corporations:
    corporations[v['corporationID']]['stations'].append(k)
  else:
    corporations[v['corporationID']] = {
      'stations': [k]
    }
  regions[v['regionID']] = {}
  solarSystems[v['solarSystemID']]['region'] = v['regionID']

stations = {k:{'name':invNames[k], 'corporation':v['corporationID'], 'solarSystem':v['solarSystemID']} for k,v in list(stations.items())}

for k,v in list(corporations.items()):
  v['name'] = invNames[k]

for k,v in list(regions.items()):
  v['name'] = invNames[k]

for k,v in list(solarSystems.items()):
  v['name'] = invNames[k]

del invNames

print('filtering...')

# remove generally inaccessible systems
# first system in database is known accessible so trace jumps from there to get accessibility map
qIn = set([sorted(solarSystems.keys())[0]])
qOut = set()
while(qIn):
  for ss in qIn:
    solarSystems[ss]['accessible'] = None
    for k in solarSystems[ss]['jumps']:
      if k in solarSystems and 'accessible' not in solarSystems[k]:
        qOut.add(k)
  qIn = qOut
  qOut = set()
del qIn
del qOut
for k in list(solarSystems.keys()):
  if 'accessible' in solarSystems[k]:
    del solarSystems[k]['accessible']
  else:
    print('removing solar system {} {}'.format(k,solarSystems[k]['name']))
    del solarSystems[k]
for v in solarSystems.values():
  v['jumps'] = [jump for jump in v['jumps'] if jump in solarSystems]

# remove inaccessible stations; populate corp station ownership; remove corp reference from station
for k in list(stations.keys()):
  if stations[k]['solarSystem'] in solarSystems:
    #corporations[stations[k]['corporation']]['stations'].append(k)
    del stations[k]['corporation']
  else:
    print('removing station {} {}'.format(k,stations[k]['name']))
    corporations[stations[k]['corporation']]['stations'].remove(k)
    del stations[k]

# remove corporations with no accessible stations
for k in list(corporations.keys()):
  if len(corporations[k]['stations']) != len(set(corporations[k]['stations'])):
    print('dup:', k)
    print(repr(sorted(corporations[k]['stations'])))
  corporations[k]['stations'] = [station for station in corporations[k]['stations'] if station in stations]
  if not corporations[k]['stations']:
    print('removing corporation {} {}'.format(k,corporations[k]['name']))
    del corporations[k]

# remove regions without stations
for ss in solarSystems.values():
  if 'region' in ss:
    regions[ss['region']]['accessible'] = None
for k in list(regions.keys()):
  if 'accessible' in regions[k]:
    del regions[k]['accessible']
  else:
    print('removing region {} {}'.format(k,regions[k]['name']))
    del regions[k]

# generate name-sorted index for corporations
corporationsSorted = sorted(list(corporations.keys()), key=lambda key:corporations[key]['name'].lower())

# generate name-sorted index for systems
solarSystemsSorted = sorted(list(solarSystems.keys()), key=lambda key:solarSystems[key]['name'].lower())

# generate data file
print('generating {}...'.format(cfg['python_filename']))
jenv = Environment(loader = FileSystemLoader('.'))
jenv.get_template(cfg['template_filename']).stream({
  'datasetname':repr(cfg['datasetname']),
  'corporations':repr(corporations),
  'regions':repr(regions),
  'stations':repr(stations),
  'solarSystems':repr(solarSystems),
  'corporationsSorted':repr(corporationsSorted),
  'solarSystemsSorted':repr(solarSystemsSorted)
}).dump(cfg['python_filename'])

print('done')
