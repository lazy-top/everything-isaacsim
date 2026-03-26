import omni.kit.commands
from omni.isaac.ros2_bridge import ROS2CameraHelper

class ROS2Camera:
    """
    高度模块化的 ROS 2 相机组件
    """
    def __init__(self, prim_path: str, position: list, topic_name: str = "/camera/image_raw"):
        self.prim_path = prim_path
        self.topic_name = topic_name
        
        # 1. 在物理世界中“物理挂载”相机
        omni.kit.commands.execute(
            "CreatePrimWithDefaultXform",
            prim_type="Camera",
            prim_path=self.prim_path,
            attributes={
                "focusDistance": 400, "focalLength": 24,
                "clippingRange": (0.1, 1000000)
            }
        )
        # 设置相机位置 (这里假设它朝向正前方)
        omni.kit.commands.execute(
            "TransformPrimSRT", 
            path=self.prim_path, 
            translation=position, 
            rotation=(0, 0, 0)
        )

        # 2. 召唤“数据直播车”桥接 ROS 2
        # 我们利用 prim_path 动态生成唯一的 node_name，防止装多个相机时名字冲突
        node_name = self.prim_path.split("/")[-1].lower() + "_node"
        
        self.helper = ROS2CameraHelper(
            prim_path=self.prim_path,
            node_namespace="/sensors",
            node_name=node_name,
            topic_name=self.topic_name,
            type="rgb",
            reset_cg=True
        )
        print(f"[✅ Camera] 已挂载至 {self.prim_path}，正在向 ROS 2 发布: {self.topic_name}")
