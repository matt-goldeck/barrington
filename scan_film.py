import time
import sys 
import select
import argparse

import requests

from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

# 400 == num of steps to complete one rev
GRABBER_CIRCUIT = 1100  # 2 1/4 revolutions at no friction


class Projector(object):
    def __init__(self):
        self.kit = MotorKit()
        self.base_url = "http://192.168.0.187:8080/"
        self.scan_url = "{}/photo_save_only.jpg".format(self.base_url)
        self.stepper_style = stepper.INTERLEAVE

    def scan_film(self, direction, steps=GRABBER_CIRCUIT, scan=False, frames=None):
        scanned = 0

        while not frames or scanned < frames:
            break_if_interrupted(scanned)
            print("Processing frame #{}".format(scanned))
            self.move_circuit(direction, steps, scan)
            scanned += 1

    def move_circuit(self, direction, steps, scan=False):
        scan_url = "{}/photo_save_only.jpg".format(self.base_url)

        if scan:
            req = requests.post(self.scan_url)
            if req.status_code != 200:
                raise Exception("Failed to save frame... error contacting server")
            print ("Succesfully scanned frame!")

        print("Moving to next frame...")
        for i in range(steps):
            self.kit.stepper1.onestep(direction=direction, style=self.stepper_style)


def break_if_interrupted(frames=None):
    i, o, e = select.select([sys.stdin], [], [], 0.0001)
    if i == [sys.stdin]:
        print("Breaking!")
        if frames:
            print ("Processed {} frames".format(frames))
        sys.exit()


def main():
    projector = Projector()

    parser = argparse.ArgumentParser()
    parser.add_argument("-scan", "--scan", action='store_true', help="Scans film until interrupted")
    parser.add_argument("-r", "--rewind", action='store_true', help="Rewinds film until interrupted")
    parser.add_argument("-f", "--frames", help="The number of frames to move")
    parser.add_argument("-add", "--add", help="How many steps to add per revolution")
    parser.add_argument("-sub", "--subtract", help="How many steps to subtract per revolution")

    args = parser.parse_args()

    frames = int(args.frames) if args.frames else None

    # Tinker with number of steps if specified
    steps = GRABBER_CIRCUIT
    if args.add:
        steps += int(args.add)
    elif args.subtract:
        steps -= int(args.subtract)

    scan = args.scan

    # Default to going 'forward' through the film unless specified
    direction = stepper.BACKWARD
    if args.rewind:
        direction = stepper.FORWARD

    print("Beginning film scanning routine for {} frames....".format(frames or "infinite"))
    projector.scan_film(direction, steps, scan, frames)


main()
