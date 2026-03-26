import omni.kit.commands
import omni.graph.core as og

class ROS2Lidar:
    """
    高度模块化的 ROS 2 激光雷达组件
    """
    def __init__(self, prim_path: str, position: list, topic_name: str = "/lidar/point_cloud"):
        self.prim_path = prim_path
        self.topic_name = topic_name
        
        # 1. 创建物理雷达
        omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path=self.prim_path,
            parent="/World",
            config="Example_Rotary", 
            translation=position,
            orientation=(1.0, 0.0, 0.0, 0.0),
        )

        # 2. 动态创建这颗雷达专属的 OmniGraph 数据流
        # 注意：这里我们用 prim_path 拼出独一无二的 graph_path，防止多个雷达的“水管”串接在一起！
        graph_path = f"{self.prim_path}_ROS2_Graph"
        
        og.Controller.edit(
            {"graph_path": graph_path, "evaluator_name": "execution"},
            {
                og.Controller.Keys.CREATE_NODES: [
                    ("Tick", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                    ("ComputePointCloud", "omni.isaac.sensor.IsaacComputeRTXLidarPointCloud"),
                    ("PublishPointCloud", "omni.isaac.ros2_bridge.ROS2PublishPointCloud"),
                ],
                og.Controller.Keys.CONNECT: [
                    ("Tick.outputs:step", "ComputePointCloud.inputs:execIn"),
                    ("ComputePointCloud.outputs:execOut", "PublishPointCloud.inputs:execIn"),
                    ("Tick.outputs:systemTime", "PublishPointCloud.inputs:timeStamp"),
                    ("ComputePointCloud.outputs:pointCloudData", "PublishPointCloud.inputs:pointCloudData"),
                ],
                og.Controller.Keys.SET_VALUES: [
                    ("ComputePointCloud.inputs:renderProductPath", [self.prim_path]), 
                    ("PublishPointCloud.inputs:topicName", self.topic_name),
                    ("PublishPointCloud.inputs:frameId", self.prim_path.split("/")[-1]), # 动态使用节点名作为 TF 坐标系
                ],
            },
        )
        print(f"[✅ Lidar] 已挂载至 {self.prim_path}，正在向 ROS 2 发布: {self.topic_name}")
