# ==========================================
# 1. 绝对铁律：启动引擎前设置 ROS 通信频段！
# ==========================================
import os
os.environ["ROS_DOMAIN_ID"] = "42"  # 设定你们的秘密通讯频道为 42
os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp"

# 2. 启动 Isaac Sim 游戏引擎
from isaacsim import SimulationApp
simulation_app = SimulationApp({"headless": False}) # 必须为 False 才能进行图像渲染

# 3. 导入核心组件
import omni
import omni.kit.commands
import numpy as np
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core.utils.rotations import euler_angles_to_quat

# 4. 强制开启 ROS 2 桥接插件
enable_extension("omni.isaac.ros2_bridge")

# ⚠️ 导入极其好用的相机直播车类 (必须在启用 extension 后导入)
from omni.isaac.ros2_bridge import ROS2CameraHelper

def main():
    # 初始化物理世界
    world = World(stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    # ==========================================
    # 步骤 A：布置舞台 (放一个红色的方块当演员)
    # ==========================================
    cube = world.scene.add(
        DynamicCuboid(
            prim_path="/World/Cube", 
            position=[2.0, 0.0, 0.5], # 放在相机正前方 2 米处
            scale=[0.5, 0.5, 0.5], 
            color=np.array([1.0, 0.0, 0.0]) # 鲜艳的红色
        )
    )

    # ==========================================
    # 步骤 B：架设物理相机 (Camera Prim)
    # ==========================================
    camera_path = "/World/MyCamera"
    
    # 1. 在虚拟空间中凭空捏造出一个相机设备
    omni.kit.commands.execute(
        "CreatePrimWithDefaultXform",
        prim_type="Camera",
        prim_path=camera_path,
        attributes={
            "focusDistance": 400.0, # 对焦距离
            "focalLength": 24.0,    # 焦距 (24mm 广角视野较好)
            "clippingRange": (0.1, 10000.0) # 剪裁范围：太近或太远的东西不画
        }
    )
    
    # 2. 调整相机的位置和姿态 (把它架设在原点，离地 0.5 米，看向前方)
    # rotation参数：(x(滚转), y(俯仰), z(偏航))，单位是度
    omni.kit.commands.execute(
        "TransformPrimSRT", 
        path=camera_path, 
        translation=(0.0, 0.0, 0.5), 
        rotation=(0.0, 0.0, 0.0)
    )

    # ==========================================
    # 步骤 C：接通 ROS 2 直播信号 (ROS2CameraHelper)
    # ==========================================
    # 这个 Helper 在后台自动帮你画了极其复杂的数据流图(OmniGraph)
    camera_helper = ROS2CameraHelper(
        prim_path=camera_path,            # 信号源：绑定刚才建的物理相机
        node_namespace="/robot",          # ROS 命名空间
        node_name="front_camera_node",    # ROS 节点名
        topic_name="image_raw",           # 最终发布的图像话题名 (完整路径会变成 /robot/image_raw)
        type="rgb",                       # 画面类型：彩色图像 (如果是 depth 就是深度图)
        reset_cg=True
    )

    print("\n[INFO] 🎬 摄影棚准备完毕！")
    print(f"[INFO] 📡 Domain ID 锁定为: {os.environ['ROS_DOMAIN_ID']}")
    print("[INFO] 📷 正在向 ROS 2 话题发布彩色画面: /robot/image_raw")
    print("[INFO] ℹ️  正在同步发布相机内参: /robot/camera_info\n")

    # ==========================================
    # 步骤 D：开机，Action！(运行仿真循环)
    # ==========================================
    world.reset()
    while simulation_app.is_running():
        # 让红方块持续原地旋转，制造动态画面
        cube.set_local_pose(
            translation=[2.0, 0.0, 0.5], 
            # 让 Z 轴随时间旋转
            orientation=euler_angles_to_quat([0, 0, world.current_time * 2.0]) 
        )
        
        # 推进物理和渲染时间 (render=True 必须开启，否则相机截取不到画面)
        world.step(render=True)

    # 杀青清理
    simulation_app.close()

if __name__ == "__main__":
    main()
