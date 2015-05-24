import numpy as np
import profile
from datetime import datetime
from sharppy.io.decoder import Decoder
from StringIO import StringIO

class VADDecoder(Decoder):
    def __init__(self, file_name):
        super(VADDecoder, self).__init__(file_name)

    def _parse(self, file_name):
        file_data = self._downloadFile(file_name)
        
        file_profiles = file_data.split('\n\n\n')

        profiles = {}
        dates = []
        profs = []
        for m in file_profiles[:len(file_profiles)-1]:
            prof, dt_obj = self._parseSection(m)
            dates.append(dt_obj)
            profs.append(prof)
        profs = np.asarray(profs)
        dates = np.unique(np.asarray(dates))
        profiles['VAD'] = profs
        return profiles, dates

    def _parseSection(self, section):
        parts = section.split('\n')
        dt_obj = datetime.strptime(parts[0], 'TIME = %y%m%d/%H%M')
        location = parts[1].split('=')[1].strip()
        data = '\n'.join(parts[4:])
        sound_data = StringIO( data )
        hght, wdir, wspd, rms = np.genfromtxt( sound_data, delimiter=',', unpack=True)
         
        prof = profile.create_profile(profile='vad', hght=hght, wspd=wspd,\
                                      wdir=wdir, rms=rms, location=location)
        return prof, dt_obj
"""
from sharppy.sharptab import interp
vad = VADDecoder('kgwx.txt')
profs = vad.getProfiles(prof_type='vad')
print vad.getProfileTimes()
print profs[0].hght, profs[0].rms
print interp.generic_interp_hght(6000, profs[0].hght, profs[0].wspd, log=False)
print interp.generic_interp_hght(6000, profs[0].hght, profs[0].u, log=False)
print interp.generic_interp_hght(6000, profs[0].hght, profs[0].v, log=False)
"""

