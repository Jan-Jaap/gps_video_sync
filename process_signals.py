#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      janjvdv
#
# Created:     17-10-2012
# Copyright:   (c) janjvdv 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import numpy as np

def align_signals(signal_1, signal_2, choose_peak=False):

    #calculate the correlation between the two signals
    corr =  np.correlate(signal_2,signal_1,'same')
    #calc how much to shift signal 1 to lineup with signal 2
    frame_shift = corr.argmax() - len(signal_1) / 2

    #if interaction is required a graph is created where peaks can be selected
    if choose_peak:
        import matplotlib.pyplot as plt
        class plot_obj:

            # define what should happen when a point is picked
            # note* all variables used are not in local dict but taken from global dict
            def onpick(self, event):
                coor = event.artist.get_xdata()[0]
                self.frame_shift  = coor - min(len(signal_1), len(signal_2))/2
                self.update()

            def __init__(self):

                self.frame_shift=   frame_shift
                peaks = peakdet(corr,corr.max())[0]
                ind = peaks[:,1].argsort()[-10:][::-1]
                peaks = peaks[ind]

                # create the figure and add the handler which reacts to a pick event
                fig = plt.figure()

                plt.subplot(211)
                plt.title('Correlation')
                plt.plot(corr)
                fig.canvas.mpl_connect('pick_event',self.onpick)
                for x, y in peaks:
                    plt.plot(x, y,'bo', picker=3)

                self.ax = plt.subplot(212)

                plt.title('GPS and Video Data')
                plt.plot(signal_2/20,'r')
                plt.plot(np.arange(len(signal_1)) + frame_shift, signal_1,'k')
                plt.show()

            def update(self):
                self.ax.lines.pop(1)
                plt.plot(np.arange(len(signal_1)) + self.frame_shift, signal_1,'k')
                plt.show()

        graph = plot_obj()
        frame_shift = graph.frame_shift
    return frame_shift


def convert_time(secs, readable=False):

    h = secs // 3600 % 24   #hours
    m = secs % 3600 // 60   #minutes
    s = secs % 60           #seconds
    if readable:
        return '{0:02.0f}:{1:02.0f}:{2:05.2f}'.format(h, m, s)
    else:
        return '{0:02.0f}{1:02.0f}{2:05.2f}'.format(h, m, s)


def conv_num(s): #convert strings to numbers
    if type(s) is str:
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return s
    else:
        return s

def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Currently returns two lists of tuples, but maybe arrays would be better

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    """
    maxtab = []
    mintab = []

    if x is None:
        x = np.arange(len(v))

    v = np.asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not np.isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        sys.exit('Input argument delta must be positive')

    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN

    lookformax = True

    for i in xrange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]

        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return np.asarray(maxtab), np.asarray(mintab)

def process_gps(GPS_Data):

    GPS_Data = gps_data_cleanup(GPS_Data)

    #Data from GPS log
    gps_time = GPS_Data[1]
    gps_speed = GPS_Data[4]
    gps_heading = GPS_Data[5]

    #calculate yaw_rate from heading data
    GPS_yaw_rate = get_angular_speed((gps_heading, gps_time))
    #discard data where speed is below treshold
    GPS_yaw_rate[gps_speed[1:]<1] = 0

    #resample data to frame rate
    GPS_yaw_rate = resample((gps_time[1:], GPS_yaw_rate), 1001. / 30 / 1000)

    return GPS_yaw_rate


def resample((x, y), rate):

    if not np.all(np.diff(x) > 0):
        print np.diff(x)
        raise IndexError('x data not in accending order')

    new_time = np.arange(min(x),max(x), rate)

    print len(x),'->',len(new_time)

    return np.interp(new_time, x, y)


def gps_data_cleanup(GPS_Data):

    #sort on timestamp and remove duplicates
    gps_time = GPS_Data[1]
    index1 = np.argsort(gps_time)
    index2 = np.unique(gps_time[index1], return_index=True)[1]
    GPS_Data = GPS_Data.T[index1][index2].T
    return GPS_Data

def convert_num(s): #convert strings to numbers
    if type(s) is str:
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return s
    else:
        return s

def get_angular_speed((x, t)):    #get angular velocity from heading
    x = np.diff(x)
    x[x>180] -= 360
    x[x<-180] += 360
    x /=  np.diff(t)
    x[abs(x)>100]=0
    return x
