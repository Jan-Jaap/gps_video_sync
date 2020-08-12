#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      janjvdv
#
# Created:     16-10-2012
# Copyright:   (c) janjvdv 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os

from process_video import video_obj
from file_parsing import loadfile_csv, write_vbox
import process_signals as ps

#TODO: Make main accept list of video files instead of looping with with separate videofilenames. Avoid loading csv each time
#TODO: Support for multiple csv files
#TODO: export 1 vbo file for all video's or make function to join vbo files (option setting)
#TODO: automaticale rename video files (option setting)



def gps_video_sync(filename_data, filename_videos, directory, vbox_prefix, csv_type, time_zone=0, video_output='True', choose_peak='True', **rest):

    #processing input from config file
    time_zone  = ps.conv_num(time_zone)
    choose_peak = choose_peak.lower() in ("yes", "true", "t", "1")
    video_output =  video_output.lower() in ("yes", "true", "t", "1")
    file_out = filename_data.rsplit('.',1)[0] + '.vbo'

    try:
        # scan_window = map(ps.conv_num, rest['scan_window'].split(','))
        scan_window = [float(s) for s in rest['scan_window'].split(',')]
    except KeyError:
        scan_window = None

    #create the video files
    videos = [video_obj(file_name, scan_window) for file_name in filename_videos]


    video_params=[]
    #Lineup all video's with the GPS data
    for video in videos:

        #Data from deshaker video log
        try:
            video.pan_x = loadfile_csv(video.filename_log,'log')[1]
            print('Video data has been loaded from .log file')

        #if not available make new log file from video
        except IOError:
            print('No log file found')
            print('I will now try to create a .log file for you (experimental)')
            video.process_video(video.filename_log, video_output)
        finally:
            video.cam.release()
        #Load GPS data
        print('Start loading GPS data from .csv file')
        GPS_Data, Info = loadfile_csv(filename_data, csv_type)
        GPS_yaw_rate = ps.process_gps(GPS_Data)

        #calculate the shift in index with cross correlation
        print('Start aligning signals')
        video.frame_shift = ps.align_signals(video.pan_x, GPS_yaw_rate, choose_peak)

        #30 fps is 1/30s per frame :-)
        video.delay = video.frame_shift / video.fps

        #positive delay means gps starts earlier then video
        print('Frame Shift:\t{0}\n'.format(video.frame_shift), 'Time Shift:\t\t{0}'.format(ps.convert_time(abs(video.delay), 1)))
        video_params.append((video.filename_video, video.length, video.delay))

    #output to vbo file for usage in Racelogic Circuit Tools
    nargs_write_vbox = dict(
        file_name       =   file_out,
        GPS_Data        =   GPS_Data,
        Info            =   Info,
        vbox_prefix     =   vbox_prefix,
        time_zone       =   time_zone,
        video_params    =   video_params)

    print('Writing files')
    print(nargs_write_vbox)
    write_vbox(**nargs_write_vbox)

if __name__ == '__main__':

    import configparser
    config = configparser.ConfigParser()
    config.read('gps_video_sync.ini')

    for section in config.sections():                                           #do a run with the settings from that section
        nargs_run = dict(config.items(section))
        print(section, 'in progress')
        root = nargs_run['directory']                                                #get the dir from the settings
        includes = tuple([ext.lower().strip() for ext in nargs_run['video_ext'].split(',')])                   #which extensions to include for processing
        prefix = nargs_run['vbox_prefix'].lower()

        filename_videos = [os.path.join(root,file) for file in os.listdir(root) if file.lower().endswith(includes) and file.lower().startswith(prefix)]
        print(filename_videos)        
        filename_data = [os.path.join(root,file) for file in os.listdir(root) if file.lower().endswith(".csv")][0]    #select the first .csv
        print(filename_data)

        gps_video_sync(filename_data, filename_videos, **nargs_run)

