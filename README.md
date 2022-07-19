# MinvayuPolarPrinter
Information about the MinvayuPolarPrinter firmware and configuration.

## Connecting with the Duet board

See https://docs.duet3d.com/en/How_to_guides/Getting_connected/Getting_connected_to_your_Duet for detailed information.

Briefly, an interface is needed to communicate and send some Gcode to the Duet board. To do that, one can use the GUI interface `cutecom` on linux (or `YAT` on windows). It is also possible to send Gcode directly from the **DuetWebControl** interface.

The user can connect the board to the wifi (using [M552](https://docs.duet3d.com/User_manual/Reference/Gcodes/M552) and [M587](https://docs.duet3d.com/User_manual/Reference/Gcodes/M587) commands) and get the IP address to connect to the **DuetWebControl**. A local name address is also created: our **DuetWebControl** MinvayuPolarPrinter interface can be accessed using the following link: http://www.polarprinter.local.

**DuetWebControl** can be used to control the board from wifi, using a computer or smartphone. With this interface, it is possible to send Gcode lines, run Gcode macros, change configuration, start printing work and even handle height maps. See [Duet Web Control Manual](https://docs.duet3d.com/User_manual/Reference/Duet_Web_Control_Manual) for more information.

## The Firmware

The MinvayPolarPrinter uses the RepRapFirmware ([main Github page](https://github.com/Duet3D/RepRapFirmware) and  [releases page](https://github.com/Duet3D/RepRapFirmware/releases)) with a *polar kinematics configuration*. The polar kinematics configuration is intended to be used for a *turntable polar printer*, but it can also be used for our purpose, considering the whole universe as a turntable.

The polar configuration is done by following the steps of the [PolarKinematics configuration page](https://docs.duet3d.com/User_manual/Machine_configuration/Configuration_Polar). Most of the work is done by the [M669](https://docs.duet3d.com/User_manual/Reference/Gcodes/M669) command, that sets parameters such as radius limits and turntable speed. It is also important to adapt the **homing files**, depending on the homing system (*z probing* or *z endstop* homing system? $\theta$ endstop?).

> In the RepRapFirmware c++ code, M669 K7 will set the current `Kinematics` class to `PolarKinematics`. Then, during run-time, the program will call the `Kinematics::CartesianToMotorSteps` and `Kinematics::MotorStepsToCartesian` functions that will realize the polar/cartesian conversions (call *atan2* and *sqrt* functions).
## Stakes / Goals

<!-- ### Build mini model for test
Peter working on it with Adhavan materials, recycling an old delta printer.

### Cartesian to Polar
Test the [PolarKinematics configuration](https://docs.duet3d.com/User_manual/Machine_configuration/Configuration_Polar) of RRF on the small model.  
Maybe some changes need to be made (but not sure).  
Understand well how the RRF move part work to explain it.  
Contact *disneytoy* and maybe *dc42*. -->

### Manage Servomotor
See if there is servomotor firmware code available.  
[Connecting external servo motor drivers](https://docs.duet3d.com/en/User_manual/Connecting_hardware/Motors_connecting_external)  
[Connecting hobby servos and DC motors](https://docs.duet3d.com/en/User_manual/Connecting_hardware/Motors_servos)  
[Controlling unused IO pins](https://docs.duet3d.com/en/User_manual/Connecting_hardware/IO_GPIO)  

### Ground topography
<!-- Choose a topography shape (Poisson, hexagons -> [*Kepler conjecture*](http://eljjdx.canalblog.com/archives/2006/12/16/3443924.html).  
Check how z-probe meshing works on *DuetWebControl*.  
Build a z-probe sensor system.  
Test on the small model.   -->

See the [mesh bed compensation page](https://docs.duet3d.com/en/User_manual/Connecting_hardware/Z_probe_mesh_bed). The useful Gcode commands are [M557](https://docs.duet3d.com/User_manual/Reference/Gcodes#m557-set-z-probe-point-or-define-probing-grid) with the `R` parameter for round area and [G29](https://docs.duet3d.com/en/User_manual/Reference/Gcodes#g29-mesh-bed-probe).

<!-- ### Handle the Hoist
Need to manage the lift up system. The distance per motor rotation seems to be un-constant. Ask Vengat for more information. -->
