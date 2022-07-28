import os.path
import sys
import numpy as np
import fileinput

DEBUG = "-debug" in sys.argv[1:] or "-d" in sys.argv[1:]

usage = """Usage : pyhton3 generate_polygons_gcode.py [data_file] [-nohoming] [-d] [-h]

Generate a gcode file corresponding to the print of regular polygons in the xy-plane.
The script take parameter lines in standard input and write gcode lines in the standard output.

It is possible to use a file as input (eg: `python3 generate_polygons_gcode.py argument_file`).
It is also possible to use user keyboard input as argument: simply use `python3 generate_polygons_gcode.py` and type the argument lines on keyboard (to exit keyboard input, type 'END' or 'EOF').
The user might want to redirect the output to a gcode file: `python3 generate_polygons_gcode.py argument_file > gcode_file`.

The parameter lines should follow the following pattern: `order radius origin_x origin_y` (where order is the number of points).
The three last arguments can be ommited: default radius is 1.0, default origin is (0.0,0.0).
For example, the line `4 1 3 0` will represent a square of radius 1.0 centered at (3,0). Hence, the coordinates of the square points will be [(4,0),(3,1),(2,0),(3,-1)]

optional arguments:
-nohoming  : avoid the G28 command at the beginning of the generated gcode_file.
-d         : enable debug mode.
-h --help  : print this message.
"""

f = 1200

def print_debug(s):
    if DEBUG:
        print(s)


"""detect the string "s" in sys.argv[1:] and return [True,float(v)] where v is the string following the found "s". It returns [False,0.0] if it didn't find "s"."""
def parse_float_argument(s):
    i = 1
    while i < len(sys.argv) and sys.argv[i] != s:
        i += 1
    if i < len(sys.argv)-1 and sys.argv[i] == s :
        v = sys.argv[i+1]
        sys.argv = sys.argv[:i]+sys.argv[i+2:]
        return [True, float(v)]
    return [False, 0.0]

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return np.array([x, y])

def gcodeline(command, params):
    s = ""
    s += command[0]
    s += str(command[1])
    for a, b in params.items():
        s += " "
        s += a + ("{:.2f}".format(round(b, 2)))
    return s

def create_2D_gcodeline(vec2, speed = None, gcodeindex = 1):
    if speed == None:
        return gcodeline(command=('G', gcodeindex), params={'X': vec2[0], 'Y': vec2[1]})
    # if gcodeindex == 1:
    #     return gcodeline(command=('G', gcodeindex), params={'X': vec2[0], 'Y': vec2[1], 'F': speed, 'E':0.01})
    return gcodeline(command=('G', gcodeindex), params={'X': vec2[0], 'Y': vec2[1], 'F': speed})

################################################################################

def main():
    global usage
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(usage)
        return 0

    s = """; Generated with generate_polygons_gcode.py
T0"""
    print_debug(s)
    if "-nohoming" not in sys.argv[1:]:
        print("G28 ; Homing all the axes")
    else :
        sys.argv = list(filter(("-nohoming").__ne__, sys.argv))

    for line in fileinput.input():
        if "END" in line or "EOF" in line:
            break
        args = line.split()
        if len(args) > 0 :
            args[0] = int(args[0])

            if len(args) > 1:
                args[1] = float(args[1])
            else:
                args.append(1.0)

            if len(args) > 2:
                args[2] = float(args[2])
            else:
                args.append(0.0)

            if len(args) > 3:
                args[3] = float(args[3])
            else:
                args.append(0.0)
            generate_polygon_gcode(args, f)
        else :
            print("; error, no arguments in line '"+line[:-1]+"'.")
    # sys.argv.pop(0)
    # args = parse_next_arguments()
    # while len(args) == 4:
    #     generate_polygon_gcode(args, f)
    #     args = parse_next_arguments()
    return 0

def generate_polygon_gcode(args, f):
    O = np.array(args[2:4])
    r = args[1]
    order = args[0]
    pos = np.array([0.0, r])
    print_debug(";order "+str(order)+" polygon")
    print(create_2D_gcodeline(np.array([O[0]+r, O[1]+0.0]), 3600, gcodeindex = 0))
    for i in range(1,order+1):
        pos = O + pol2cart(r, i * 2.0*np.pi/order)
        print(create_2D_gcodeline(pos, f))
    print_debug(";End of Gcode")
################################################################################

main()
