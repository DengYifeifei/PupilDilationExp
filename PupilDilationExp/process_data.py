import os
import sys
import json
import pandas as pd
import subprocess

from config import VERSION
wid = '24-09-29-1717_setting0'
if len(sys.argv) > 1:
    VERSION = sys.argv[1]

trials = []
for file in sorted(os.listdir(f"data/exp/{VERSION}/")):
    if 'test' in file or 'txt' in file:
        continue
    # wid = file.replace('.json', '')

    
    # experimental data
    # fn = f"data/exp/{VERSION}/{file}"
    # print(fn)
    # with open(fn) as f:
    #     data = json.load(f)
    # for i, t in enumerate(data["trial_data"]):
    #     t["wid"] = wid
    #     t["trial_index"] = i
    #     trials.append(t)

    # eyelink data
 
    edf = f'data/eyelink/{wid}/raw.edf'
    print("EDF file path:", edf)
    assert os.path.isfile(edf)
    dest = f'data/eyelink/{wid}/samples.asc'
    if os.path.isfile(edf) and not os.path.isfile(dest):
        cmd = f'edf2asc {edf} {dest}'
        output = subprocess.getoutput(cmd)
        if 'Converted successfully' not in output:
            print(f'Error parsing {edf}', '-'*80, output, '-'*80, sep='\n')


# os.makedirs(f'data/processed/{VERSION}/', exist_ok=True)
# with open(f'data/processed/{VERSION}/trials.json', 'w') as f:
#     json.dump(trials, f)


