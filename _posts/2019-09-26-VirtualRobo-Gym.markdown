---
title: "Virtual Robo Gym"
layout: post
date: 2019-09-26 22:10
tag: 
- robotics
- machinlearning
- neuralnetwork
- research
image: 
headerImage: false
projects: true
hidden: true 
description: "A Safer-Smarter-Cheaper way to train Robot' NN for complex motor functions"
category: Project
author: Harsh
externalLink: false
---

![Robot.jpg](/assets/Robot.jpg)

## Introduction & Background
We have created a faster, safer and a smarter method to train robots using **Deep learning** and **Virtual Simulations**. Nowadays machines & robots are trained using ‘**Reinforcement Learning**’: A subset of Machine Learning which enables a machine to learn and adapt by itself through interacting with the environment. Reinforcement learning is nowadays coherently integrated with **Artificial Neural Networks**- some of the most famous Deep Learning Frameworks. These work on a similar mechanism as our brain does. In the process, the machine tries to reduce the error in every training session and increase its accuracy gradually.

![Error_vs_time_graph](https://www.researchgate.net/profile/Mahmut_Bilgehan/publication/240536145/figure/fig6/AS:298706990583812@1448228704129/Training-error-versus-epoch-number-for-the-neural-network-model.png)

In the initial training sessions, it's observed that the error percentage is very high and the descent in the error is high too but as we notice the ending training sessions, it's visible that the error is very less and so is the descent. Because of this very high error percentage in the initial training sessions, the robot behaves absurdly and mostly all the losses take place in these initial training sessions, this is one of the reasons which makes Machine Learning, specifically Reinforcement Learning cumbersome and time-consuming in the real world.

## Proposed Solution
To solve this issue what we have done is that we have shifted the initial training sessions to a **Virtual Physics Environment** and left its neural network to train. A Virtual Physics Environment is similar to a game engine; it contains all the environmental constraints such as gravity, friction, atmospheric pressure, etc. And when the robot has attained a certain level of accuracy then we have transferred the training experience into the Neural Network of the Original Robot. After the transfer, the Robot is left for training in the real world for even better accuracy.

This method could be a boon to small developers as it will provide an efficient and smart platform to develop and train Robots secondly this could be used to even further advance the robotic development by teaching robots more complicated compound functions like surgery, cooking, driving, etc.

[Check out our project's timelapse](https://youtu.be/PzhdrxREtoU)
[Check out the Project's Github Repo](https://github.com/shresthagrawal/VirtualRoboGym)

>'Power does not comes from knowledge kept but knowledge shared' - _Bill Gates_
