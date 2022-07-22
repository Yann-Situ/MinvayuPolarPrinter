# Movement in RepRapFirmware
> This file is a copy of the *Developer-documentation/Movement_in_RepRapFirmware.odt* file in the [RepRapFirmware repository](https://github.com/Duet3D/RepRapFirmware) with additional comments about the actual location of functions in the code.\
The file is useful if one wants to dive in the RepRapFirmware c++ code.

## Overview

### Initial processing
G0, G1, G2 and G3 commands are parsed and turned into a sequence of basic moves which are stored in the move buffer within the Gcodes class. Each basic move is a linear move or an arc move.

### Fetching and segmentation
The Move class calls the ReadMove (`in MoveLoop function`) method in class GCodes to fetch primitive moves (`ReadMove set the movestate and its precalculations`). This may involve segmentation (`in function ReadMove Gcodes.cpp l.2525`), which is done if any of the following is true:

- The kinematics flags segmentation as being required. This will always be the case for nonlinear kinematics (`in PolarKinematics.cpp l.42, the segmentation flags are set`) except for delta kinematics. In RRF 3.3 even linear and delta kinematics can be segmented if desired, for example to support pausing earlier.
- G2 and G3 moves are always segmented into short linear moves.
- Bed compensation is in use. In this case, moves will be divided into segments of size similar to the mesh spacing, unless they are already smaller.

### Queueing and lookahead
Primitive moves read by the Move class are put into the Move queue.
(`in Move.cpp at l.310 ; the MoveQueue seems to be the DDAring`)
Each entry in the move queue is represented by a DDA. Each DDA describes acceleration, steady speed, and deceleration phases of a movement.

When a DDA is added (`Move.cpp at l.310`), its end speed is set to zero in case it is the last move (`DDA.cpp in function InitStandardMove at l.540`). Then the system computes the maximum ending speed of the DDA, which is limited either by the configured acceleration and the move length, or by the maximum configured movement speed. It increases the speed of the previous move if possible in order to match this speed. This will only be possible if the previous DDA has a deceleration segment. If the previous DDA was a pure deceleration move then it may also be possible to increase the ending speed of that DDA; and so on.

> in the MoveLoop, the call to AddStandardMove results in calling the function InitStandardMove in DDA.cpp l.297, where many things are done :
1. Compute the new endpoints and the movement vector (call  Kinematics::CartesianToMotorSteps to convert the nextMove.coords to the endpoints of the DDA. Call Kinematics::MotorStepsToCartesian (in DDA::GetEndCoordinate) to set the directionVector value.)
2. Throw it away if there's no real movement.
3. Store some values (set some flags)
4. Normalise the direction vector and compute the amount of motion.
5. Compute the maximum acceleration available
6. Set the speed to the smaller of the requested and maximum speed.
7. Calculate the provisional accelerate and decelerate distances and the top speed
In the DDA code, the `endPoints` represents the machine coordinates (in int32) whereas the `endCoordinates` represents the cartesian real coordinates.
)
(Application entry point is in Task.cpp in function AppMain at l.127`)

### Preparation
A short while before the  movement described by a DDA is due to start, and after preparing all previous DDAs in the queue, a DDA is prepared for execution (`In Prepare function in DDA.cpp at l.1293. DDARing::Spin -> DDARing::PrepareMoves -> DDA::Prepare`). Once a DDA has been prepared, it cannot be altered, except that it may be possible to apply babystepping to it.
To prepare a DDA:

- The acceleration and deceleration phases of the move (if present) are planned by applying input shaping. This may split each acceleration or deceleration phase into multiple segments with different accelerations.

- A linked list of MoveSegment objects (`see DDA.shapedSegments, DDA.unshapedSegments`) is attached to each DDA. Each one describes (in Cartesian space always) an acceleration segment, the optional single steady speed segment, or a deceleration segment.

- A DM is attached to it for each set of local drives (`DDA.cpp l.1498`) that corresponds to a single machine axis or extruder (a delta tower is an example of a machine axis) (`see activeDMs, completedDMs`). Each DM points to the first MoveSegment (`DriveMovement.currentSegment`).

- Parameters are stored in the DM to facilitate step time calculation. Some of these parameters depend on the type of move, which is one of: Linear move (e.g. Cartesian machine axis), Delta move (i.e. delta printer tower), or  Linear move with Pressure Advance (i.e. extruder).  (`Check PrepareCartesianAxis in DriveMovement.cpp l.408 and PrepareExtruder l.630`)

- For each DM the total number of steps (`totalSteps in DDA.cpp l.1500`), initial direction (`direction DDA.cpp l.1499`), and time of the first step measured from the move start time (`nextStepTime  at the end of CalcNextStepTimeFull function in DriveMovement at l.1150. This function is called by CalcNextStepTime which is called at the end of PrepareCartesianAxis.`) are calculated.

- The DMs are then attached to the DDA as a linked list in step-time order (earliest step first). (`InsertDM call in DDA.cpp at l.1509 put the DM in the DDA.activeDMs queue list`)

- For drives moving that are attached via CAN, DMs are not created, instead the movement details are stored in CAN buffers (normally one  bufferper CAN address that has a moving drive). When preparation of the move is complete, these CAN buffers are transmitted, along with the time at which the move is due to start.
(`currentSegment is set to the next segment in DriveMovement.cpp CalcNextStepTimeFull l.912. This function computes the step times with maths formula (detailed in the onset of MoveSegment.h).`)

### Execution
When a move becomes due for execution, its actual start time is recorded in the DDA (`in DDA.cpp function DDA::Start (called by DDARing::StartNextMove called by DDARing::Spin at l.377)`). For each DM, the driver direction is set to the required direction for the first step (`DDA::Start l.1903 this where the DM information are sent to the Platform`). Then an interrupt is scheduled for the time at which the first step is required, as indicated in the first DM in the linked list (`DDARing::ScheduleNextStepInterrupt`).

When the interrupt occurs (`DDARing::Interrupt`), the ISR iterates through the DMs at the start of the linked list to identify the ones for which a step is due or almost due. It then generates steps for those drivers. During the step-high time it calculates for each of those DMs when the next step is due, and re-inserts them in the correct place in the linked list so as to keep the list in step-time order. Any DMs for which no further steps are due are moved to a separate linked list attached to the DDA (`DDA.completedDMs I guess`). Then it schedules the next interrupt according to the time indicated in the DM now at the head of the main list. If there are no active DMs left, it schedules the next move to start at the time at which the current move should finish.

### Recycling
The Move task goes works through the completed DDAs (`DDARing::RecycleDDAs?`). For each one it examines the DMs (which are now all in the completed list) for errors that need to be reported, then recycles the DMs. The DDA is then free to be re-used for another incoming move.

## Move segments

### Purpose
The purpose of a move segment is to represent a constant-acceleration part of a move. When input shaping is not being used, or DAA is being used, the most general type of move has one acceleration segment, one steady speed segment, and one deceleration segment. Some moves have only one or two of these segments.

When input shaping is used, each acceleration or deceleration segment is split into two to or more phases: two for ZV, three for ZVD, and four for ZVDD or EI2. This means that when using EI2 or ZVDD input shaping, there may be up to 9 move segments per DDA. Therefore the MoveSegment records are kept short and shared between all DMs.

The MoveSegment is designed to make it easy to compute the time at which a given fraction of the move has been completed. From this, the times of step pulses can be computed.
During an acceleration or deceleration segment, the calculation of the time at which a specified fraction of the move will be complete is the solution of this quadratic equation:
```
(s - s0) = u*(t - t_start) + 0.5*a*(t - t_start)t^2

If we write s = d * move_fraction (where d is the total length of the move)
and s0 = d * initial_move_fraction, it is therefore of this form:
t = sqrt(A + B * move_fraction) + C
where:
A = (u/a)^2 – B * initial_move_fraction
B = 2 * d/a
C = u/a + t_start.

The MoveSegment record holds the constants A, B and C
along with the fraction of the total distance at which this segment ends.

For a linear segment the equation is:
(s - s0) = u*(t - t_start)

and the solution is of the form:
t = B * move_fraction + C
where:
B = d/a
C = t_start – B * initial_move_fraction
```
In this case the MoveSegment stores constants B and C and once again the fraction of the total distance at which this segment ends. It also stores a flag to identify this as a linear segment.\
The fraction of the total move at which a segment starts is found from the ending distance fraction of the previous segment if there is one, and is zero for the first segment.

If the MCU has floating point hardware then all calculations are done in floating point arithmetic. The main reason for this is that the ARM M4F and M7 processors have a fast floating point square root instruction taking 14 clock cycles. Computing integer square roots takes much longer, even with the optimised integer square root function in RRFLibraries, especially as we usually need to use more than 32 bits because of the variation in printer size/resolution.

## Computing step pulse times

### Linear motion
This is the simplest case. The total steps needed for the entire move is recorded in the DM. To calculate the time of the next step, the firmware computes the corresponding movement fraction, which is (next_step_number/total_steps). Then it uses the current MoveSegment to compute the corresponding time since the start of the move.

To keep track of when to switch to the next MoveSegment, when starting a new one it precomputes the step number at which a switch to the next MoveSegmennt is needed, and stores this value in the DM.

### Delta motion
Step times for the motion of a carriage on a delta tower are computed in two phases:
1. Compute the fraction of the move that will be complete when the next step is due. This is the solution to a quadratic equation.
2. Use the current MoveSegment to compute the step time from that fraction.

A complication is that for some moves, the carriage moves first up and then down. In such cases there will be a reversal within a segment or possibly at a segment boundary. When starting a new MoveSegment, the firmware checks whether a reversal occurs within the segment, and if so sets a flag and stores the step number at which the reversal starts.

An alternative mechanism would be to check whether the operand of the square root in the solution to the quadratic equation is negative, signalling that reversal is needed.

### Extruder motion with pressure advance
This is probably the most complicated case. Using quadratic pressure advance, the extrusion distance is modified as follows:\
`e’ = e + k1*(v-u) + k2*(v-u)^2`

where e is the requested extrusion at the nozzle, e’ is the required motion at the extruder, u is the requested extrusion speed at the nozzle start of the move, and v is the instantaneous requested extrusion speed at the nozzle. Constant k2 is zero for linear pressure advance. The total extrusion distance (and hence the net number of steps taken) is also modified according to the above formula, substituting the ending requested extrusion velocity for v.

The motion equations are the same as for linear motion, except that the ABC constants are changed and a deceleration segment may reverse. There are a few options:

1. Use different MoveSegment objects for extruders, each one containing the correct constants for that extruder according to the pressure advance for that extruder. Multiple extruders using the same pressure advance values could share MoveSegment objects. Extruders using no pressure advance could share the axis MoveSegments.

2. As *1.* but don’t apply input shaping to extruder movements. This means that extruder motion will not track axis motion precisely during acceleration and deceleration segments; but it will use many fewer MoveSegment objects in systems with mixing extruders. Does it matter if the acceleration profile is not matched?

3. Convert the extrusion at the next step into distance fraction and use the common MoveSegments to work out the time. To do the conversion, first subtract the extra extrusion done at the start of the segment. This amount can be computed and stored in the DM when the segment is started. Then for an acceleration segment, we need to take account of the additional speed. Unfortunately this is not simple.

4. Compute corrections to the A, B and C values in the MoveSegment and use those corrected values in the step time calculation. The new ABC values for the current segment can be stored in the DM. This looks like a reasonable option if the ABC values stored in the MoveSegment plus the pressure advance constants and extruder move fraction are all we need to compute the corrected values.

The linear segment (if any) is the same as in the Linear case apart from the relationship between step number and distance moved.


## Entry points and Call tree
<details><summary>Show entry points and call tree in the firmware code</summary>

* `Task::AppMain` which create a `Task::MainTask` which call `RepRap::Spin` in an infinite loop.  
`RepRap::Spin` call multiple `Spin` function (not all of them!) such as `GCodes::Spin` and `Platform::Spin`.  

* The Move task starts executing at `Move::MoveStart` which calls `Move::Moveloop` and enters an infinite loop.  
`Move::MoveLoop` : Main loop called by the Move task.
    * `DDARing::AddStandardMove` : Add a new move, returning true if it represents real movement.
        * `DDA::InitStandardMove` : Set up a real move. Return true if it represents real movement, else false.
            - `Kinematics::CartesianToMotorSteps` : Convert Cartesian coordinates to motor positions measured in steps from reference position.
            - `Kinematics::MotorStepsToCartesian` : Convert motor positions (measured in steps from reference position) to Cartesian coordinates.
    * `DDARing::Spin` : Try to process moves in the ring. Called by the Move task.
        * `DDARing::PrepareMoves` : Prepare some moves.
            - `DDA::Prepare` : Prepare this DDA for execution.
                - `DriveMovement::PrepareCartesianAxis` : Prepare this DM for a Cartesian axis move, returning true if there are steps to do.
                - `DriveMovement::CalcNextStepTime` : Calculate and store the time since the start of the move when the next step for the specified DriveMovement is due.
        * `DDARing::StartNextMove` : Start the next move.
            - `DDA::Start` : Start executing this move.
        * `DDARing::ScheduleNextStepInterrupt` : Schedule the next step interrupt for this DDA ring.
        * `DDARing::Interrupt` : ISR for the step interrupt.
            - `DDARing::OnMoveCompleted` : This is called when the state has been set to 'completed'.
                - `DDARing::StartNextMove` : Start the next move.
</details>
