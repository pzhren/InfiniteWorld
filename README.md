<div align="center">
<h1> :earth_africa: InfiniteWorld </h1>
<h3>An Open-Ended Simulation Framework for Embodied AI with Social and Collaborative Benchmarks</h3>
    
Pengzhen Ren*, Min Li*, Zhen Luo*, Xinshuai Song*, Ziwei Chen*, Weijia Liufu*, Yixuan Yang*

Hao Zheng，Rongtao Xu, Zitong Huang, Tongsheng Ding, Luyang Xie, Kaidong Zhang, Yang Liu

Feng Zheng<sup>:email:</sup>, Xiaodan Liang<sup>:email:</sup>，Liang Lin<sup>:email:</sup>

<sup>* </sup>equal contribution.   <sup>:email:</sup> corresponding author.

[[`Paper`](https://arxiv.org/abs/2412.05789).]
[[`Workshop/Web`](https://smm-challenge.github.io/)]

</div>

## 💥Updates

<!--
**2026-01-29**: We update the [camera-ready version](https://link-to-your-file) 📸 of our paper and uploaded the official [paper poster](https://link-to-your-poster) for AAAI 2026.
- **2025-11-21**: We release the code for X-SAM with [Qwen3-4B-Instruct-2507](https://link) and [Qwen3-1.7B](https://link). We will release the weights soon.
- **2025-11-19**: We release the code for [Training X-SAM](https://link). Welcome to try it! If you have any questions, please feel free to open an issue.
- **2025-11-08**: Congratulations! 🎉🎉🎉 X-SAM has been accepted by AAAI 2026! We will release all the code in the coming week!
- **2025-09-28**: We update the [Local Demo](https://link) Inference script, you can run local inference instead of on the Web Demo.
- **2025-08-11**: Thanks for your great attention to our work! We have deployed another [Online Demo2](https://link). You can also try it if [Online Demo1](https://link) is not available.
- **2025-08-11**: We released the effective code for [Evaluation on All Segmentation Benchmarks](https://link). We have updated all code except for [Training X-SAM](https://link).
- **2025-08-10**: We released the detailed instructions for [Demo Deployment](https://link).
- **2025-08-09**: We released the code for [Training LLaVA-based MLLMs](https://link).
- **2025-08-08**: We released the simple code for [Evaluation on All VLM Benchmarks](https://link).
- **2025-08-06**: We are excited to publish the [Technical Report](https://link), please check it out for more technical details.
- **2025-08-05**: We provided the [Model Weights](https://huggingface.co/your-model) 🤗.
- **2025-07-26**: We deployed the [Online Demo](https://link), you can try it now!
-->
- **2025-08**: We have released multiple demos about [collaborative exploration of scene graphs](https://www.bilibili.com/video/BV1Js8DzPE4P?), [physics-based grabbing in reconstructed scenes](https://www.bilibili.com/video/BV1PH8RzQEWf?), [real robot](https://www.bilibili.com/video/BV1KbPdeKE1K?), and [benchmarks](#demo).
- **2025-08**: We released the OWSMM benchmark and asset conversion interface.
- **2025-07**: We have released the corresponding robot interface 🤖 and LAGSE-related code.
- **2025-06**: The V3A team from Adelaide University won the championship 🏆 in the CVPR2025 SMM Challenge.
- **2025-05**: We released the first version 🎉🎉🎉 of InfiniteWorld.
- **2025-04**: We held the first social mobile manipulation challenge 🏃‍♀️ - [CVPR2025 Embodied AI workshop challenge](https://smm-challenge.github.io/).




![20241202_215955](https://gitee.com/pzhren/img/raw/master/img/202412022200214.png)

## :rocket: Introduction

* We have built a unified and scalable simulation framework that integrates various improved and latest embodied asset reconstruction methods. This has greatly alleviated the community's plight of lacking high-quality embodied assets.
* We build a complete web-based smart point cloud automatic annotation framework that supports distributed collaboration, AI assistance, and optional human-in-the-loop features. This provides strong support for complex robot interactions.
* We designed systematic benchmarks for robot interaction, including scene graph collaborative exploration and open-world social mobile manipulation. This provides a comprehensive and systematic evaluation of the capabilities of embodied agents in perception, planning, execution, and communication.

## :page_facing_up: Simulator
![20241202_221116](https://gitee.com/pzhren/img/raw/master/img/202412022211180.png)

Overview of the functions of InfiniteWorld simulator.  Our simulation platform supports different sensors, robot platforms, and teleoperation. In addition, it also realizes unlimited expansion of scene and object assets through generative and Sim2Real methods, and we have also built an annotation platform to reduce annotation costs and improve annotation quality.

### Language-Driven Automatic Scene Generation and Editing
![20241202_221141](https://gitee.com/pzhren/img/raw/master/img/202412022211858.png)Language-driven automatic scene generation and editing framework based on HOLODECK [77]. It can easily generate various interactive high-fidelity scenes that meet the requirements of users, including scene style replacement, object editing (e.g., adding/removing a  specific number of objects), and replacement (that is, replacing similar objects), etc.

### Depth-Prior-Constrained Real2Sim
We use the depth prior to constrain the generation of the 3D model, which enhances simulation realism by integrating depth priors and normal priors into the Planar-based Gaussian Splatting Reconstruction (PGSR) framework.

Additionally, this project contains Python scripts for post-processing reconstructed mesh scene `ply` files, which could help you optimize, repair, and enhance the 3D mesh. Especially, an example of a conda environment `real2sim/post-process/env.yaml` is provided, which has been tested to successfully run all scripts on Windows 11. 

For specific usage methods, see [README.md](./real2sim/README.md).

### Annot8-3D

The 3D annotation framework is open-sourced at: https://github.com/zh-plus/annot8-3d.

### Unified 3D Asset

We provide code for converting 3D datasets into different formats in `3D format convert`. We have the scene converter and object converter. The scene converter requires installing the `pymeshlab` library. The script `./object_format_convert/obj_usd.py` allows you to convert objects in OBJ format to USD format for use in Isaac Sim. For batch conversions, you can use `obj_usd_multi.py`, though its compatibility with Isaac Sim is limited. Additionally, `./object_format_convert/pkl_obj.py` converts files from PKL to OBJ format, which is the first step in adapting the Objaverse dataset for use in Isaac Sim.

The example of object converter is in the corresponding file folders. Due to the large size of the scene, the examples are in the link [`here`](https://pan.baidu.com/s/1F3cvNVf9hZG3h7AOD4FM0g?pwd=1234 ) with the [password:1234].

And here is the link for our 3D object assets list:
| Dataset              | Categories | Count     | Scenes              | Links                                                       | Password |
| -------------------- | ---------- | --------- | ------------------- | ----------------------------------------------------------- | -------- |
| 3D Front             | 21         | 5,172     | Furniture scenes    | [Download](https://pan.baidu.com/s/1Hyhsw-nkgt4HgNNN1tfMIQ) | qprj     |
| PartNet              | 24         | 26,671    | Articulated objects | [Download](https://pan.baidu.com/s/1LPH-LKmYYoBu4sOvqUnzVA) | parn     |
| Objaverse (Holodeck) | 940        | 4,042,937 | Small objects       | [Download](https://pan.baidu.com/s/17BPY5CV5szfTSXDuVKPtPQ) | etmn     |
| ClothesNet           | 11         | 3,051     | Clothing            | [Download Link](https://sites.google.com/view/clothesnet/)  | -        |

### Generation Scene
We provide scripts in `generation scene` to import from the scene generated json file. You can convert them to usd format using `./multi_place.py`. Note: you need to change 'scene_files' 'output_files' and 'obj_data_usd' to your own paths in [code](https://github.com/pzhren/InfiniteWorld/blob/master/generation%20scene/multi_place.py#L189).

## Dataset

We integrated our dataset on Hugging Face, for more details please refer to [this link](https://huggingface.co/datasets/Starry123/InfiniteWorld).

## Benchmark

![20241202_220957](https://gitee.com/pzhren/img/raw/master/img/202412022210150.png)
Detailed benchmark descriptions can be found [`here`](/benchmark/readme.md).

## Demo

- [Benchmark1](https://www.bilibili.com/video/BV199rVYBEnf?)
- [Benchmark2](https://www.bilibili.com/video/BV1RXrVYuE8d?)
- [Benchmark3](https://www.bilibili.com/video/BV1FTNCedExu?)
- [Benchmark4：Real robot demonstration](https://www.bilibili.com/video/BV1KbPdeKE1K?)
- [Physical grabbing-based desktop organization in a reconstruction scenario](https://www.bilibili.com/video/BV1PH8RzQEWf?)
- [Example of point target navigation for an agent in Real2Sim scenario](https://www.bilibili.com/video/BV1D7tAz1EuZ/?spm_id_from=333.1387.list.card_archive.click&vd_source=b01e665629cc1f07444fb56603b20deb)
- [Humanoid and quadruped robot explore in the room](https://www.bilibili.com/video/BV1Js8DzPE4P?)

You can click on the links to view the videos directly.



## Citation

If you find this code useful in your work, please consider citing

```shell
@misc{ren2024infiniteworld,
    title={InfiniteWorld: A Unified Scalable Simulation Framework for General Visual-Language Robot Interaction},
    author={Pengzhen Ren and Min Li and Zhen Luo and Xinshuai Song and Ziwei Chen and Weijia Liufu and Yixuan Yang and Hao Zheng and Rongtao Xu and Zitong Huang and Tongsheng Ding and Luyang Xie and Kaidong Zhang and Changfei Fu and Yang Liu and Liang Lin and Feng Zheng and Xiaodan Liang},
    year={2024},
    eprint={2412.05789},
    archivePrefix={arXiv},
    primaryClass={cs.RO}
}
