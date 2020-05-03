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
    def __init__(self, auto_mode=False):
        self.kit = MotorKit()
        self.base_url = "http://192.168.0.187:8080/"
        self.scan_url = "{}/photo_save_only.jpg".format(self.base_url)
        self.stepper_style = stepper.DOUBLE

        self.auto_mode = auto_mode
        self.breakbeam = digitalio.DigitalInOut(board.D21)
        self.breakbeam.direction = digitalio.Direction.INPUT
        self.breakbeam.pull = digitalio.Pull.UP

    def scan_film(self, direction, scan=False, frames=None):
        scanned = 0

        while not frames or scanned < frames:
            if not self.auto_mode:
                break_if_interrupted(scanned)
            print("Processing frame #{}".format(scanned))
            self.move_circuit(direction, scan)
            scanned += 1

            if scanned % 3 == 0:
                self.adjust_takeup(direction)

    def move_circuit(self, direction, scan):
        scan_url = "{}/photo_save_only.jpg".format(self.base_url)

        # Move until beam is blocked
        if self.breakbeam.value:
            self.move_until_condition(False, direction)

        if scan:
            self.take_picture()
            print ("Succesfully scanned frame!")
        else:
            print("CLICK!")  # debug output to verify accuracy of circuit
            time.sleep(.5)

        # Move until no longer blocked then edge a little further
        self.move_until_condition(True, direction)
        for i in range(400):
            self.kit.stepper1.onestep(direction=direction, style=self.stepper_style)

    def move_until_condition(self, condition, direction):
        count = 0
        while self.breakbeam.value is not condition:
            count += 1
            self.kit.stepper1.onestep(direction=direction, style=self.stepper_style)

            # Shut down in case something goes horribly wrong
            if count >= 10000:
                raise Exception("Nothing detected in 10000 steps... Shutting down!")

    def adjust_takeup(self, direction):
        # Adjust the takeup spool to pull film taught or loosen
        for i in range(200):
            self.kit.stepper2.onestep(direction=direction, style=stepper.MICROSTEP)

    def initialize_camera(self):
        # Perform necessary settings adjustments
        req = requests.post("{}/ptz?zoom=100".format(self.base_url)) # Adjust zoom
        if req.status_code != 200:
            raise Exception("Failed to initialize zoom.... error contacting server")
        req = requests.post("{}/settings/focusmode?set=off".format(self.base_url)) # Adjust focus
        if req.status_code != 200:
            raise Exception("Failed to initialize focus... error contacting server")

    def take_picture(self):
        scan_url = "{}/photo_save_only.jpg".format(self.base_url)

        attempts = 0
        while attempts < 3:
            try:
                req = requests.post(scan_url, timeout=2)
                return
            except requests.exceptions.Timeout as e:
                print("Timed out... attempting to take photo again.")
                time.sleep(.5)

                attempts += 1
                self.initialize_camera()  # Need to reinitialize in event of timeout

        raise Exception("Failed to contact camera server... Aborting!")

def break_if_interrupted(frames=None):
    i, o, e = select.select([sys.stdin], [], [], 0.0001)
    if i == [sys.stdin]:
        print("Breaking!")
        if frames:
            print ("Processed {} frames".format(frames))
        sys.exit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-scan", "--scan", action='store_true', help="Scans film until interrupted")
    parser.add_argument("-r", "--rewind", action='store_true', help="Rewinds film until interrupted")
    parser.add_argument("-f", "--frames", help="The number of frames to move")
    parser.add_argument("-a", "--auto", action='store_true', help="Whether or not this script is being run automatically")
    args = parser.parse_args()

    frames = int(args.frames) if args.frames else None

    scan = args.scan
    auto = args.auto
    projector = Projector(auto)

    # Default to going 'forward' through the film unless specified
    direction = stepper.BACKWARD
    if args.rewind:
        direction = stepper.FORWARD

    print("Beginning film scanning routine for {} frames....".format(frames or "infinite"))
    projector.scan_film(direction, scan, frames)


main()
