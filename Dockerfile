# ROS 2 Jazzy (Ubuntu 24.04) with Gazebo Harmonic through the ros_gz packages.
FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-ros-gz \
        ros-jazzy-launch-testing-ros \
        python3-pytest \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws
COPY src/ src/
RUN . /opt/ros/jazzy/setup.sh && colcon build --symlink-install

# Every shell in the container gets ROS 2 and the workspace on its path.
RUN echo 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash' >> /root/.bashrc
CMD ["bash"]
