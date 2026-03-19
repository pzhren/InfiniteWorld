# Installation
## Install isaac-sim
Infiniteworld is built upon NVIDIA's Omniverse and Isaac Sim 4.0.0 platforms, so we inherit their dependencies. For more information, please refer to the official [Isaac Sim requirements](https://docs.omniverse.nvidia.com/isaacsim/latest/installation/requirements.html#system-requirements) and [installation tutorial](https://docs.omniverse.nvidia.com/isaacsim/latest/installation/install_workstation.html).


## Set up conda environment
1. After installing isaac sim, please remember the path of the `isaac-sim.sh` file. Generally, it is located at `../isaac-sim/pkg/isaac-sim4.0.0/isaac-sim.sh`.

2. run the `setup_conda.sh` file to create the conda environment. The command line prompts you to enter the path of the isaac-sim.sh file. After entering the path, you will be prompted to enter the name of the conda environment you want to create. If it defaults to `isaac-sim`.
    ```bash
    bash setup_conda.sh
    ```

3. conda activates the environment that was just created.
    ```bash
    conda activate isaac-sim
    ```

4. pip install the dependencies.
    ```bash
    pip install -r requirements.txt
    ```
## Run the benchmark
1. Prepare the dataset.
    - You can download the dataset from [here](https://huggingface.co/datasets/hssd/hssd-scenes/tree/main/scenes). Use our provided [script](/3D%20format%20convert/scene_format_convert/glb2usd.py) to generate `.usd` files from the `.glb` files. Use the ID number as the folder name, with the file name being `ID_number.usd`. 
    - The folder should contain the `.usd` file and a `textures` folder.



2. Get the occupancy map of the scene.
    - Open the USD file in the Isaac Sim interface by going to `File` -> `Open`, then select the corresponding USD file to import it into the software.
   - Click on `Isaac Utils` -> `Occupancy Map` to obtain the global obstacle map for the scene.
   - In the `Origin` option, change the numerical values to set the center of diffusion in an open area, such as a living room without obstacles; otherwise, you will get an incorrect obstacle map.
   - Set the `Upper bound z-axis` and `Lower bound z-axis` heights to 1.5 and 0.2, respectively.
   - Click `BOUND SELECTION` to make the scene map closely fit the obstacle map.
   - Click `CALCULATE` to generate the obstacle map.
   - Click `VISUALIZE IMAGE` to save the map. At the same time, mark the coordinates of the top-left corner of the map. With x-axis pointing down and y-axis pointing right, the top-left corner coordinates are usually negative. Record the coordinates in the format `X_(x-coordinate)Y_(y-coordinate).png`, for example, `X_-0.5Y_-2.7.png`. It is best to store the map along with the USD file in the same folder.



3. Get the task json of the scene.
    - You can generate your own tasks based on `gen task/task_gen.py`, you can choose a scene id of HSSD scene to generate the tasks in the scene. Don't forget to fill your openai key in `gpt.py`.
    - You can get the semantic info from `semantic/semantic.py`, and you need to unzip the `scenes-uncluttered` file first.

4. Run the benchmark code.You should modify the scne file path and the map file path in the `arguments.py` and then  Modify the task json file path in `Benchmark1.py` and `Benchmark2.py`.After that, you can run them.
    - Navigate to the `benchmark` folder.
    - Run the `Benchmark1.py` or `Benchmark2.py`.
     ```bash
     python Benchmark1.py
     ```

Then you will see the simulation scene in the Isaac Sim window. Click the `Start Simulation` button on the left side. Wait a moment to observe the robot performing the tasks. You can use the middle mouse button in combination with the `Alt` key on the keyboard to switch between different viewpoints.

**You can view the demonstration videos through the following links.**


- [Benchmark1](https://www.bilibili.com/video/BV199rVYBEnf?)
- [Benchmark2](https://www.bilibili.com/video/BV1RXrVYuE8d?)
- [Benchmark3](https://www.bilibili.com/video/BV1FTNCedExu?)
- [Benchmark4](https://www.bilibili.com/video/BV1KbPdeKE1K?)



## Keyboard Control

After completing the benchmark tests, if you want to control the robot's movement in the scene using the `keyboard`, it can be executed by following these steps:

- modify the `--keyboard_json_path` in the [`arguments.py`](/benchmark/arguments.py) to the desired `.json file`
- run the [`demo_keyboard_control.py`] to control stretch robot (/benchmark/demo_keyboard_control.py) .
- run the [`demo_keyboard_control_h1.py`] to control Unitree H1 robot (/benchmark/demo_keyboard_control_h1.py) 
  

You can control the stretch robot with keyboard command:

- W: Move Forward
- S: Move Backward
- A: Turn Left
- D: Turn Right
- Q: Exit

You can control the h1 robot with keyboard command:

- NUMPAD 8/UP: Move forward
- NUMPAD 4/LEFT: Turn left
- NUMPAD 6/RIGHT: Turn right
- ESC: Exit
