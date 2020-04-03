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
        self.stepper_style = stepper.INTERLEAVE

    def scan_film(self, frames=None, steps=GRABBER_CIRCUIT):
        scanned = 0
        if frames:
            while scanned < frames:
                break_if_interrupted(scanned)
                print("Processing frame #{}".format(scanned))
                self.scan_circuit(x steps)
                scanned += 1
        else:
            while True:
                break_if_interrupted(scanned)
                print("Processing frame #{}".format(scanned))
                self.scan_circuit(steps)
                scanned += 1

    def scan_circuit(self, steps):
        """Image the frame and move the reel forward by specified steps."""
        scan_url = "{}/photo_save_only.jpg".format(self.base_url)

        req = requests.post(scan_url)
        if req.status_code != 200:
            raise Exception("Failed to save frame... error contacting server")

        print ("Succesfully scanned frame!")

        # Rotate motor 1 grabber circuit
        print("Moving to next frame...")
        for i in range(steps):
            self.kit.stepper1.onestep(direction=stepper.BACKWARD, style=self.stepper_style)

    def move_circuit(self, direction, steps, frames=None):
        """Move the reel in a specified direction and step count"""
        if frames:
            scanned = 0
            while scanned < frames:
                break_if_interrupted(scanned)
                for i in range(steps):
                    self.kit.stepper1.onestep(direction=direction, style=self.stepper_style)

                scanned += 1
        else:
            while True:
                break_if_interrupted()
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
    parser.add_argument("-s", "--scan", action='store_true', help="Scans film until interrupted")
    parser.add_argument("-r", "--rewind", action='store_true', help="Rewinds film until interrupted")
    parser.add_argument("-ff", "--forward", action='store_true', help="Fast fowards film until interrupted")
    parser.add_argument("-f", "--frames", help="The number of frames to move")
    parser.add_argument("-p", "--plus", help="How many steps to add per revolution")
    parser.add_argument("-s", "--subtract", help="How many steps to subtract per revolution")

    args = parser.parse_args()

    frames = int(args.frames) if args.frames else None

    # Tinker with number of steps if specified
    steps = GRABBER_CIRCUIT
    if args.plus:
        steps += int(args.plus)
    elif args.subtract:
        steps -= int(args.subtract)

    if args.scan:
        print("Beginning film scanning routine for {} frames....".format(frames or "infinite"))
        projector.scan_film(frames=frames, steps=steps)
    elif args.rewind:
        print("Rewinding film {} frames....".format(frames or "infinite"))
        projector.move_circuit(frames=frames, steps=steps, direction=stepper.FORWARD)
    elif args.forward:
        print("Fast forwarding film {} frames....".format(frames or "infinite"))
        projector.move_circuit(frames=frames, steps=steps, direction=stepper.BACKWARD)


main()
