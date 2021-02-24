import os
from zipfile import ZipFile

import yaml
from yaml import Loader, Dumper

import pickle as pickle

with open(r'config.yaml') as f:
  cfg = yaml.load(f, Loader=yaml.FullLoader)

def splitpath(path=''):
  results = []
  head = path
  while head != '':
    (head, tail) = os.path.split(head)
    results.append(tail)
  results.reverse()
  return results

invNames = None
stations = None
solarSystems = {}

gates = {}
with ZipFile(cfg['datasetname'],'r') as z:
  systemCount = 0
  for name in z.namelist():
    if name.startswith('sde/fsd/universe/eve/') and name.endswith('solarsystem.staticdata'):
      systemCount = systemCount + 1
  for name in z.namelist():
    path = splitpath(name)
    if path[1] == 'bsd':
      if path[-1] == 'invNames.yaml':
        # get id:name map
        print(name)
        invNames = {}
        with z.open(name) as f:
          # PyYAML eats a ton of memory. Keep it low by taking advantage of file structure and paging the data in.
          n = 50000
          i = 0
          chunk = []
          for j in f:
            chunk.append(j)
            if len(chunk) >= n:
              i = i + len(chunk)
              print(i)
              invNames.update({item['itemID']:item['itemName'] for item in yaml.load(b''.join(chunk).decode(), Loader=yaml.FullLoader)})
              chunk = []
          if len(chunk):
            i = i + len(chunk)
            print(i)
            invNames.update({item['itemID']:item['itemName'] for item in yaml.load(b''.join(chunk).decode(), Loader=yaml.FullLoader)})
          del chunk
      elif path[-1] == 'staStations.yaml':
        # get stations and their system, constellation, region, corp
        print(name)
        y = yaml.load(z.open(name), Loader=yaml.FullLoader)
        k = ('corporationID', 'solarSystemID', 'constellationID', 'regionID')
        stations = {item['stationID']:{kk:item[kk] for kk in k} for item in y if item['solarSystemID'] >= 30000000 and item['solarSystemID'] < 31000000}
        del y
    elif path[1] == 'fsd':
      if path[2] == 'universe':
        if path[3] == 'eve':
          if path[-1] == 'solarsystem.staticdata':
            # get jumps and security
            print(name, systemCount)
            systemCount = systemCount - 1
            y = yaml.load(z.open(name), Loader=yaml.FullLoader)
            if y['solarSystemID'] >= 30000000 and y['solarSystemID'] < 31000000:
              solarSystems[y['solarSystemID']] = {
                'rating': max(int(round(y['security']*10)),0),
                'jumps': [gate['destination'] for gate in y['stargates'].values()]
              }
              for k in y['stargates']:
                gates[k] = y['solarSystemID']
  # fix jumps so they point to solar systems rather than gates
  for k,v in solarSystems.items():
    v['jumps'] = [gates[jump] for jump in v['jumps'] if jump in gates]
  del gates

with open('solarSystems.pickle','wb') as f:
  pickle.dump(solarSystems, f)

with open('invNames.pickle','wb') as f:
  pickle.dump(invNames, f)
  
with open('staStations.pickle','wb') as f:
  pickle.dump(stations, f)
