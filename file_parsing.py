#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      janjvdv
#
# Created:     04-05-2012
# Copyright:   (c) janjvdv 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import datetime
import numpy as np
import process_signals as ps


def loadfile_csv(file_name, type, raw=False):
    """Loads comma separated files and returns its data

        valid types are:
        'racechrono' = default
        'qstarz'
        'deshaker' = used for log files
    """


    def loadfile_racechrono(file_name, raw=False):
        with open(file_name) as f:

            Race_Chrono_Data = {}
            for i, line in enumerate(f):
                if i<=9:
                    key = [key.strip(',') for key in line.strip().split(',',1)]
                    try:
                        Race_Chrono_Data['Info'].append(key)
                    except(KeyError):
                        Race_Chrono_Data['Info']=[key]
                elif i==10:
                    Header = line.strip().split(',')
                    for x in Header: Race_Chrono_Data[x] = []
                else:
                    key = line.strip().split(',')
                    if not key[18]:
                        for i, x in enumerate(key):
                            Race_Chrono_Data[Header[i]].append(ps.convert_num(x))

        if raw:
            return Race_Chrono_Data
        else:
            Vbox_Data = []
            Vbox_Data.append(Race_Chrono_Data['Locked satellites'])
            Vbox_Data.append(Race_Chrono_Data['Timestamp (s)'])
            Vbox_Data.append(Race_Chrono_Data['Latitude (deg)'])
            Vbox_Data.append(Race_Chrono_Data['Longitude (deg)'])
            Vbox_Data.append(Race_Chrono_Data['Speed (kph)'])
            Vbox_Data.append(Race_Chrono_Data['Bearing (deg)'])
            Vbox_Data = np.array(Vbox_Data)
            Vbox_Data[2] *= 60
            Vbox_Data[3] *= -60

            return Vbox_Data, Race_Chrono_Data['Info']

    def loadfile_qstarz(file_name):
        """needs updating
        look for details in race chrono import
        but fine for now"""
        with open(file_name) as f:
            Info = []
            Data= []

            for i, line in enumerate(f):
                if i==0:
                    Header = line.strip().split(',')
                    idx_time = Header.index('LOCAL TIME')
                    idx_ms   = Header.index('MS')
                    idx_lat  = Header.index('LATITUDE')
                    idx_long  = Header.index('LONGITUDE')
                    idx_spd  = Header.index('SPEED')
                    idx_head  = Header.index('HEADING')

                else:
                    key = line.strip().split(',')
                    key = [ps.convert_num(x) for x in key]

                    time = [ps.convert_num(x) for x in key[idx_time].split(':')]
                    time = time[0]*3600. + time[1]*60. + time[2] + key[idx_ms]/1000.
                    key = [20, time, key[idx_lat]*60, key[idx_long]*-60, key[idx_spd], key[idx_head]]
                    Data.append(key)

        return np.array(Data).T, Info

    def loadfile_deshaker(file_name):
        with open(file_name) as f:
            Data= []
            for i, line in enumerate(f):
                key = line.strip().split('\t')
                key = [ps.convert_num(x) for x in key]

                try:
                    key[1]/2
                    Data.append([key[0],key[1]])
                except:
                    pass
        return np.array(Data).T


    if type=='racechrono':
        return loadfile_racechrono(file_name, raw)
    elif type=='qstarz':
        return loadfile_qstarz(file_name)
    elif type=='deshaker':
        return loadfile_deshaker(file_name)
    elif type=='log':
        return loadfile_deshaker(file_name)



def write_vbox(file_name, GPS_Data, Info, vbox_prefix, video_params, time_zone=0):
    """Writes .vbo files for RaceLogic Circuit Tools

    arguments:
        file_name
        GPS_Data
        Info
        avifileindex
        vbox_aviname
        avi_length
        delay
        time_zone=0
    """
##    channels = []

##    filename_video, avi_length, delay = zip(*video_params)

    with open(file_name, 'w') as f:

        # write creation time
        date = datetime.datetime.now()
        f.write('File created on {0.day:02}/{0.month:02}/{0.year:02} @ {0.hour:02}:{0.minute:02}\n'.format(date))

        #write [header]
        f.write('\n[header]\n')
        vbox_header=[
        'satellites',
        'time',
        'latitude',
        'longitude',
        'velocity kmh',
        'heading',
        'avifileindex',
        'avisynctime']

        for line in vbox_header:
            f.write('{0}\n'.format(line))

        #write [avi]
        f.write('\n[avi]\n')
        f.write(vbox_prefix + '\n')
        f.write('MP4' + '\n')

        #write [comments]
        if Info:
            comments = ['\n[comments]',
            'Session note:',
            'Generator: {0}'.format(Info[0]),
            'Title: Import Script',
            'Session type: {0}'.format(Info[3][1]),
            'Track name: {0}'.format(Info[4][1]),
            'Driver name: {0}'.format(Info[5][1]),
            'Scope: Traveled route']
            for line in comments:
                f.write('{0}\n'.format(line))

        #write [laptiming]
##        f.write('\n[laptiming]\n')

        video_data = np.zeros((len(GPS_Data[1]), 2))
        video_data[:,1] -= 1

        #write [session data] and prepare avifileindex and time
        f.write('\n[session data]\n')
        for i, (filename_video, avi_length, delay) in enumerate(video_params):
            f.write('Processed file({:04d}, {}s) : {}\n'.format(i+1, avi_length, filename_video))
            f.write('Time Delay: {}\n'.format(ps.convert_time(abs(delay), 1)))

            starttime_video = GPS_Data[1][0] + delay
            endtime_video = starttime_video + avi_length
            ind = np.logical_and( GPS_Data[1]>starttime_video , GPS_Data[1]<endtime_video)

            video_data[ind,0] = i+1
            video_data[ind,1] = (GPS_Data[1][ind] - starttime_video) * 1000


        #write [column names]
        f.write('\n[column names]\n')
        f.writelines('sats time lat long velocity heading avifileindex avisynctime\n')


        #write [data] block
        f.write('\n[data]\n')

        ind = video_data[:,0] != 0
        
        t0 = 0
        for (D, v) in zip(GPS_Data.T[ind], video_data[ind]):

            #time since previous measurement
            gps_time = D[1]

            #discard small timesteps due to crashing Circuit Tools (take care with high sample rates ;-)
            if gps_time - t0 < 0.05:
##                print 'WARNING: timestep to small for Circuit Tools'
                continue
            t0 = gps_time

            f.write('{GPS[0]:03.0f} {time} {GPS[2]:+012.5f} {GPS[3]:+012.5f} {GPS[4]:06.2f} {GPS[5]:06.2f} {video[0]:04.0f} {video[1]:09.0f}\n'.format(GPS=D, time=ps.convert_time(gps_time), video=v))


def write_csv(file_name, GPS_Data, Info, vbox_aviname, video_params, time_zone=0):
    pass

