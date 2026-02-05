
# 实现对多个机器人的控制

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
# 将dingo模型以列表形式批量加载到场景中
import isaacsim.core.utils.stage as stage_utils



dingo_usd_path = "/home/wcj/sim/everything-isaacsim/usd/Dingo/dingo.usd"
robot_prim_paths = [
    "/World/Dingo_0",
    "/World/Dingo_1",
    "/World/Dingo_2",
    "/World/Dingo_3",

]
# 将多个dingo模型注册到场景中,并且为其添加各异的控制器
for i in range(len(robot_prim_paths)):
    stage_utils.add_reference_to_stage(dingo_usd_path, robot_prim_paths[i])


# 创建一个franka模型，并加载到场景中
from isaacsim.core.api.controllers.articulation_controller import ArticulationController
from isaacsim.core.prims import Articulation
franka_usd_path = "/home/wcj/sim/everything-isaacsim/usd/FrankaPanda/franka.usd"
franka_prim_path = "/World/FrankaPanda"
stage_utils.add_reference_to_stage(franka_usd_path, franka_prim_path)
articulation_view = Articulation(prim_paths_expr=franka_prim_path, name="franka_panda_view")
articulation_controller = ArticulationController()
articulation_controller.initialize(articulation_view)


import isaacsim.core.utils.prims as prims_utils
import numpy as np
# 调整各个模型的位置和旋转
prims_utils.set_prim_attribute_value(robot_prim_paths[0], attribute_name="xformOp:translate", value=np.array([0, 0.5, 0.5]))
prims_utils.set_prim_attribute_value(robot_prim_paths[1], attribute_name="xformOp:translate", value=np.array([0, -0.5, 0.5]))
prims_utils.set_prim_attribute_value(robot_prim_paths[2], attribute_name="xformOp:translate", value=np.array([0.5, 0, 0.5]))
prims_utils.set_prim_attribute_value(robot_prim_paths[3], attribute_name="xformOp:translate", value=np.array([-0.5, 0, 0.5]))






# 获取仿真的上下文
from isaacsim.core.api import SimulationContext
simulation_context = SimulationContext()




# 创建一个dingo_0的专属的异步任务，用于关节控制器的执行
async def dingo_0_task():
    # 播放模拟
    await simulation_context.play_async()
# 创建一个dingo_1的专属的异步任务，用于关节控制器的执行
async def dingo_1_task():
    # 播放模拟
    await simulation_context.play_async()
# 创建一个dingo_2的专属的异步任务，用于关节控制器的执行
async def dingo_2_task():
    # 播放模拟
    await simulation_context.play_async()
# 创建一个dingo_3的专属的异步任务，用于关节控制器的执行
async def dingo_3_task():
    # 播放模拟
    await simulation_context.play_async()

# 创建一个franka的专属的异步任务，用于关节控制器的执行
async def franka_task():
    # 播放模拟
    await simulation_context.play_async()
        # Create target positions
    import asyncio
    await asyncio.sleep(5.0) 
    target_positions = np.array([0.0, -1.5, 0.0, -2.8, 0.0, 2.8, 1.2, 0.04, 0.04])


    # Create and apply articulation action

    action = ArticulationAction(joint_positions=target_positions)

    articulation_controller.apply_action(action)


# 运行异步任务
from omni.kit.async_engine import run_coroutine
run_coroutine(dingo_0_task())
run_coroutine(dingo_1_task())
run_coroutine(dingo_2_task())
run_coroutine(dingo_3_task())


# 当isaacsim应用运行时，持续更新模拟
while simulation_app.is_running():
    simulation_app.update()

simulation_context.stop()
simulation_app.close()
