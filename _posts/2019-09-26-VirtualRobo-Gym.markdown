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
author: Shresth
externalLink: false
---

![Robot.jpg](/assets/Robot.jpg)

We have created a faster, safer and a smarter method to train robot’s neural Network using deep learning and virtual environment. Nowadays machines are trained using ‘Machine Learning’: A process which enables a machine to learn and adapt itself. One of the most popular branches of Machine Learning is Deep Learning. Deep Leaning has networks capable to learn through unsupervised data. And the most widely used network is ‘Artificial Neural Network’. These work on a similar mechanism as our brain does. It tries to find the relation between the given data by the process of trial and error. In this process, the machine tries to reduce the error in every training session and increase its accuracy gradually.
In the initial training sessions, the error percentage is very high and the descent in the error is very high too but as we see the last few training sessions we could find that the error is very less and so is the descent. And because of very high error percentage in the initial training sessions, the robot behaves absurdly and mostly all the losses take place in the initial training sessions, this is one of the reasons which makes Machine Learning cumbersome and time-consuming.
To solve this issue what we have done is, we have shifted the initial training sessions to a virtual physics environment and leave its neural network to train. A Virtual Physics Environment is similar to a game engine; it contains all the environmental constraints such as gravity, friction, atmospheric pressure etc. And when the robot has attained a certain level of accuracy then we’ll transfer the training experience into the Neural Network of the Original Robot. After the transfer the Robot is left for training in the real world for better accuracy.
This method could be a boon to small developers as it will provide an efficient and smart platform to develop and train Robots secondly this could be used to even further advance the robotic development by teaching robots more complicated compound functions like surgery, cooking, driving, etc.

[MakingTImeLaps](https://youtu.be/PzhdrxREtoU)
[ProjectRepo](https://github.com/shresthagrawal/VirtualRoboGym)