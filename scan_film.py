import time
import sys 
import select
import argparse
import time

import requests
import board
import digitalio

from adafruit_motorkit import MotorKit
from adafruit_motor import stepper


class Projector(object):
    def __init__(self):
        self.kit = MotorKit()
        self.base_url = "http://192.168.0.187:8080/"
        self.scan_url = "{}/photo_save_only.jpg".format(self.base_url)
        self.stepper_style = stepper.INTERLEAVE
 
        self.breakbeam = digitalio.DigitalInOut(board.D21)
        self.breakbeam.direction = digitalio.Direction.INPUT
        self.breakbeam.pull = digitalio.Pull.UP

    def scan_film(self, direction, scan=False, frames=None):
        scanned = 0

        while not frames or scanned < frames:
            break_if_interrupted(scanned)
            print("Processing frame #{}".format(scanned))
            self.move_circuit(direction, scan)
            scanned += 1

    def move_circuit(self, direction, steps, scan=False):
        scan_url = "{}/photo_save_only.jpg".format(self.base_url)

        # Move until beam is blocked
        if self.breakbeam.value:
            self.move_until_condition(False, direction)

        if scan:
            req = requests.post(self.scan_url)
            if req.status_code != 200:
                raise Exception("Failed to save frame... error contacting server")
            print ("Succesfully scanned frame!")
        else:
            print("CLICK!")
            time.sleep(1)

        # Move until no longer blocked then edge a little further
        self.move_until_condition(True, direction)
        for i in range(400):
            self.kit.stepper1.onestep(direction=direction, style=self.stepper_style)

    def move_until_condition(self, condition, direction):
        while self.breakbeam.value is not condition:
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

    args = parser.parse_args()

    frames = int(args.frames) if args.frames else None

    scan = args.scan

    # Default to going 'forward' through the film unless specified
    direction = stepper.BACKWARD
    if args.rewind:
        direction = stepper.FORWARD

    print("Beginning film scanning routine for {} frames....".format(frames or "infinite"))
    projector.scan_film(direction, scan, frames)


main()
