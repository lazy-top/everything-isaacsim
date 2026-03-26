# 1. 最重要的一步：在加载任何 Isaac Sim 模块前，设置 ROS_DOMAIN_ID！
import os
os.environ["ROS_DOMAIN_ID"] = "42"  # 假设你的 ROS 2 算法端 Domain ID 是 42
os.environ["RMW_IMPLEMENTATION"] = "rmw_fastrtps_cpp" # 推荐显式指定通信中间件

# 2. 启动 Isaac Sim
from isaacsim import SimulationApp

# 配置isaacsim应用参数
config = {
    "headless": False,
    # "hide_ui": True,

    "width": 1280,
    "height": 720,
}
# 启动isaacsim应用
simulation_app = SimulationApp(config)

# 3. 导入核心组件 (必须在 SimulationApp 启动后导入)
