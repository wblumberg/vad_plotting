import matplotlib as mpl
mpl.use("Agg")
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np
import sys
from datetime import datetime, timedelta
import gc
from sharppy.sharptab import interp
#import grayify as gfy
from vad_decoder import VADDecoder
"""
    plot_vad_map.py
    Author: Greg Blumberg (OU/CIMMS/SoM)
    Email: wblumberg@ou.edu

"""

def vec2comp(wdir, wspd):
    '''
        Underlying function that converts a vector to its components
        Parameters
        ----------
        wdir : number, masked_array
        Angle in meteorological degrees
        wspd : number, masked_array
        Magnitudes of wind vector
        Returns
        -------
        u : number, masked_array (same as input)
        U-component of the wind
        v : number, masked_array (same as input)
        V-component of the wind
    '''
    u = wspd * np.sin(np.radians(wdir % 360.)) * -1
    v = wspd * np.cos(np.radians(wdir % 360.)) * -1
    return u, v

def getNexrad(site_locations):
    locs = []
    lats = []
    lons = []
    for location in site_locations.keys():
        site_string = site_locations[location]
        if site_string[9] != 'X':
            # Then it's not a nexrad site        
            continue
        if site_string[-1].split()[-1] != 'US':
            # It's not a US site
            continue
        locs.append(location)
        lats.append(float(site_string[5]))
        lons.append(float(site_string[6]))
    return locs, lats, lons

sites = np.load('WMOStationDatabase.npz')
locs, lats, lons = getNexrad(sites)

"""
# Here is where I wanted to have an option to overlay the reflectivity in light
gray al la the SPC Mesoanalysis surface observation PDF files.
# Load in the radar data if you want to
radarlink = "http://thredds.ucar.edu/thredds/dodsC/nexrad/composite/gini/n0r/1km/%Y%m%d/Level3_Composite_n0r_1km_%Y%m%d_%H%M.gini"
radar_dat = Dataset(datetime.strftime(dt, radarlink))
stride = 30
ref = radar_dat.variables['Reflectivity'][0,::stride,::stride]
ref_grid = np.load('1kmref_grid.npz')
ref_grid_lat = ref_grid['lat'][::stride,::stride]
ref_grid_lon = ref_grid['lon'][::stride,::stride]
"""

plt.figure(figsize=(17,11))
m = Basemap(llcrnrlon=-120,llcrnrlat=20,urcrnrlat=45, urcrnrlon=-58,
            resolution='h',projection='stere',\
            lat_ts=50,lat_0=50,lon_0=-97., area_thresh=10000)
m.drawcoastlines(color='#999999')
m.drawcountries(color='#999999')
m.drawstates(color='#999999')
#m.drawparallels(np.arange(-80.,81.,10.), linestyle='--', alpha=.5, color='#999999')
#m.drawmeridians(np.arange(-180.,181.,10.), linestyle='--', alpha=.5, color='#999999')

"""
#Plot the radar
ref_x, ref_y = m(ref_grid_lon, ref_grid_lat)
print ref.max(), ref.min()
plt.pcolormesh(ref_x, ref_y, ref, cmap=gfy.grayify_cmap('autumn_r'), vmin=30, vmax=70)
"""

offset = 1e4
for loc, lat, lon in zip(locs, lats, lons):
    gc.collect()
    print lon, lat
    x, y = m(lon, lat)
    xbnds = plt.xlim()
    ybnds = plt.ylim()
  
    print " Plotting", loc
    loc = loc.lower()
    try:
        vad = VADDecoder(loc + '.txt')
    except:
        print " Can't find a file for", loc
    profs = vad.getProfiles(prof_type='vad')
    vad_prof = profs[-1]
    u6km = interp.generic_interp_hght(6000, vad_prof.hght, vad_prof.u, log=False)
    v6km = interp.generic_interp_hght(6000, vad_prof.hght, vad_prof.v, log=False)
    
    u1km = interp.generic_interp_hght(1000, vad_prof.hght, vad_prof.u, log=False)
    v1km = interp.generic_interp_hght(1000, vad_prof.hght, vad_prof.v, log=False)
    print u1km, v1km
    print u6km, v6km
    print 
    try:
        # Plot the 6 km winds
        u_map, v_map = m.rotate_vector(np.asarray([[u6km]]), np.asarray([[v6km]]), np.asarray([[lon]]), np.asarray([[lat]]))
        m.barbs(x,y, u_map[0][0],v_map[0][0], color='b', length=8, sizes={'spacing':.15,'width':.15,'height':.35,'emptybarb':.001})
    except:
        print "Unable to plot 6 km winds"
    try:
        # Plot the 1 km
        u_map, v_map = m.rotate_vector(np.asarray([[u1km]]), np.asarray([[v1km]]), np.asarray([[lon]]), np.asarray([[lat]]))
        m.barbs(x,y, u_map[0][0],v_map[0][0], color='r', length=8, sizes={'spacing':.15,'width':.15,'height':.35,'emptybarb':.001})
    
    except:
        print "Unable to plot 1 km winds"

map_details_x, map_details_y = m(-95,24) 
#plt.text(map_details_x, map_details_y, str(level) + ' mb ' + datetime.strftime(dt, "%Y%m%d/%H%M"), fontsize=18, fontweight='bold', fontstyle='italic') 
plt.tight_layout()
plt.savefig('thing.png', bbox_inches='tight', pad_inches=0)
#plt.show()
#plt.savefig(datetime.strftime(dt, '%Y%m%d_%H_') + str(int(level)) + '.pdf',bbox_inches='tight', pad_inches=0)


