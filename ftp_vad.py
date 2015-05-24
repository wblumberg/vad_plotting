import ftplib
import numpy as np
from datetime import datetime, timedelta
import urllib2
import struct
import sys

class VADFile(object):
    def __init__(self, file):
        self._rpg = file

        self._readHeaders()
        has_symbology_block, has_graphic_block, has_tabular_block = self._readProductDescriptionBlock()

        if has_symbology_block:
            self._readProductSymbologyBlock()

        if has_graphic_block:
            pass

        if has_tabular_block:
            self._readTabularBlock()
        return

    def _readHeaders(self):
        wmo_header = self._read('s30')

        message_code = self._read('h')
        message_date = self._read('h')
        message_time = self._read('i')
        message_length = self._read('i')
        source_id = self._read('h')
        dest_id = self._read('h')
        num_blocks = self._read('h')

        return

    def _readProductDescriptionBlock(self):
        self._read('h') # Block separator
        self._radar_latitude  = self._read('i') / 1000.
        self._radar_longiutde = self._read('i') / 1000.
        self._radar_elevation = self._read('h')

        product_code = self._read('h')
        if product_code != 48:
            print "This isn't a VAD file."

        operational_mode    = self._read('h')
        self._vcp           = self._read('h')
        req_sequence_number = self._read('h')
        vol_sequence_number = self._read('h')

        scan_date    = self._read('h')
        scan_time    = self._read('i')
        product_date = self._read('h')
        product_time = self._read('i')

        self._read('h')      # Product-dependent variable 1 (unused)
        self._read('h')      # Product-dependent variable 2 (unused)
        self._read('h')      # Elevation (unused)
        self._read('h')      # Product-dependent variable 3 (unused)
        self._read('h' * 16) # Product-dependent thresholds (how do I interpret these?)
        self._read('h' * 7)  # Product-dependent variables 4-10 (mostly unused ... do I need the max?)

        version    = self._read('b')
        spot_blank = self._read('b')

        offset_symbology = self._read('i')
        offset_graphic   = self._read('i')
        offset_tabular   = self._read('i')

        self._time = datetime(1969, 12, 31, 0, 0, 0) + timedelta(days=scan_date, seconds=scan_time)
        print self._time

        return offset_symbology > 0, offset_graphic > 0, offset_tabular > 0

    def _readProductSymbologyBlock(self):
        self._read('h') # Block separator
        block_id = self._read('h')

        if block_id != 1:
            print "This isn't the product symbology block."

        block_length    = self._read('i')
        num_layers      = self._read('h')
        layer_separator = self._read('h')
        layer_num_bytes = self._read('i')
        block_data      = self._read('h' * (layer_num_bytes / struct.calcsize('h')))

        packet_code = -1
        packet_size = -1
        packet_counter = -1
        packet_value = -1
        packet = []
        for item in block_data:
            if packet_code == -1:
                packet_code = item
            elif packet_size == -1:
                packet_size = item
                packet_counter = 0
            elif packet_value == -1:
                packet_value = item
                packet_counter += struct.calcsize('h')
            else:
                packet.append(item)
                packet_counter += struct.calcsize('h')

                if packet_counter == packet_size:
                    if packet_code == 8:
                        str_data = struct.pack('>' + 'h' * (packet_size / struct.calcsize('h') - 3), *packet[2:])
                    elif packet_code == 4:
                        pass

                    packet = []
                    packet_code = -1
                    packet_size = -1
                    packet_counter = -1
                    packet_value = -1

        return

    def _readTabularBlock(self):
        self._read('h')
        block_id = self._read('h')
        if block_id != 3:
            print "This is not the tabular block."

        block_size = self._read('i')

        self._read('h')
        self._read('h')
        self._read('i')
        self._read('i')
        self._read('h')
        self._read('h')
        self._read('h')

        self._read('h')
        self._read('i')
        self._read('i')
        self._read('h')
        product_code = self._read('h')

        operational_mode    = self._read('h')
        vcp                 = self._read('h')
        req_sequence_number = self._read('h')
        vol_sequence_number = self._read('h')

        scan_date    = self._read('h')
        scan_time    = self._read('i')
        product_date = self._read('h')
        product_time = self._read('i')

        self._read('h')      # Product-dependent variable 1 (unused)
        self._read('h')      # Product-dependent variable 2 (unused)
        self._read('h')      # Elevation (unused)
        self._read('h')      # Product-dependent variable 3 (unused)
        self._read('h' * 16) # Product-dependent thresholds (how do I interpret these?)
        self._read('h' * 7)  # Product-dependent variables 4-10 (mostly unused ... do I need the max?)

        version    = self._read('b')
        spot_blank = self._read('b')

        offset_symbology = self._read('i')
        offset_graphic   = self._read('i')
        offset_tabular   = self._read('i')

        self._read('h') # Block separator
        num_pages = self._read('h')
        self._text_message = []
        for idx in range(num_pages):
            num_chars = self._read('h')
            self._text_message.append([])
            while num_chars != -1:
                self._text_message[-1].append(self._read("s%d" % num_chars))
#               print self._text_message[-1][-1]
                num_chars = self._read('h')

        return

    def _read(self, type_string):
        if type_string[0] != 's':
            size = struct.calcsize(type_string)
            data = struct.unpack(">%s" % type_string, self._rpg.read(size))
        else:
            size = int(type_string[1:])
            data = tuple([ self._rpg.read(size).strip("\0") ])

        if len(data) == 1:
            return data[0]
        else:
            return list(data)

site = sys.argv[1]
no_samples = 10

HOST = 'tgftp.nws.noaa.gov'
f = ftplib.FTP(HOST)
f.login()

path2files = '/SL.us008001/DF.of/DC.radar/DS.48vwp/SI.' + site
f.cwd(path2files)

data = []
f.dir(data.append)
dates = []
filenames = []
for line in data:
    if line.split()[8] == 'sn.last':
        continue
    filenames.append(line.split()[8])
    datestr = ' '.join(line.split()[5:8])
    dt = datetime.strptime(datestr, '%b %d %H:%M')
    dates.append(dt)

dates = np.asarray(dates)
filenames = np.asarray(filenames)
idx_sort = np.argsort(np.asarray(dates))[::-1]
dates = dates[idx_sort][:no_samples]
filenames = filenames[idx_sort][:no_samples]
f.close()

out = open(site + '.txt', 'w')


for fn, dt in zip(filenames, dates):
    vad = VADFile(urllib2.urlopen('ftp://' + HOST + '/' + path2files + '/' + fn))

    vad_list = []
    for page in vad._text_message:
        if (page[0].strip())[:20] == "VAD Algorithm Output":
            vad_list.extend(page[3:])

    altitude = []
    wind_dir = []
    wind_spd = []
    rms_error = []
    slant_range = []
    elev_angle = []

    for line in vad_list:
        values = line.strip().split()
        wind_dir.append(int(values[4]))
        wind_spd.append(int(values[5]))
        rms_error.append(float(values[6]))
        slant_range.append(float(values[8]))
        elev_angle.append(float(values[9]))

    #       altitude_msl = (np.array(altitude) + vad._radar_elevation) / 3281.
    #       altitude_agl = np.array(altitude) / 3281.

    wind_dir = np.array(wind_dir)
    wind_spd = np.array(wind_spd)
    rms_error = np.array(rms_error)
    slant_range = np.array(slant_range) * 6067.1 / 3281.
    elev_angle = np.array(elev_angle)

    r_e = 4. / 3. * 6371
    altitude_agl = np.sqrt(r_e ** 2 + slant_range ** 2 + 2 * r_e * slant_range * np.sin(np.pi * elev_angle / 180.)) - r_e
    altitude_agl *= 1000
    time = vad._time.strftime("TIME = %y%m%d/%H%M")

    header = time + '\nSTID = ' + site.upper() + '\n\n'
    out.write(header + 'HGHT, WDIR, WSPD, RMS\n')
    for i in range(len(altitude_agl)):
        string = str(round(altitude_agl[i], 2)) + ',' + str(round(wind_dir[i],2)) + ',' +\
                 str(round(wind_spd[i], 2)) + ',' + str(round(rms_error[i],2)) + '\n'
        out.write(string)
    out.write('\n\n')
out.close()
    



