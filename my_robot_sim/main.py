import os

# 1. 绝对铁律：设置 Domain ID 和通信后端
os.environ["ROS_DOMAIN_ID"] = "42"
os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"

from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": False}) 

# 2. 导入组件
from omni.isaac.core import World
from omni.isaac.core.utils.extensions import enable_extension

# 启用必要的官方插件
enable_extension("omni.isaac.ros2_bridge")

# ⚠️ 导入我们新写的执行器模块
from actuators.robot_base import ROS2WheeledRobot

def main():
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    print("\n--- 开始部署机器人 ---")
    
    # 实例化我们的机器人，并告诉它监听 "/joint_commands" 话题
    my_robot = ROS2WheeledRobot(
        prim_path="/World/Jetbot", 
        position=[0.0, 0.0, 0.05], # 放在地面上
        topic_name="/joint_commands"
    )
    
    print("--- 部署完毕 ---\n")

    # 3. 极其重要的一步：让物理引擎解析机器人的驱动链
    # 因为我们动态加载了一个复杂的 USD，必须调用 reset() 唤醒它的物理关节
    world.reset()

    # 4. 运行仿真循环
    print("[INFO] 等待 ROS 2 发送速度指令...")
    while simulation_app.is_running():
        world.step(render=True)

    simulation_app.close()

if __name__ == "__main__":
    main()
