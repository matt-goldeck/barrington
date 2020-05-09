#!/bin/bash
# Bash script to process and compile images into an mp4; uses ffmpeg + imagemagick

# Rename all jpeg files in the folder to follow sequential standard format
ls -v *.jpg | cat -n | while read n f; do mv "$f" "frame-$n.jpg"; done

# Automagically crop the black border out of the images
mogrify -trim -background black -fuzz 25% -define trim:percent-background=20% *.jpg

# Compile video at 24fps, mirror and rotate 180 degrees
ffmpeg -r 24 -start_number 1 -i frame-%d.jpg -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2,transpose=2,transpose=2,hflip" test.mp4
