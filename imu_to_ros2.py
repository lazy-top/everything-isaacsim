# 1. 最重要的一步：在加载任何 Isaac Sim 模块前，设置 ROS_DOMAIN_ID！
import os
os.environ["ROS_DOMAIN_ID"] = "42"  # 假设你的 ROS 2 算法端 Domain ID 是 42
os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp" # 推荐显式指定通信中间件

# 2. 启动 Isaac Sim
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": False}) # headless=False 会显示图形界面

# 3. 导入核心组件 (必须在 SimulationApp 启动后导入)
import omni
import omni.graph.core as og
import omni.kit.commands
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid
from omni.isaac.core.utils.extensions import enable_extension

# 4. 强制启用 ROS 2 桥接插件
enable_extension("omni.isaac.ros2_bridge")

def main():
    # 创建物理世界
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    # 步骤 A: 创建一个可以掉落的方块（作为 IMU 的载体）
    # 为什么用方块？因为物体在自由落体和砸到地板时，IMU 的加速度数据会发生剧烈变化，方便我们验证！
    cube_path = "/World/Cube"
    cube = world.scene.add(
        DynamicCuboid(
            prim_path=cube_path,
            name="my_cube",
            position=[0, 0, 5.0], # 把它挂在 5 米高的地方
            scale=[0.5, 0.5, 0.5],
            color=[1.0, 0.0, 0.0], # 红色
        )
    )

    # 步骤 B: 在方块内部创建一个 IMU 传感器
    imu_path = f"{cube_path}/IMU_Sensor"
    # 使用底层命令创建 IMU
    omni.kit.commands.execute(
        "IsaacSensorCreateImuSensor",
        path=imu_path,
        parent=cube_path,
        translation=(0, 0, 0), # 放在方块的正中心
        orientation=(1, 0, 0, 0),
    )

    # 步骤 C: 构建 OmniGraph ("接水管")
    # 我们需要 3 个节点：触发器(Tick) -> 读取IMU(ReadIMU) -> 发布到ROS2(PublishIMU)
    graph_path = "/World/IMU_ROS2_Graph"
    keys = og.Controller.Keys
    
    og.Controller.edit(
        {"graph_path": graph_path, "evaluator_name": "execution"},
        {
            # 1. 声明需要的节点
            keys.CREATE_NODES: [
                ("Tick", "omni.isaac.core_nodes.IsaacReadSimulationTime"), # 提供系统时间和执行触发脉冲
                ("ReadIMU", "omni.isaac.sensor.IsaacReadIMU"),              # 读取 IMU 数据
                ("PublishIMU", "omni.isaac.ros2_bridge.ROS2PublishImu"),    # 发送 ROS 2 消息
            ],
            # 2. 连接节点的执行流 (Exec) 和 数据流 (Data)
            keys.CONNECT: [
                # 执行流：滴答 -> 读取 -> 发布
                ("Tick.outputs:step", "ReadIMU.inputs:execIn"),
                ("ReadIMU.outputs:execOut", "PublishIMU.inputs:execIn"),
                
                # 数据流：把读取到的 IMU 物理数据 接入到 ROS 2 发布节点
                ("ReadIMU.outputs:linAcc", "PublishIMU.inputs:linearAcceleration"), # 线加速度
                ("ReadIMU.outputs:angVel", "PublishIMU.inputs:angularVelocity"),    # 角速度
                ("ReadIMU.outputs:orientation", "PublishIMU.inputs:orientation"),   # 姿态(四元数)
                
                # 把仿真时间作为 ROS 消息的时间戳
                ("Tick.outputs:systemTime", "PublishIMU.inputs:timeStamp"),
            ],
            # 3. 设置节点的初始参数
            keys.SET_VALUES: [
                ("ReadIMU.inputs:imuPrim", [imu_path]),      # 告诉读取节点：去读哪个 IMU 设备？
                ("PublishIMU.inputs:topicName", "/imu/data"),# ROS 2 的话题名称
                ("PublishIMU.inputs:frameId", "imu_link"),   # ROS 2 消息中的 TF 坐标系名称
            ],
        },
    )

    print("\n[INFO] 🚀 仿真世界已准备就绪！")
    print("[INFO] 📦 红色方块即将从 5 米高空坠落...")
    print(f"[INFO] 📡 正在 Domain {os.environ['ROS_DOMAIN_ID']} 上向话题 '/imu/data' 发布数据\n")

    # 步骤 D: 运行仿真循环
    world.reset()
    while simulation_app.is_running():
        # 推进物理仿真时间，此时 OmniGraph 会自动触发，将数据发给 ROS 2
        world.step(render=True) 

    # 退出清理
    simulation_app.close()

if __name__ == "__main__":
    main()
