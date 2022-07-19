import os.path
import sys
import numpy as np
#from gcodeparser import GcodeParser

script_path = os.path.abspath(__file__)
directory_path = script_path[:-len("check_polar_gcode.py")]

DEBUG = "-debug" in sys.argv[1:] or "-d" in sys.argv[1:]

r = 1.0
f = 900
m = 3
M = 3
O = np.array([0.0,0.0])

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

"""detect the string "s" in sys.argv[1:] and return [True,int(v)] where v is the string following the found "s". It returns [False,0.0] if it didn't find "s"."""
def parse_int_argument(s):
    i = 1
    while i < len(sys.argv) and sys.argv[i] != s:
        i += 1
    if i < len(sys.argv)-1 and sys.argv[i] == s :
        v = sys.argv[i+1]
        sys.argv = sys.argv[:i]+sys.argv[i+2:]
        return [True, int(v)]
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
    return gcodeline(command=('G', gcodeindex), params={'X': vec2[0], 'Y': vec2[1], 'F': speed})

################################################################################

def main():
    if sys.argv[1:] == [] or "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print("""Usage : pyhton3 generate_poly.py
[-r radius][-m min_order] [-M max_order] [-Ox origin_x] [-Oy origin_y] [-f feedrate] [-nohoming]
[-d] [-h]

Print a generated gcode that simulate the 2D drawing of regular polygons from order m to order M, centered at O with radius r.

-r radius     : set the radius of the polygons (default is 1.0).
-f feedrate   : set the feedrate of the movement (default is 900).
-m min_order  : set the minimum polygon order (default is 3).
-M max_order  : set the maximum polygon order (default is 3).
-Ox origin_x  : set the origin x coordinate (default is 0.0).
-Oy origin_y  : set the origin y coordinate (default is 0.0).
-nohoming     : disable the homing at the beginning of the gcode.
-debug -d     : enable debug.

-h ou --help affiche ce message.""")
        return 1

    global r
    global f
    global m
    global M
    global O
    temp = parse_float_argument("-r")
    if temp[0]:
        r = max(temp[1], 0.0)

    temp = parse_float_argument("-f")
    if temp[0]:
        f = max(temp[1], 0.0)

    temp = parse_int_argument("-m")
    if temp[0]:
        m = max(temp[1], 3)

    temp = parse_int_argument("-M")
    if temp[0]:
        M = max(temp[1], m)

    temp = parse_float_argument("-Ox")
    if temp[0]:
        O[0] = temp[1]
    temp = parse_float_argument("-Oy")
    if temp[0]:
        O[1] = temp[1]
    print_debug(";m: "+str(m))
    print_debug(";M: "+str(M))
    print_debug(";O: "+str(O))

    generate_gcode(m,M,O)
    return 0

def generate_gcode(m,M,O):
    s = """;Generated with generate_poly.py
T0"""
    print(s)
    if "-nohoming" not in sys.argv[1:]:
        print("G28 ; Homing all the axes")
    print(create_2D_gcodeline(np.array([O[0]+r, O[1]+0.0]), 3600, gcodeindex = 0))
    pos = np.array([0.0, r])
    for order in range(m,M+1):
        print_debug(";order "+str(order)+" polygon")
        for i in range(1,order+1):
            pos = O + pol2cart(r, i * 2.0*np.pi/order)
            print(create_2D_gcodeline(pos, f))
    print_debug(";End of Gcode")
################################################################################

main()
