import numpy as np
import subprocess

site_locations = np.load("WMOStationDatabase.npz")

max_proc = 10
cur_proc = 0
procs = []
for location in site_locations.keys():
    site_string = site_locations[location]
    if site_string[9] != 'X':
        # Then it's not a nexrad site        
        continue
    if site_string[-1].split()[-1] != 'US':
        # It's not a US site
        continue
    print site_string
    if cur_proc < max_proc:
        print 'Getting', location
        p = subprocess.Popen(['python', 'ftp_vad.py', location.lower()])    
        procs.append(p)
        cur_proc += 1
    else:
        for p in procs:
            p.wait()
        cur_proc = 0

