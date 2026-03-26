import os
import numpy as np

# ==========================================
# 极其重要的第一步：设置环境与启动引擎！
# ==========================================
os.environ["ROS_DOMAIN_ID"] = "42"
os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"

from isaacsim import SimulationApp
# 必须先实例化 SimulationApp，然后才能 import 我们自己写的模块！
simulation_app = SimulationApp({"headless": False}) 

# ==========================================
# 第二步：引擎启动后，再导入相关的组件
# ==========================================
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid
from omni.isaac.core.utils.extensions import enable_extension

# 启用必要的官方插件
enable_extension("omni.isaac.ros2_bridge")
enable_extension("omni.sensors.nv.lidar")

# ⚠️ 此时再导入我们自己写的传感器模块，绝对安全！
from sensors.camera_sensor import ROS2Camera
from sensors.lidar_sensor import ROS2Lidar

def main():
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    # 1. 搭建测试场景 (扔个演员进去)
    cube = world.scene.add(DynamicCuboid(
        prim_path="/World/Cube", position=[3, 0, 1], scale=[0.5, 0.5, 0.5], color=np.array([1, 0, 0])
    ))

    # ==========================================
    # 2. 模块化的高光时刻：一键组装传感器！
    # ==========================================
    print("\n--- 开始挂载传感器 ---")
    
    # 实例化一个前置摄像头
    front_camera = ROS2Camera(
        prim_path="/World/Robot/FrontCamera", 
        position=[0, -2, 2], 
        topic_name="/front_camera/image"
    )

    # 实例化一个顶部激光雷达
    top_lidar = ROS2Lidar(
        prim_path="/World/Robot/TopLidar", 
        position=[0, 0, 2.5], 
        topic_name="/top_lidar/points"
    )
    
    # 如果你多有钱，想再装一个后置摄像头？只需再加一行代码！不会有任何冲突！
    # back_camera = ROS2Camera("/World/Robot/BackCamera", position=[0, 2, 2], topic_name="/back_camera/image")
    
    print("--- 传感器组装完毕 ---\n")

    # 3. 运行仿真引擎
    world.reset()
    while simulation_app.is_running():
        # 让方块旋转，制造动态画面
        cube.set_local_pose(translation=[3, 0, 1], orientation=omni.isaac.core.utils.rotations.euler_angles_to_quat([0, 0, world.current_time * 2]))
        world.step(render=True)

    simulation_app.close()

if __name__ == "__main__":
    main()
