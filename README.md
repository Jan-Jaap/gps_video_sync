# gps_video_sync
Synchoronize GPS and video data from track racing for use in RaceLogic Circuit Tools

Uses OpenCV optical flow to correlate video rotation with GPS heading data.

Install dependencies:

conda install opencv



Input:

GPS: data from Racechrono exported .csv
Video: .avi or .mp4

Output:
.vbox file with sychronized gps data to be used in RaceLogic Circuit Tools

todo:
renaming video files to correct naming convention for Circuit Tools
