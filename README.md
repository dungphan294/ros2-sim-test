# ros2-sim-test

A small two-wheeled robot in Gazebo that has to stop before a wall, plus an automated test that
checks it does. The test runs headless in Docker, so the same check runs on a laptop and in
GitHub Actions on every push.

Stack: ROS 2 Jazzy, Gazebo Harmonic, Python (`rclpy`), `launch_testing`, Docker, GitHub Actions.

## What is in it

```
Dockerfile                         Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic, builds the package
src/sim_test/
  worlds/wall_world.sdf            floor, a wall at x = 3 m, the robot (diff drive + front lidar)
  sim_test/safety_stop.py          node: drive forward, stop when the lidar sees < stop_distance
  launch/sim.launch.py             starts Gazebo, the ROS 2 <-> Gazebo bridge and safety_stop
  test/test_stops_before_wall.py   regression test
.github/workflows/sim-test.yml     CI: build the image, run the test
```

How the parts talk:

```
Gazebo  --/scan (lidar)-------->  safety_stop  --/cmd_vel (speed)-->  Gazebo (DiffDrive)
Gazebo  --/ground_truth (pose)->  test: did the robot move, stop, and stay clear of the wall?
```

## Run it

```bash
docker build -t ros2-sim-test .
docker run --rm ros2-sim-test bash -c 'source /ws/install/setup.bash && colcon test --packages-select sim_test && colcon test-result --verbose'
```

Run the same test with a bug on purpose (stop distance 5 cm) and watch it fail:

```bash
docker run --rm ros2-sim-test bash -c 'source /ws/install/setup.bash && launch_test /ws/src/sim_test/test/test_stops_before_wall.py stop_distance:=0.05'
```

Results on my machine (Apple Silicon, Docker, software rendering):

| Run | Final x | Gap to wall | Result |
|---|---|---|---|
| `stop_distance` 0.5 m | 2.28 m | 0.42 m | pass |
| `stop_distance` 0.05 m | 2.73 m | touching | fail: "robot got within 10 cm of the wall" |

## What the test checks

After 15 s of simulated time, on the simulator's true pose:

1. the robot moved more than 1 m (a robot that never starts does not pass),
2. its front is more than 10 cm from the wall,
3. it has stopped (speed under 0.02 m/s).

## Two things I learned building it

**Wheel odometry is not the truth.** The first version of the test read `/odom`, which the drive
plugin computes from wheel rotation. With the bug, the robot hit the wall and the wheels kept
spinning, so `/odom` reported x = 4.47 m: through a wall at 2.9 m. The test now reads
`/ground_truth`, the pose the simulator knows. A real robot has no ground truth, which is one
reason simulation is useful for testing.

**A leftover simulator gives a false pass.** Running the broken test right after the normal one
in the same container passed, with exactly the same numbers. `gz sim` had survived the first
launch, and the second test read the old simulation. The launch file now stops Gazebo on shutdown,
and CI runs every test in a fresh container.

## Next steps

- More scenarios as separate tests: obstacle at an angle, a gap the robot fits through, a moving
  obstacle.
- Record each run with `ros2 bag` and keep it as a CI artifact when a test fails.
- Swap the hand-written controller for Nav2 and test navigation to a goal.
- Viewing the Gazebo window (`gui:=true`) from Docker on macOS is not set up yet.
