from navigate_python.map_show import *
from navigate_python.navigate import *
from navigate_python.dstar_lite import *
from navigate_python.discretize_map import *
from arguments import get_args

def main(json_file, img_index, record = False):
    '''
    :param json_file: task json file
    :param img_index: record_photo index
    :param record: to or not to record the process
    '''

    import os
    os.environ["OMNI_KIT_ACCEPT_EULA"] = "YES" # Set environment variable to accept OMNI Kit's EULA (End User License Agreement)
    import isaacsim
    from omni.isaac.kit import SimulationApp
    config = {
    "width": "1280",
    "height": "720",
    "headless": False,
    }
    simulation_app = SimulationApp(config) # Configure simulation app, specify window size and headless mode

    import omni.isaac.core.utils.bounds as bounds_utils
    import numpy as np
    import math
    import json
    from omni.isaac.core import World
    from omni.isaac.core.prims import GeometryPrim,XFormPrim
    import omni.isaac.core.utils.prims as prim_utils
    from omni.isaac.sensor import Camera


    from BaseControl_position import BaseControl
    from BaseGrasp import BaseGrasp
    from transformations import quaternion_from_euler
    from benchmark_utils import check_wall_block, init_robot_pos, calculate_path_length, create_imgs_folder, add_boundary_walls
 
    args = get_args()
    # Import scene
    scene_root_path = args.scene_root_path
    
     # Create a recording folder under the task json
    if record:
        process_img_folder = create_imgs_folder(json_file)
    else:
        process_img_folder = ''

    # Extract the target scene ID
    with open(json_file, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    
    scene_id = json_data['Scene']
    scene_path = scene_root_path + scene_id + "/" + scene_id + ".usd"
    
    # Create world
    my_world = World(stage_units_in_meters=1.0)
    reset_needed = False

    # Add default ground plane to the scene
    add_boundary_walls()

    # Use map random point to initialize robot position
    map_path = args.occupancy_map_root_path + scene_id
    img_folder = os.listdir(map_path)
    png_files = [file for file in img_folder if file.endswith('.png')]
    map_name = png_files[0]

    map_file=map_path+"/"+map_name
    stretch_pos = init_robot_pos(map_file=map_file)
    print("Robot position determined")

    # Create robot
    stretch_path = args.robot_usd_path
    prim_utils.create_prim(
    prim_type="Xform",
    prim_path = "/World/stretch",
    usd_path=stretch_path,
    translation = np.array([stretch_pos[0],stretch_pos[1],0.0])
    )

    # Create scene
    construct_scene=prim_utils.create_prim(
        prim_type="Xform",
        prim_path = "/World/Scene",
        usd_path = scene_path,
        scale=[1, 1, 1],
        translation=np.array([0, 0, 0]),
        orientation=[1,0,0,0]
    )
    GeometryPrim("/World/Scene", collision=True)


    # Overall lighting
    prim_utils.create_prim(
        "/World/Light_3",
        "DomeLight",
        position=np.array([0.0, 0.0, 0.0]),
        attributes={
            "inputs:intensity": 1e3,
            "inputs:color": (1.0, 1.0, 1.0)
        }
    )

    # Add camera sensor
    camera = Camera(args.camera_path,
                        position = np.array([stretch_pos[0],stretch_pos[1], 1.0]),
                        resolution=(1280,640),
                        frequency=30,
                        orientation = np.array([1, 0, 0, 0]))

    camera.initialize()
    camera.add_motion_vectors_to_frame() 
    camera.add_distance_to_image_plane_to_frame()
    camera.set_focal_length(31.17691)
    camera.set_horizontal_aperture(36.0)


    robot_path = args.robot_path    

    while simulation_app.is_running():
        my_world.step(render=True)
        if my_world.is_stopped() and not reset_needed:
            reset_needed = True
        # my_world.play() # auto simulation
        if my_world.is_playing():
            if reset_needed:
                my_world.reset()
                reset_needed = False

                # Extract prior information
                # Get all object names in the scene, prim_dict keys are prim names, values are corresponding prims
                child = prim_utils.get_prim_children(construct_scene)
                child = prim_utils.get_prim_children(child[0])
                prim_list = []
                prim_dict = {}
                for prim in child:
                    prim_list.extend(prim_utils.get_prim_children(prim))
                for prim in prim_list:
                    prim_dict[prim.GetName()]=prim
                
                # Extract target object IDs
                target_ids = [item[0] for item in json_data['Target']]
                ID1,_ = target_ids

                # Check if the two object IDs are in the scene dictionary, otherwise use _ prefixed version
                if ID1 not in prim_dict:
                    ID1 = "_" + ID1[1:]
                            
                # ID1, used for grasping
                obj_path = args.obj_in_isaac_path + ID1

                # Define object 1attribute dictionary
                obj_dict = {} 
                for attr in prim_dict[ID1].GetAttributes(): 
                    obj_dict[attr.GetName()] = attr.Get()

                # Define object prims
                r,p,y = obj_dict["xformOp:rotateXYZ"]
                quaternion1 = quaternion_from_euler(r/180 * math.pi,p/180 * math.pi,y/180 * math.pi)
                obj_xformprim = XFormPrim(obj_path,translation=obj_dict["xformOp:translate"],orientation=quaternion1) 

            
                # Get actual position of the object
                goal_obj_3, _ = obj_xformprim.get_world_pose()
                goal_obj = [goal_obj_3[0], goal_obj_3[1]]

                # Define map and navigation classes
                hm = HeightMap(map_file)
                xy_range = hm.compute_range()
                hm.make_map()
                hm_map = hm.get_map()

                navigator = Navigator(area_range=xy_range, map=hm_map, scale_ratio=1)
                navigator.planner.compute_cost_map()

                stretch_robot = XFormPrim("/World/stretch")
                position = stretch_robot.get_default_state().position
                nav_start1 = [position[0],position[1]]

                # Define movement and grasping classes
                base_control = BaseControl(robot=robot_path,obj_prim=obj_xformprim)
                                
                # Path planning
                path, map_path = navigator.navigate(goal_obj, nav_start1)

                # Calculate total path length and deviation of the first navigation segment
                path_plan_len = calculate_path_length(path=path)
                
                # Move to the specified position
                for i in range(len(path)):
                    tmp = [path[i][0],path[i][1],0]
                    base_control.move_by_target(tmp, my_world,img_index=img_index,
                                                orientation=False,camera=camera,
                                                process_img_folder=process_img_folder)
                    my_world.step(render=True)

                
                # Calculate the deviation of the first navigation segment
                cur_position, cur_orientation = stretch_robot.get_world_pose()
                NE = math.dist(goal_obj, [cur_position[0],cur_position[1]])
                # Check if there is a wall between the object and the robot
                if check_wall_block(img_path=map_file,obj_world_pos=goal_obj,robot_world_pos=[cur_position[0],cur_position[1]]) and NE < 2:
                    success = 1
                    return success, path_plan_len, NE
                else:
                    success = 0
                    return success, path_plan_len, NE

    simulation_app.close()