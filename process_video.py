'''
Pan_X tracker
====================

Made by: Jan-Jaap van de Velde


Keys
----
ESC - exit
'''

import numpy as np
import cv2, cv
import datetime


lk_params = dict( winSize  = (10, 10),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

class video_obj:
    def __init__(self, filename_video, scan_window=None):

        self.filename_video = filename_video
        self.filename_log = filename_video.rsplit('.',1)[0] + '.log'

        self.cam = None
        self.cam = cv2.VideoCapture(filename_video)

        if self.cam is None or not self.cam.isOpened():
            print 'Warning: unable to open video source: ', filename_video
            exit('Error opening file')

        # get some video properties
        self.frame_width = int(self.cam.get(cv.CV_CAP_PROP_FRAME_WIDTH))
        self.frame_heigth = int(self.cam.get(cv.CV_CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cam.get(cv.CV_CAP_PROP_FPS)
        self.frame_count = int(self.cam.get(cv.CV_CAP_PROP_FRAME_COUNT))
        self.length = float(self.frame_count - 1) / self.fps

        if not scan_window==None:
            self.set_scan_window(scan_window)

    def read(self):
        ret, frame = self.cam.read()
        return frame

    def set_grid(self, roi, num=100):
        [x0,x1,y0,y1] = roi
        dx, dy = x1-x0, y1-y0
        x = np.linspace(x0, x1, round(np.sqrt(num * dx / dy)))
        y = np.linspace(y0, y1, round(np.sqrt(num * dy / dx)))
        x, y = np.meshgrid(x, y)
        self.grid = np.float32(np.array([x, y]).T.reshape(-1, 1, 2))

    def convert_rel_coor(self, rel_coor):
        abs_coor = np.array(rel_coor) / 100.
        abs_coor[0:2] *= self.frame_width
        abs_coor[2:4] *= self.frame_heigth
        return abs_coor


    def get_roi(self,frame_gray):

        class mouse_action:

            def on_mouse(self,click, x, y, drag, args):
                if click==1: #mouse down
                    self.x0, self.y0 = x,y

                elif click==4: #mouse release
                    if self.x0<x : self.x1 = x
                    else :         self.x0,self.x1 = x,self.x0

                    if self.y0<y:  self.y1 = y
                    else:          self.y0,self.y1 = y,self.y0

                    self.finish_flag = True

                if click==0 and drag==1:
                    frame_gray = np.copy(self.frame_gray)
                    cv2.rectangle(frame_gray, (self.x0, self.y0), (x,y), [255,150,150])
                    cv2.imshow('Set Scan Window', frame_gray)
                    pass #update box

            def __init__(self):
                self.frame_gray = np.copy(frame_gray)
                cv2.imshow('Set Scan Window', frame_gray)
                cv.SetMouseCallback('Set Scan Window', self.on_mouse,0)
                self.finish_flag = False

        m = mouse_action()
        while not m.finish_flag:     #loop till finished
            cv2.waitKey(1)

        cv2.destroyWindow('Set Scan Window')

        print [m.x0 * 100 / self.frame_width,
               m.x1 * 100 / self.frame_width,
               m.y0 * 100 / self.frame_heigth,
               m.y1 * 100 / self.frame_heigth]

        return [m.x0, m.x1, m.y0 , m.y1]

    def set_scan_window(self, scan_window):

        roi = np.array(scan_window[0:4]) / 100.
        roi[0:2] *= self.frame_width
        roi[2:4] *= self.frame_heigth

        self.set_grid(roi, scan_window[4])


    def process_video(self, filename_log, video_output=True):

        def draw_str(dst, (x, y), s):
            cv2.putText(dst, s, (x+1, y+1), cv2.FONT_HERSHEY_PLAIN, 1.0, (0, 0, 0), thickness = 2, lineType=cv2.CV_AA)
            cv2.putText(dst, s, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.0, (255, 255, 255), lineType=cv2.CV_AA)

        def calc_flow(prev_gray, frame_gray, p0):
            #calculate the flow for each point in p0
            p1, st, err = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, p0, None, **lk_params)
            p0r, st, err = cv2.calcOpticalFlowPyrLK(frame_gray, prev_gray, p1, None, **lk_params)
            d = abs(p0-p0r).reshape(-1, 2).max(-1)
            good = d < 1
            pan = (p0 - p1)[good,0][:,0].mean()         #will be nan if no flow could be calculated
            return pan

        k = 4
        self.frame_width  /= k
        self.frame_heigth /= k
        if hasattr(self, 'grid'): self.grid /= k

##        pan_x = np.zeros(self.frame_count)
        pan_x = []
        t0 = datetime.datetime.now()

        for frame_idx in range(self.frame_count):

            frame = self.read()
            frame = cv2.resize(frame, (self.frame_width, self.frame_heigth))

            try:
                prev_gray = frame_gray
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            except UnboundLocalError:  #error is raise on the first frame
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                prev_gray = frame_gray   #first 2 frame are equal, so on frame 0 pan_x is 0

                if not hasattr(self, 'grid'):
                    roi = self.get_roi(frame_gray)
                    self.set_grid(roi,100)


            pan = calc_flow(prev_gray, frame_gray, self.grid)
            t1 = datetime.datetime.now()
            dt, t0 = t1-t0, t1

            if video_output:
                try:
                    for p in self.grid:
                        cv2.circle(frame, tuple(p[0]), 2, (0, 255, 0), -1)
                    cv2.rectangle(frame, (self.frame_width/2, self.frame_heigth-10), (self.frame_width/2+int(pan*50), self.frame_heigth-20), [255,150,150], -1)
                    draw_str(frame, (20, 20), 'frame nr: {0:d}'.format(frame_idx))
                    draw_str(frame, (20, 40), 'fps: {0:0.0f}'.format(1e6/dt.microseconds))
                    draw_str(frame, (self.frame_width-140, 20), 'progress: {0:0.1f}%'.format(frame_idx * 100.0 / self.frame_count))
                    cv2.imshow('pan_x', frame)
                    if 0xFF & cv2.waitKey(1) == 27 : break
                except:
                    print 'frame processing error on frame:',frame_idx

            pan_x.append(pan)

        self.pan_x = np.nan_to_num(pan_x)
        cv2.destroyAllWindows()

        # write the log file
        with open(filename_log, 'w') as f:
            for i,j in enumerate(self.pan_x):
                #write frame_number pan_x_value
                f.write('{0}\t{1:0.3f}\n'.format(i,j))

        return self.pan_x



