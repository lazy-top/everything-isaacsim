import os

# -----------------------------
# 1) 这些环境变量要在 SimulationApp 之前设置
# -----------------------------
os.environ["ROS_DOMAIN_ID"] = "10"   # 和你的 ROS2 算法端保持一致
# 如果你已在外部终端 export，这里也可以不写
# os.environ["FASTRTPS_DEFAULT_PROFILES_FILE"] = os.path.expanduser("~/.ros/fastdds.xml")

from isaacsim import SimulationApp

simulation_app = SimulationApp({
    "headless": False
})

# -----------------------------
# 2) 启用扩展
# -----------------------------
from omni.isaac.core.utils.extensions import enable_extension

enable_extension("isaacsim.ros2.bridge")
enable_extension("isaacsim.sensors.rtx")

# -----------------------------
# 3) 常规导入
# -----------------------------
import omni
import omni.replicator.core as rep
from pxr import Gf, UsdGeom

from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.utils.prims import create_prim

# -----------------------------
# 4) 创建场景
# -----------------------------
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

# 放一个障碍物，方便雷达扫到
cube = world.scene.add(
    DynamicCuboid(
        prim_path="/World/obstacle_cube",
        name="obstacle_cube",
        position=[3.0, 0.0, 0.5],
        scale=[1.0, 1.0, 1.0],
        color=[1.0, 0.0, 0.0],
    )
)

# 传感器挂载点
create_prim("/World/LidarRig", "Xform", translation=(0.0, 0.0, 1.0))

# -----------------------------
# 5) 创建 2D RTX LiDAR -> 发布 LaserScan
# -----------------------------
_, lidar_2d = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/World/LidarRig/lidar_2d",
    parent=None,
    config="Example_Rotary_2D",
    translation=(0.0, 0.0, 0.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
)

render_product_2d = rep.create.render_product(
    lidar_2d.GetPath(),
    [1, 1],
    name="Isaac"
)

laser_writer = rep.writers.get("RtxLidarROS2PublishLaserScan")
laser_writer.initialize(
    topicName="scan",
    frameId="lidar_2d_frame"
)
laser_writer.attach([render_product_2d])

# -----------------------------
# 6) 创建 3D RTX LiDAR -> 发布 PointCloud2
# -----------------------------
_, lidar_3d = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/World/LidarRig/lidar_3d",
    parent=None,
    config="Example_Rotary",
    translation=(0.0, 0.0, 0.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
)

render_product_3d = rep.create.render_product(
    lidar_3d.GetPath(),
    [1, 1],
    name="Isaac"
)

pc_writer = rep.writers.get("RtxLidarROS2PublishPointCloud")
pc_writer.initialize(
    topicName="point_cloud",
    frameId="lidar_3d_frame"
)
pc_writer.attach([render_product_3d])

# -----------------------------
# 7) 运行仿真
# -----------------------------
world.reset()

# 先跑几帧让传感器和 bridge 稳定起来
for _ in range(10):
    world.step(render=True)

print("RTX LiDAR ROS2 publishers are running...")
print("ROS_DOMAIN_ID =", os.environ.get("ROS_DOMAIN_ID"))

while simulation_app.is_running():
    world.step(render=True)

simulation_app.close()
