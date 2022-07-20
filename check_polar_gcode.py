import os.path
import sys
import numpy as np
from gcodeparser import GcodeParser

script_path = os.path.abspath(__file__)
directory_path = script_path[:-len("check_polar_gcode.py")]

DEBUG = "-debug" in sys.argv[1:] or "-d" in sys.argv[1:]
VERBOSE = "-verbose" in sys.argv[1:] or "-v" in sys.argv[1:]

usage = """Usage : pyhton3 check_polar_gcode.py gcode_file1 gcode_file2 ... [-r minradius] [-R maxradius] [-Ox origin_x] [-Oy origin_y] [-d] [-v] [-h]

Check if in the gcode files, the position of the nozzle stays between a distance of minradius and maxradius from the origin. Print out the gcode lines that went wrong with the verbose mode (-v).
Also plot the nozzle xy-path with colors depending on the encountered issues:
* \033[33myelow lines\033[m are G0 rapid movement segment.
* \033[32mgreen lines\033[m are valid segment.
* \033[34mblue lines\033[m are non-valid segment crossing the inner radius area.
* \033[31mred lines\033[m are non-valid segment crossing the outer radius area.
* \033[35mpurple lines\033[m are non-valid segment crossing both the outer and the inner radius area.

-r minradius  : set the minimum radius (default is 0.0).
-R maxradius  : set the maximum radius (default is +infinite).
-Ox origin_x  : set the origin x coordinate (default is 0.0).
-Oy origin_y  : set the origin y coordinate (default is 0.0).
-debug -d     : enable debug.
-verbose -v   : enable verbose (print the encountered issues).

-h --help     : print this message."""

r = 0.0
R = np.inf
O = np.array([0.0,0.0])

def print_debug(s):
    if DEBUG:
        print(s)
def print_verbose(s):
    if DEBUG or VERBOSE:
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

"""l should be a gcode line"""
def get_xy_param(l):
    return [l.get_param("X", default = None), l.get_param("Y", default = None)]

"""the length_squared of a np.array"""
def norm2(v):
    return np.dot(v,v)

def clamp(num, min_value, max_value):
   return max(min(num, max_value), min_value)

"""Compute the squared distance of d(segment(p1,p2), p)"""
def distance_squared_from_segment(p1, p2, p):
    v = p2-p1
    l2 = np.dot(v,v) # = |p2-p1|^2
    if (l2 == 0.0):
        return norm2(p-p1)
    # Consider the line extending the segment, parameterized as p1 + t (p2 - p1).
    # We find projection of point p onto the line.
    # It falls where t = [(p-p1) . (p2-p1)] / |p2-p1|^2
    t = clamp(np.dot(p-p1, v)/l2, 0.0, 1.0)
    return norm2(p - (p1+t*v)) # p1+t*v is the closest point

################################################################################

def main():
    global usage
    if sys.argv[1:] == [] or "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(usage)
        return 0

    global r
    global R
    global O
    temp = parse_float_argument("-r")
    if temp[0]:
        r = temp[1]

    temp = parse_float_argument("-R")
    if temp[0]:
        R = temp[1]

    temp = parse_float_argument("-Ox")
    if temp[0]:
        O[0] = temp[1]
    temp = parse_float_argument("-Oy")
    if temp[0]:
        O[1] = temp[1]
    print_debug("r: "+str(r))
    print_debug("R: "+str(R))
    print_debug("O: "+str(O))

    for arg in sys.argv[1:]:
        if arg[0] != '-':
            print("processing "+arg)
            process(arg)
    return 0

def process(filename):
    # open gcode file and store contents as variable
    with open(filename, 'r') as f:
        gcode = f.read()
    gcode_lines = GcodeParser(gcode, include_comments=True).lines
    if len(gcode_lines) == 0:
        print("empty gcode file")
        return 1

    line_index = 0
    xy = np.array([None,None])
    while np.any(np.array([None,None]) == xy): # loop until we know the position of the nozzle
        l = gcode_lines[line_index]
        if l.command[0] == 'G' and l.command[1] in [0,1]:
            params = get_xy_param(l)
            if params[0] != None:
                xy[0] = params[0]
            # else, keep the previous value

            if params[1] != None:
                xy[1] = params[1]
        line_index += 1

    position_list = [xy.copy()]
    g0_list = [] # list of g0 index in position list
    lines_list = [[]] # list of int_list

    print_debug("first gcode line where the nozzle position is not [Unknown,Unknown]: "+str(line_index))
    for l in gcode_lines[line_index:]:
        if l.command[0] == 'G' and l.command[1] in [0,1]:
            print_debug(l)    # get parsed gcode lines
            previous_xy = xy.copy()
            params = get_xy_param(l)
            if params[0] != None:
                xy[0] = params[0]
            # else, keep the previous value

            if params[1] != None:
                xy[1] = params[1]
            # else, keep the previous value
            if np.any(previous_xy != xy):
                position_list.append(xy.copy())
                lines_list.append([])
                if l.command[1] == 0:
                    # if it is a G0
                    g0_list.append(len(position_list)-1)
            lines_list[-1].append(line_index)
        line_index += 1


    position_array = np.array(position_list)
    [in_list, out_list] = check_polar_array(O,r,R, position_array)
    print_debug(position_array)

    issue_array = np.zeros(len(position_list))
    issue_num = 0

    print_debug("\n##### in_list #####")
    for issue in in_list:
        print_verbose("Issue "+str(issue_num)+" (inside)")
        print_verbose("\tDistance from origin: "+str(np.sqrt(issue[1])))
        for line_index in lines_list[issue[0]]:
            print_verbose("\tl"+str(line_index+1)+":    \t"+gcode_lines[line_index].gcode_str)
        issue_array[issue[0]] += 2 # see issue_array info below
        issue_num += 1

    print_debug("\n##### out_list #####")
    for issue in out_list:
        print_verbose("Issue "+str(issue_num)+" (outside)")
        print_verbose("\tDistance from origin: "+str(np.sqrt(issue[1])))
        for line_index in lines_list[issue[0]]:
            print_verbose("\tl"+str(line_index+1)+":    \t"+gcode_lines[line_index].gcode_str)
        issue_array[issue[0]] += -1 # see issue_array info below
        issue_num += 1

    for i in g0_list:
        issue_array[i] = -2

    print("number of issues: "+str(issue_num))
    plot_path(position_array, issue_array)
    # issue_array info:
    # - 0 : the segment doesn't provoke any issues.
    # - -1 : the segment provoke outside issues.
    # - 2 : the segment provokes inside issues.
    # - 1 : the segment provokes outside and inside issues.
    # - 2 : G0 segment.

"""Return two lists of [array index, dist_squared_from_origin] where the position
   is outside the thick disk D(O,r,R). The first list is inner problems, the
   second is outside problems."""
def check_polar_array(O,r,R, position_array):
    assert(position_array.ndim == 2)
    in_list = []
    out_list = []
    r2 = r*r
    R2 = R*R

    last_p = position_array[0]
    i = 1
    for p in position_array[1:]:
        d2 = distance_squared_from_segment(p, last_p, O)
        if d2 < r2:
            in_list.append([i, d2])
        d2 = max(norm2(p-O), norm2(last_p-O))
        if d2 > R2:
            out_list.append([i, d2])
        last_p = p#.copy()
        i += 1
    return [in_list, out_list]

################################################################################

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm

def plot_path(position_array, issue_array):
    global r
    global R
    global O
    plt.figure()
    plt.subplot(111)
    plt.title('Nozzle 2D Path')

    #plt.plot(position_array[:,0], position_array[:,1], 'r', lw=1)
    points = position_array.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # issue_array info:
    # - 0 : the segment doesn't provoke any issues.
    # - -1 : the segment provoke outside issues.
    # - 2 : the segment provokes inside issues.
    # - 1 : the segment provokes outside and inside issues.
    # - 2 : G0 segment.
    cmap = ListedColormap(['y', 'r', 'g', 'm','b'])
    norm = BoundaryNorm([-2.5, -1.5, -0.5, 0.5, 1.5, 2.5], cmap.N)
    lc = LineCollection(segments, cmap=cmap, norm=norm)
    lc.set_array(issue_array[1:])

    offset = max(1.0, 0.25*r)
    m = min(np.min(position_array)-offset, -0.5*r)
    M = max(np.max(position_array)+offset, 0.5*r)
    plt.xlim(m,M)
    plt.ylim(m,M)

    circle_radius = min(1.42*M,R)
    circle2 = plt.Circle((O[0], O[1]), circle_radius, color='g', alpha = 0.2)
    plt.gca().add_patch(circle2)
    circle1 = plt.Circle((O[0], O[1]), r, color='w', alpha = 1.0)
    plt.gca().add_patch(circle1)
    plt.gca().add_collection(lc)

    print("""    * \033[33myelow lines\033[m are G0 rapid movement segment.
    * \033[32mgreen lines\033[m are valid segment.
    * \033[34mblue lines\033[m are non-valid segment crossing the inner radius area.
    * \033[31mred lines\033[m are non-valid segment crossing the outer radius area.
    * \033[35mpurple lines\033[m are non-valid segment crossing both the outer and the inner radius area.""")
    plt.show()


################################################################################

main()
