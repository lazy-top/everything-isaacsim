import os

# 如果你需要固定 Domain ID，可以在这里指定
os.environ["ROS_DOMAIN_ID"] = os.environ.get("ROS_DOMAIN_ID", "10")

from isaacsim import SimulationApp

simulation_app = SimulationApp({
    "headless": False
})

# 启用 ROS2 bridge
from omni.isaac.core.utils.extensions import enable_extension
enable_extension("isaacsim.ros2.bridge")

import omni.graph.core as og
from omni.isaac.core import World

# 创建一个简单世界，保证仿真可以正常 step
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

GRAPH_PATH = "/ActionGraph"

og.Controller.edit(
    {"graph_path": GRAPH_PATH, "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("Context", "isaacsim.ros2.bridge.ROS2Context"),
            ("PublishClock", "isaacsim.ros2.bridge.ROS2PublishClock"),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
            ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
            ("Context.outputs:context", "PublishClock.inputs:context"),
        ],
        og.Controller.Keys.SET_VALUES: [
            # /clock 建议保持全局，不要加 namespace
            ("PublishClock.inputs:topicName", "clock"),

            # 默认可以直接使用环境变量 ROS_DOMAIN_ID
            ("Context.inputs:useDomainIDEnvVar", True),

            # 如果你想写死 domain id，则改成：
            # ("Context.inputs:useDomainIDEnvVar", False),
            # ("Context.inputs:domain_id", 10),
        ],
    },
)

world.reset()

print("ROS2 clock publisher started.")
print("Publishing topic: /clock")
print("ROS_DOMAIN_ID =", os.environ.get("ROS_DOMAIN_ID"))

while simulation_app.is_running():
    world.step(render=True)

simulation_app.close()
