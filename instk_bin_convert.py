#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      janjvdv
#
# Created:     08-08-2013
# Copyright:   (c) janjvdv 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os
import datetime
import numpy as np
import struct

def loadfile_datamonitor(file_name):

    sensor_format = '>LQQLfff'
    byt_size = struct.calcsize(sensor_format)
    data = []

    first_sysTime = []

    with open(file_name, 'rb') as f:
        while True:
            sensor_read = f.read(byt_size)
            if not sensor_read: break
            [typ, sysTime, evTime, len, x,y,z] = struct.unpack(sensor_format, sensor_read)
            if not first_sysTime:
                first_sysTime = sysTime
            data.append([typ,sysTime - first_sysTime, x,y,z])

    return data


def write_csv(file_name, data):
    with open(file_name, 'w') as f:
        for line in data:
            f.write('{0[0]}, {0[1]:d}, {0[2]:f}, {0[3]:f}, {0[4]:f}\n'.format(line))


if __name__ == '__main__':

    print 'in progress'
    root = 'C:\Data\Dropbox'
    filename_videos = [os.path.join(root,fi) for fi in os.listdir(root) if fi.lower().endswith(".bin")]
    data = loadfile_datamonitor(filename_videos[0])
    write_csv(os.path.join(root,'sensor_output.csv'), data)