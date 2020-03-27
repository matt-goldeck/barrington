#!/bin/bash
# Bash script to process and compile images into an mp4; uses ffmpeg 

# Rename all jpeg files in the folder to follow sequential standard format
ls -v *.jpg | cat -n | while read n f; do mv "$f" "frame-$n.jpg"; done

# Compile video at 24fps, mirror and rotate 180 degrees
ffmpeg -r 24 -start_number 1 -i frame-%d.jpg -vf "transpose=2,transpose=2,hflip" test.mp4
