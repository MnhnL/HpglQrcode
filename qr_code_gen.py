#!/usr/bin/env python
import argparse

import pyqrcode
import sys


class Writer:
    def __init__(self, buffer):
        self.buffer = buffer

# https://en.wikipedia.org/wiki/HP-GL
# IN: Initialize
# PA x,y: Plot absolute
# SP1: Select pen 1
# PU: Pen Up
# PD: Pen Down

class GCodeWriter(Writer):
    def __init__(self, buffer, depth, step_mm, clearance=2, feedrate=600):
        self.buffer = buffer
        self.x_bit_position = 0
        self.y_bit_position = 0

        self.step_mm = step_mm
        self.depth = depth
        self.clearance = clearance
        self.feedrate = feedrate


    def add_header(self):
        self.buffer.write('IN;PA;SP1;PU;\n')
        self.buffer.write("CT1;\n")


    def add_footer(self):
        self.buffer.write("PU;\n")
        self.buffer.write("PU;SP;\n")


    def define_bit_as_1(self):
        self.increment_y_position()
        x = int(self.x_bit_position*self.step_mm * 100)
        y = int(self.y_bit_position*self.step_mm * 100)
        self.buffer.write(f"PU;PA{x},{y};PD;\n")
        self.buffer.write(f"PA{x+1},{y};\n")

        
    def define_bit_as_0(self):
        self.increment_y_position()

        
    def carrier_return(self):
        self.increment_x_position()
        self.y_bit_position = 0


    def increment_x_position(self):
        self.x_bit_position += 1


    def increment_y_position(self):
        self.y_bit_position += 1


    def new_line(self):
        self.buffer.write("\n")


def generate_gcode(text, output_file, depth, width=None, step=None):
    text = pyqrcode.create(text, error='H')

    print(text.terminal())

    with open(output_file, 'wt') as output:
        code = text.code
        if width:
            step_mm = round(width / len(code), 2)
        else:
            step_mm = round(step, 2)

        print('Total size of QRCode {size:.3f}mm with steps of {step:.3f}mm'.format(size=len(code)*step_mm, step=step_mm))
        writer = GCodeWriter(output, depth, step_mm)
        writer.add_header()
        for row in code:
            # Each code has a quiet zone on the left side, this is the left
            # border for this code
            for bit in row:
                if bit == 1:
                    writer.define_bit_as_1()
                elif bit == 0:
                    writer.define_bit_as_0()
            writer.carrier_return()
        writer.add_footer()


def main():
    parser = argparse.ArgumentParser(description='Generate CNC QRCode GCode from a string.')
    parser.add_argument('text_to_encode', type=str, metavar='TEXT',
                        help='Text to encode in a QRCode')

    parser.add_argument('-d', '--depth', dest='depth', default=1, type=float,
                        help='Depth of each hole of QRCode')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-w', '--width', dest='width', type=float, default=0,
                       help='Total size in mm of the final QRCode')

    group.add_argument('-s', '--step', dest='step', type=float, default=0,
                       help='Step per bit in mm of the final QRCode')

    parser.add_argument('-o', '--output', dest='output_file', type=str, default='output.hpg',
                        help='Output GCode file')

    args = parser.parse_args()
    if args.width:
        generate_gcode(text=args.text_to_encode, depth=args.depth, width=args.width, output_file=args.output_file)
    else:
        generate_gcode(text=args.text_to_encode, depth=args.depth, step=args.step, output_file=args.output_file)

    print('Generation of the GCode is done in {file}'.format(file=args.output_file))


if __name__ == '__main__':
    main()
