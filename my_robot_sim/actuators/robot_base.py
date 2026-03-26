import omni.graph.core as og
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.robots import Robot

class ROS2WheeledRobot:
    """
    高度模块化的 ROS 2 轮式机器人底盘接收组件
    """
    def __init__(self, prim_path: str, position: list, topic_name: str = "/joint_commands"):
        self.prim_path = prim_path
        self.topic_name = topic_name
        
        # 1. 获取 NVIDIA 官方服务器上的标准机器人模型 (Jetbot)
        # 为什么不自己画方块？因为物理车轮需要极其复杂的摩擦力、碰撞体和驱动链(Articulation)设置。
        # 使用官方模型是最稳妥的做法。Jetbot 有两个关节：left_wheel_joint 和 right_wheel_joint
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            raise Exception("无法连接到 Omniverse Nucleus 服务器，请检查网络！")
        
        jetbot_usd_path = assets_root_path + "/Isaac/Robots/Jetbot/jetbot.usd"

        # 2. 将机器人加载到物理世界中
        self.robot = Robot(
            prim_path=self.prim_path,
            name="my_jetbot",
            usd_path=jetbot_usd_path,
            position=position
        )

        # 3. 动态搭建“接收指令 -> 驱动马达”的神经反射弧 (OmniGraph)
        graph_path = f"{self.prim_path}_ROS2_Control_Graph"
        
        og.Controller.edit(
            {"graph_path": graph_path, "evaluator_name": "execution"},
            {
                # 创建三个关键节点
                og.Controller.Keys.CREATE_NODES: [
                    ("Tick", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                    ("SubscribeJointState", "omni.isaac.ros2_bridge.ROS2SubscribeJointState"), # 接收器
                    ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"), # 肌肉控制器
                ],
                # 连接数据流
                og.Controller.Keys.CONNECT: [
                    # 执行流：滴答 -> 接收 -> 控制
                    ("Tick.outputs:step", "SubscribeJointState.inputs:execIn"),
                    ("SubscribeJointState.outputs:execOut", "ArticulationController.inputs:execIn"),
                    
                    # 核心数据流：把收到的 ROS 指令，直接插到肌肉控制器上
                    ("SubscribeJointState.outputs:jointNames", "ArticulationController.inputs:jointNames"),
                    ("SubscribeJointState.outputs:positionCommand", "ArticulationController.inputs:positionCommand"),
                    ("SubscribeJointState.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
                    ("SubscribeJointState.outputs:effortCommand", "ArticulationController.inputs:effortCommand"),
                ],
                # 设置参数
                og.Controller.Keys.SET_VALUES: [
                    ("SubscribeJointState.inputs:topicName", self.topic_name), # 监听的 ROS 2 话题
                    ("ArticulationController.inputs:targetPrim", [self.prim_path]), # 告诉肌肉控制器：你去驱动哪个机器人？
                ],
            },
        )
        print(f"[✅ Robot] 机器人已部署至 {self.prim_path}，正在监听 ROS 2 指令: {self.topic_name}")
