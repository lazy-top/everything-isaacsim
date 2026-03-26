import os

# ============================================================
# 0) 环境变量：一定要在 SimulationApp 之前
# ============================================================
os.environ["ROS_DOMAIN_ID"] = os.environ.get("ROS_DOMAIN_ID", "10")
# 如果你在终端里已经 export 了，这里可以不再重复设置
# os.environ["FASTRTPS_DEFAULT_PROFILES_FILE"] = os.path.expanduser("~/.ros/fastdds.xml")

from isaacsim import SimulationApp

simulation_app = SimulationApp({
    "headless": False
})

# ============================================================
# 1) 启用扩展
# ============================================================
from omni.isaac.core.utils.extensions import enable_extension

enable_extension("isaacsim.ros2.bridge")
enable_extension("isaacsim.sensors.rtx")

# ============================================================
# 2) 常规导入
# ============================================================
import omni
import omni.graph.core as og
import omni.replicator.core as rep

from pxr import Gf

from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid
from omni.isaac.core.utils.prims import create_prim

# ============================================================
# 3) 参数区
# ============================================================
NAMESPACE = "robot1"
BASE_FRAME = "base_link"
LIDAR_FRAME = "lidar_link"
ODOM_FRAME = "odom"

SCAN_TOPIC = f"{NAMESPACE}/scan"
POINTCLOUD_TOPIC = f"{NAMESPACE}/point_cloud"
ODOM_TOPIC = f"{NAMESPACE}/odom"

WORLD_XFORM = "/World"
ROBOT_XFORM = f"{WORLD_XFORM}/{NAMESPACE}"
BASE_PRIM = f"{ROBOT_XFORM}/{BASE_FRAME}"
LIDAR_PRIM = f"{BASE_PRIM}/{LIDAR_FRAME}"

USE_LASERSCAN = True
USE_POINTCLOUD = True

# ============================================================
# 4) 构建基础场景
# ============================================================
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

# 机器人根
create_prim(ROBOT_XFORM, "Xform", translation=(0.0, 0.0, 0.0))
create_prim(BASE_PRIM, "Xform", translation=(0.0, 0.0, 0.20))
create_prim(LIDAR_PRIM, "Xform", translation=(0.2, 0.0, 0.25))

# 放几个障碍物，方便直接看 scan / cloud
world.scene.add(
    DynamicCuboid(
        prim_path="/World/obstacle_1",
        name="obstacle_1",
        position=[3.0, 0.0, 0.5],
        scale=[1.0, 1.0, 1.0],
        color=[1.0, 0.0, 0.0],
    )
)
world.scene.add(
    DynamicCuboid(
        prim_path="/World/obstacle_2",
        name="obstacle_2",
        position=[2.0, 2.0, 0.5],
        scale=[0.6, 0.6, 1.0],
        color=[0.0, 1.0, 0.0],
    )
)
world.scene.add(
    DynamicCuboid(
        prim_path="/World/obstacle_3",
        name="obstacle_3",
        position=[2.5, -1.5, 0.5],
        scale=[0.8, 0.8, 1.0],
        color=[0.0, 0.0, 1.0],
    )
)

# ============================================================
# 5) 创建 RTX LiDAR
#    2D: Example_Rotary_2D -> LaserScan
#    3D: Example_Rotary    -> PointCloud2
# ============================================================
lidar_prim_for_scan = None
lidar_prim_for_cloud = None
render_product_scan = None
render_product_cloud = None

if USE_LASERSCAN:
    _, lidar_prim_for_scan = omni.kit.commands.execute(
        "IsaacSensorCreateRtxLidar",
        path=f"{LIDAR_PRIM}/lidar_2d",
        parent=None,
        config="Example_Rotary_2D",
        translation=(0.0, 0.0, 0.0),
        orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
    )

    render_product_scan = rep.create.render_product(
        lidar_prim_for_scan.GetPath(),
        [1, 1],
        name="Isaac"
    )

if USE_POINTCLOUD:
    _, lidar_prim_for_cloud = omni.kit.commands.execute(
        "IsaacSensorCreateRtxLidar",
        path=f"{LIDAR_PRIM}/lidar_3d",
        parent=None,
        config="Example_Rotary",
        translation=(0.0, 0.0, 0.0),
        orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
    )

    render_product_cloud = rep.create.render_product(
        lidar_prim_for_cloud.GetPath(),
        [1, 1],
        name="Isaac"
    )

# ============================================================
# 6) 通过 ROS2 bridge writer 发布 LiDAR 数据
# ============================================================
if USE_LASERSCAN:
    scan_writer = rep.writers.get("RtxLidarROS2PublishLaserScan")
    scan_writer.initialize(
        topicName=SCAN_TOPIC,
        frameId=LIDAR_FRAME
    )
    scan_writer.attach([render_product_scan])

if USE_POINTCLOUD:
    pc_writer = rep.writers.get("RtxLidarROS2PublishPointCloud")
    pc_writer.initialize(
        topicName=POINTCLOUD_TOPIC,
        frameId=LIDAR_FRAME
    )
    pc_writer.attach([render_product_cloud])

# ============================================================
# 7) 创建 Action Graph:
#    - /clock
#    - TF tree
#    - odom -> base_link raw TF
#    - odom topic
#
# 注意：
# 这里使用 OmniGraph 节点名。不同版本 Isaac Sim 个别节点名
# 可能会有小变化，但整体思路是一致的。
# ============================================================
GRAPH_PATH = "/ActionGraph/ROS2BridgeGraph"

(keys, (graph, nodes, _, _)) = og.Controller.edit(
    {"graph_path": GRAPH_PATH, "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),

            # ROS2 Context：如需显式写死 domain id，可取消 useDomainIDEnvVar
            ("ROS2Context", "isaacsim.ros2.bridge.ROS2Context"),

            # /clock
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),

            # 发布机器人和传感器 TF tree
            ("PublishTF", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),

            # 里程计计算与发布
            ("ComputeOdom", "isaacsim.core.nodes.IsaacComputeOdometry"),
            ("PublishOdom", "isaacsim.ros2.bridge.ROS2PublishOdometry"),
            ("PublishRawTF", "isaacsim.ros2.bridge.ROS2PublishRawTransformTree"),
        ],

        og.Controller.Keys.CONNECT: [
            # Tick -> 所有执行节点
            ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "PublishTF.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "ComputeOdom.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "PublishOdom.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "PublishRawTF.inputs:execIn"),

            # Sim Time -> timestamp
            ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
            ("ReadSimTime.outputs:simulationTime", "PublishTF.inputs:timeStamp"),
            ("ReadSimTime.outputs:simulationTime", "PublishOdom.inputs:timeStamp"),
            ("ReadSimTime.outputs:simulationTime", "PublishRawTF.inputs:timeStamp"),

            # ROS2 Context -> 各 ROS2 节点
            ("ROS2Context.outputs:context", "PublishClock.inputs:context"),
            ("ROS2Context.outputs:context", "PublishTF.inputs:context"),
            ("ROS2Context.outputs:context", "PublishOdom.inputs:context"),
            ("ROS2Context.outputs:context", "PublishRawTF.inputs:context"),

            # odometry 计算输出 -> 发布 odom
            ("ComputeOdom.outputs:position", "PublishOdom.inputs:position"),
            ("ComputeOdom.outputs:orientation", "PublishOdom.inputs:orientation"),
            ("ComputeOdom.outputs:linearVelocity", "PublishOdom.inputs:linearVelocity"),
            ("ComputeOdom.outputs:angularVelocity", "PublishOdom.inputs:angularVelocity"),

            # odometry 计算输出 -> 发布 odom->base_link raw tf
            ("ComputeOdom.outputs:position", "PublishRawTF.inputs:translation"),
            ("ComputeOdom.outputs:orientation", "PublishRawTF.inputs:rotation"),
        ],

        og.Controller.Keys.SET_VALUES: [
            # 1) ROS2Context
            # 默认取环境变量；若你要显式指定 domain，可把下面两行改成 False 和 10
            ("ROS2Context.inputs:useDomainIDEnvVar", True),

            # 2) /clock
            # /clock 一般不加 namespace，方便 use_sim_time 节点直接订阅
            ("PublishClock.inputs:topicName", "clock"),

            # 3) TF Tree
            # 这里把 base_link 和 lidar_link 都挂进 TF tree
            ("PublishTF.inputs:topicName", "tf"),
            ("PublishTF.inputs:parentPrim", WORLD_XFORM),
            ("PublishTF.inputs:targetPrims", [BASE_PRIM, LIDAR_PRIM]),

            # 4) Compute Odometry
            # 这里把底盘 prim 作为 chassis
            ("ComputeOdom.inputs:chassisPrim", BASE_PRIM),

            # 5) Publish Odometry
            ("PublishOdom.inputs:topicName", ODOM_TOPIC),
            ("PublishOdom.inputs:chassisFrameId", BASE_FRAME),
            ("PublishOdom.inputs:odomFrameId", ODOM_FRAME),

            # 6) Publish Raw TF: odom -> base_link
            ("PublishRawTF.inputs:topicName", "tf"),
            ("PublishRawTF.inputs:parentFrameId", ODOM_FRAME),
            ("PublishRawTF.inputs:childFrameId", BASE_FRAME),
        ],
    },
)

# ============================================================
# 8) 可选：如果你想把整个 robot 的 ROS 图都挂到 namespace 下
#    有些版本节点支持 nodeNamespace / namespace 输入；有些不支持。
#    下面用 try/except 做兼容尝试。
# ============================================================
def try_set_attr(attr_path, value):
    try:
        og.Controller.set(og.Controller.attribute(attr_path), value)
        print(f"[OK] set {attr_path} = {value}")
    except Exception:
        print(f"[WARN] attribute not supported in this Isaac Sim version: {attr_path}")

try_set_attr(f"{GRAPH_PATH}/PublishClock.inputs:nodeNamespace", "")
try_set_attr(f"{GRAPH_PATH}/PublishTF.inputs:nodeNamespace", NAMESPACE)
try_set_attr(f"{GRAPH_PATH}/PublishOdom.inputs:nodeNamespace", NAMESPACE)
try_set_attr(f"{GRAPH_PATH}/PublishRawTF.inputs:nodeNamespace", NAMESPACE)

# ============================================================
# 9) 可选：如果要显式固定 domain id，而不是取环境变量
# ============================================================
EXPLICIT_DOMAIN_ID = None  # 例如改成 10

if EXPLICIT_DOMAIN_ID is not None:
    try_set_attr(f"{GRAPH_PATH}/ROS2Context.inputs:useDomainIDEnvVar", False)
    try_set_attr(f"{GRAPH_PATH}/ROS2Context.inputs:domain_id", EXPLICIT_DOMAIN_ID)

# ============================================================
# 10) 初始化并运行
# ============================================================
world.reset()

# 先预热几帧
for _ in range(20):
    world.step(render=True)

print("=" * 80)
print("Isaac Sim standalone ROS2 bridge started")
print(f"ROS_DOMAIN_ID = {os.environ.get('ROS_DOMAIN_ID')}")
print(f"Namespace     = /{NAMESPACE}")
print(f"Scan topic     = /{SCAN_TOPIC}" if USE_LASERSCAN else "Scan disabled")
print(f"PointCloud     = /{POINTCLOUD_TOPIC}" if USE_POINTCLOUD else "PointCloud disabled")
print(f"Odom topic     = /{ODOM_TOPIC}")
print("Clock topic    = /clock")
print("TF topics      = /tf, /tf_static")
print("=" * 80)

# 演示：让 base_link 缓慢前进，便于 odom / tf / slam 联调
x = 0.0
while simulation_app.is_running():
    x += 0.002

    # 让机器人底盘沿 x 正方向缓慢移动
    prim = omni.usd.get_context().get_stage().GetPrimAtPath(BASE_PRIM)
    xform = omni.usd.get_world_transform_matrix(prim)
    # 这里直接修改 prim 的平移更简单
    omni.kit.commands.execute(
        "TransformPrimSRT",
        path=BASE_PRIM,
        new_translation=(x, 0.0, 0.20),
        new_rotation_euler=(0.0, 0.0, 0.0),
        new_scale=(1.0, 1.0, 1.0),
        old_translation=None,
        old_rotation_euler=None,
        old_scale=None,
    )

    world.step(render=True)

simulation_app.close()
