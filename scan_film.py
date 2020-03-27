import time
import sys 
import select
import argparse

import requests

from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

# 3200 == num of microsteps to complete one revolution
GRABBER_CIRCUIT = 8000 # 2 1/2 revs

class Projector(object):
    def __init__(self):
        self.kit = MotorKit()
        self.base_url = "http://192.168.0.189:8080/"
        self.stepper_style = stepper.MICROSTEP
    def scan_film(self, frames=None):
        scanned = 0
        if frames:
            while scanned < frames:
                break_if_interrupted(scanned)
                print("Processing frame #{}".format(scanned))
                self.scan_circuit(scanned)
                scanned += 1
        else:
            while True:
                break_if_interrupted(scanned)
                print("Processing frame #{}".format(scanned))
                self.scan_circuit(scanned)
                scanned += 1
            
    def scan_circuit(self, scanned_frames):
        scan_url = "{}/photo_save_only.jpg".format(self.base_url)

        req = requests.post(scan_url)
        if req.status_code != 200:
            raise Exception("Failed to save frame... error contacting server")

        print ("Succesfully scanned frame!")

        # Rotate motor 1 grabber circuit
        print("Moving to next frame...")
        for i in range(GRABBER_CIRCUIT):
            self.kit.stepper1.onestep(direction=stepper.FORWARD, style=self.stepper_style)

        self.kit.stepper1.release()

    def infinite_move(self, direction, frames=None):
        if frames:
            scanned = 0
            while scanned < frames:
                break_if_interrupted(scanned)
                for i in range(GRABBER_CIRCUIT):
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

    args = parser.parse_args()
    frames = int(args.frames) if args.frames else None

    if args.scan:
        print("Beginning film scanning routine for {} frames....".format(frames or "infinite"))
        projector.scan_film(frames=frames)
    elif args.rewind:
        print("Rewinding film {} frames....".format(frames or "infinite"))
        projector.infinite_move(frames=frames, direction=stepper.REVERSE)
    elif args.forward:
        print("Fast forwarding film {} frames....".format(frames or "infinite"))
        projector.infinite_move(frames=frames, direction=stepper.FORWARD)

main()

        