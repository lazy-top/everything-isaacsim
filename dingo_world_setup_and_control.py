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

# 添加世界原点
import isaacsim.core.utils.prims as prims_utils
prims_utils.create_prim(prim_path="/World",prim_type="Xform")
from isaacsim.core.api.objects import GroundPlane
# 创建一个地板，并且加载到场景中
plane = GroundPlane(prim_path="/World/GroundPlane", z_position=0)


from pxr import UsdLux, Sdf, Gf
# 获取stage 对象
import isaacsim.core.utils.stage as stage_utils
stage =stage_utils.get_current_stage()


# 创建平行光源
light_path = "/World/DistantLight"  # 设置prim_path
light = UsdLux.DistantLight.Define(stage, Sdf.Path(light_path))  # 创建DistantLight实例
light.CreateIntensityAttr(6e2)  # 设置光照强度
light.CreateColorAttr(Gf.Vec3f(1.0, 1.0, 1.0))  # 设置RGB颜色
light.AddRotateXYZOp().Set(Gf.Vec3f(-45, 0, 0))  # 设置旋转


# 加载dingo模型到场景中
import isaacsim.core.utils.stage as stage_utils

dingo_usd_path = "/home/wcj/sim/QRCodeSim/usd/Dingo/dingo.usd"
dingo_prim_path = "/World/Dingo"

stage_utils.add_reference_to_stage(dingo_usd_path, dingo_prim_path)

# 创建一个关节，及其关节控制器
from isaacsim.core.prims import Articulation
from isaacsim.core.api.controllers.articulation_controller import ArticulationController
dingo_art = Articulation(prim_paths_expr=dingo_prim_path,name="Dingo_Articulation")


dingo_controller = ArticulationController()

dingo_controller.initialize(dingo_art)

# 创建一个关节动作
from isaacsim.core.utils.types import ArticulationAction
import numpy as np
joint_action = ArticulationAction(joint_velocities=np.array([1.0, 0.0]), joint_indices=np.array([0, 1]))

# 获取仿真的上下文
from isaacsim.core.api import SimulationContext
simulation_context = SimulationContext()

# 创建一个异步任务，用于关节控制器的执行
async def task():
    # 播放模拟
    await simulation_context.play_async()
    dingo_controller.apply_action(joint_action)


# 运行异步任务
from omni.kit.async_engine import run_coroutine
run_coroutine(task())


# 当isaacsim应用运行时，持续更新模拟
while simulation_app.is_running():
    simulation_app.update()

simulation_context.stop()
simulation_app.close()
