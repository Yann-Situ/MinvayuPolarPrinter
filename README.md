# MinvayuPolarPrinter
Information about Minvayu's polar printer. The MinvayPolarPrinter runs on a [DuetWifi board v.1.26](https://www.duet3d.com/DuetWifi) with [RepRapFirmware v.3.4.1](#the-firmware). It is a 3D printer for architectural purpose with a central rotating axis (similar to a crane).

## Connecting With The Duet Board

See [Getting connected to your Duet](https://docs.duet3d.com/en/How_to_guides/Getting_connected/Getting_connected_to_your_Duet) for detailed information.

The best way to communicate with the board is the **DuetWebControl** interface.
**DuetWebControl** can be used to control the board using a computer or smartphone connected to the same wifi point. With this interface, it is possible to send gcode lines, run gcode macros, change configuration, start printing work and even handle height maps. See [Duet Web Control Manual](https://docs.duet3d.com/User_manual/Reference/Duet_Web_Control_Manual) for more information.

To access **DuetWebControl**, it is firstly necessary to communicate some gcode to the Duet board using another interface. To do that, it is possible to use the GUI interface `cutecom` on linux (or `YAT` on windows) after wiring the board to the computer.\
Then, the user can connect the board to the wifi using [M552](https://docs.duet3d.com/User_manual/Reference/Gcodes/M552) and [M587](https://docs.duet3d.com/User_manual/Reference/Gcodes/M587) commands.

After connecting, send `M552 S1` to get the IP address and connect to the **DuetWebControl** by typing the address in the browser.\
A local name address is also created: our **DuetWebControl** MinvayuPolarPrinter interface can be accessed using the following link http://www.polarprinter.local (note that the board needs to be powered up to access the interface).

## The Firmware

The MinvayPolarPrinter uses the RepRapFirmware v.3.4.1 ([main Github page](https://github.com/Duet3D/RepRapFirmware) and  [releases page](https://github.com/Duet3D/RepRapFirmware/releases)) with a *polar kinematics configuration*. The polar kinematics configuration is intended to be used for a *turntable polar printer*, but it can also be used for our purpose, considering the whole universe as a turntable.

The polar configuration is done by following the steps of the [PolarKinematics configuration page](https://docs.duet3d.com/User_manual/Machine_configuration/Configuration_Polar). Most of the work is done by the [M669](https://docs.duet3d.com/User_manual/Reference/Gcodes/M669) command, that sets parameters such as radius limits and turntable speed. It is also important to adapt the **homing files**, depending on the homing system (*z probing* or *z endstop* homing system? $\theta$ endstop?).

> In the RepRapFirmware c++ code, M669 K7 will set the current `Kinematics` class to `PolarKinematics`. Then, during run-time, the program will call the `Kinematics::CartesianToMotorSteps` and `Kinematics::MotorStepsToCartesian` functions that will realize the polar/cartesian conversions (call *atan2* and *sqrt* functions).

For the whole configuration, we need a bunch of information on the mechanical details of the printer. Those information are listed in the [Required information page](https://docs.duet3d.com/User_manual/Overview/Adapting).

## The Slicer

Common slicer softwares (*Cura*, *PrusaSlic3r*, *Slic3r*) can be configured for a round bed shape. However it doesn't seem possible to configure the software to check if the print object is inside our annulus printing area or not.\
We created a python script for this purpose (see [`check_polar_gcode.py`](#check_polar_gcodepy)).

## Testing The Printer

It is possible test the motors individually by using the relative mode ([G91](https://docs.duet3d.com/User_manual/Reference/Gcodes/G91) command) and then using the G1 command with H2 parameter to move individual motors. In the relative mode in polar configuration, the `X` parameter stands for the radius axis whereas the `Y` parameter stands for the rotational axis (the `Y` value must be specified in **degrees**).

The user can also use the [`generate_polygons_gcode.py`](#generate_polygons_gcodepy) python script to create simple gcode for 2D polygonal structures in order to test the *xy*-plane movement.

## Connecting Servo Motor

Main help links concerning servo motors and Duet boards:
- [Connecting external servo motor drivers](https://docs.duet3d.com/en/User_manual/Connecting_hardware/Motors_connecting_external)
- [Connecting hobby servos and DC motors](https://docs.duet3d.com/en/User_manual/Connecting_hardware/Motors_servos)  
- [Controlling unused IO pins](https://docs.duet3d.com/en/User_manual/Connecting_hardware/IO_GPIO)  
- [How to connect integrated servo motors](https://forum.duet3d.com/topic/4570/how-to-connect-integrated-servo-motors/24) (forum talk)

> “You can connect servo drives with step and direction inputs to the Duet just like regular external stepper drivers. They are likely to need 5V drive to the step, direction and enable inputs, so you will probably need the breakout board”
>
> --  <cite>dc42 in [DUET3D --> servo motor](https://reprap.org/forum/read.php?178,844701,844701#msg-844701) (forum talk)</cite>

It will be easier to power the servo motors with a separate power supply to avoid voltage/current issues.\
After connecting the servo, we will need to configure it in the `config.gd` file. Use the [M584](https://docs.duet3d.com/User_manual/Reference/Gcodes/M584) command to remap the axes and use the appropriate [M569](https://docs.duet3d.com/User_manual/Reference/Gcodes/M569) commands to configure the drivers, step pulse timings, closed loops etc. This parts seems a bit tedious and needs details and information.


## Bed Compensation

See the [mesh bed compensation page](https://docs.duet3d.com/en/User_manual/Connecting_hardware/Z_probe_mesh_bed). Use the [M557](https://docs.duet3d.com/User_manual/Reference/Gcodes#m557-set-z-probe-point-or-define-probing-grid) command with the `R` parameter for configuring a round bed grid in the `config.gd` file. Use the [G29](https://docs.duet3d.com/en/User_manual/Reference/Gcodes#g29-mesh-bed-probe) command to probe the bed, load height map from file, disable mesh bed compensation or save height map.

> Summary of gcode commands related to mesh bed compensation
>    - `G29` Run file sys/mesh.g, or if that file isn't found then do `G29 S0`
>    - `G29` S0 Probe the bed and save height map to file
>    - `G29` S1 Load height map from file
>    - `G29` S2 Clear height map
>    - `G29` S3 P"filename" Save height map to file
>    - `G30` Probe the bed at a single point (can be used to measure Z probe trigger height)
>    - `G31` Set Z probe trigger height, threshold and offsets from the print head reference point
>    - `G32` Run sys/bed.g file. You can put commands in bed.g to perform mesh bed levelling, e.g. `M401` followed by `G29 S0` followed by `M402`.
>    - `M374` Save height map to file
>    - `M375` Load height map from file (same as `G29 S1`)
>    - `M376` Set bed compensation taper height
>    - `M401` Deploy Z probe (runs `sys/deployprobe#.g` file where # is the Z probe number, or file sys/deployprobe.g if that file isn't found).
>    - `M402` Retract Z probe (runs `sys/retractprobe#.g` file where # is the Z probe number, or sys/retractprobe.g if that file isn't found)
>    - `M557` Define the probing grid
>    - `M558` Set Z probe type, dive height, probing speed, travel speed between probe points, and probe recovery time
>    - `M561` Clear height map (same as `G29 S2`)


## Additional Python Scripts
This directory contains two handmade python scripts:

### `check_polar_gcode.py`

Take a **gcode file** as input and check if the nozzle *xy*-coordinate movement stays between a distance of `minradius` and `maxradius` from the `origin`.\
As *Cura*, *Slic3r* and *PrusaSlic3r* can't check if the print object is inside our annulus printing area, it is possible to use this script on the resulting gcode file to check if the print will be valid.

   Usage : `pyhton3 check_polar_gcode.py gcode_file [-r minradius] [-R maxradius] [-Ox origin_x] [-Oy origin_y] [-d] [-v] [-h]`
>   - `-r minradius` : set the minimum radius (default is 0.0).
>   - `-R maxradius` : set the maximum radius (default is +infinite).
>   - `-Ox origin_x` : set the origin x coordinate (default is 0.0).
>   - `-Oy origin_y` : set the origin y coordinate (default is 0.0).
>   - `-debug -d`    : enable debug.
>   - `-verbose -v`  : enable verbose (print the encountered issues).
>   - `-h --help`          : print help information.

Print the gcode lines that went wrong using the **verbose mode** (`-v` parameter). Use the `-r`, `-R`, `-Ox` and `-Oy` parameters to define the annulus printing area.


The script also plot the *xy*-coordinates nozzle path with colors depending on the encountered issues:
>    - **yelow lines** are G0 rapid movement segment. Those segments can also raise issues even though it might not be a problem in practice (as G0 segment mostly represent non extruding rapid movement).
>    - **green lines** are valid segment.
>    - **blue lines** are non-valid segment crossing the inner radius area.
>    - **red lines** are non-valid segment crossing the outer radius area.
>    - **purple lines** are non-valid segment crossing both the outer and the inner radius area.

### `generate_polygons_gcode.py`

Generate a gcode file corresponding to the print of regular polygons in the *xy*-plane.
The script take parameter lines in standard input and write gcode lines in the standard output.\
In the MinvayuPolarPrinter project, we use this script to create gcode file to test the xy polar movement.

Usage : `pyhton3 generate_polygons_gcode.py [argument_file] [-nohoming] [-d] [-h]`
>optional arguments:
>- `-nohoming`  : avoid the G28 command at the beginning of the generated gcode_file.
>- `-d`         : enable debug mode.
>- `-h --help`  : print this message

The user can use a file as input or use keyboard input as argument: simply use `python3 generate_polygons_gcode.py` and type the argument lines on keyboard (to exit keyboard input, type *'END'* or *'EOF'*).\
The user might want to redirect the output to a gcode file: in bash, `python3 generate_polygons_gcode.py argument_file > gcode_file` will do the job. For example: `python3 generate_polygons_gcode.py test.datafile > test.gcode`

The parameter lines should follow the following pattern: `order radius origin_x origin_y` (where order is the number of points).\
The three last arguments can be ommited: default radius is 1.0, default origin is (0.0,0.0).
For example, the line ''`4 1 3 0`'' will represent a square of radius 1.0 centered at (3,0). Hence, the coordinates of the square points will be [(4,0),(3,1),(2,0),(3,-1)].

### External Scripts
[text-to-gcode](https://github.com/Stypox/text-to-gcode)
[image-to-gcode](https://github.com/Stypox/image-to-gcode)
