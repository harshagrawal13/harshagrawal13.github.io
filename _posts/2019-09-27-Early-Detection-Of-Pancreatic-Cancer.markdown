---
title: "Early Detection of Pancreatic Cancer through a Cheap, Non-invasive Salivary Test"
layout: post
date: 2019-09-27 22:29
tag: 
- cancer
- pancreas
- machinlearning
- neuralnetwork
- research

image: 
headerImage: false
projects: true
hidden: true 
description:
category: Project
author: Harsh
externalLink: false
---

## Introduction & Background

**Pancreatic Cancer** is one of the most life-threatening cancers in the world. It takes away lives of around 300,000 people worldwide. Currently, there’s an urgent need for the early detection of this disease to increase the survival rates of this deadly cancer.   
Generally, it is diagnosed using:
- Scans like PET, CT or MRI.  
- Biopsy or,
- CA19-9 Blood Test

But according to **American College of Radiology**, no imaging exams should be done unless there is a clear medical benefit, also these scans are too expensive, which is not viable for a normal person to regularly take these scans. 
**Biopsies** on the other hand, often lead to confirmatory diagnosis, but a doctor usually recommends a biopsy after the patient has presented with almost all signs for a tumor. As it is an _Invasive procedure_, a patient can't take biopsy tests for general screening. 
Coming to the **CA19-9 blood test**, it has a poor specificity & sensitivity of just **_65-70%_**, hence cannot be used as a screening tool for the general population. 

## Proposed Solution

### Spermine as a potential Bio-marker

According to a recent study, it was found that an increase of poly-amine concentration in bio-fluids correlates with increased cell proliferation and tumorigenesis. In Carcinomas like that of the pancreas, significant  up-regulation of the 4 different poly-amines were found to have significant changes in salivary concentrations of Pancreatic Cancer vs Non-pancreatic Cancer patients 
- Spermine
- N1 Acetylspermine
- N1 Acetylspermidine
- 2-amino-butanoate 

Hence, Spermine was endorsed as a marker for Pancreatic Cancer.

### Lateral Flow Assay for Analyzing the concentration of Spermine

![Lateral_Flow_Assay](https://groeptms1316.files.wordpress.com/2013/02/assay-config.jpg)

We have designed a novel strip based assay to analyze the concentration of **Spermine Protein**  through saliva. By the presence of 40nm carboxyl gold, a conjugate, it shows a color change at the _control line_, when target spermine present in the saliva binds with **_Anti-spermine gold-conjugated antibody_** & is detected by the **_Secondary detector probe_**.  

After the test has been conducted, the intensity of the color change would be measured through a Convolution Neural Network based web application which would effectively confirm either the test showed positive or negative results & if positive then classify in which stage is the tumor most likely to be. 

### Novelty
* This is the _first ever_ strip to detect Pancreatic Cancer through saliva and it is nearly **125 times cheaper** than general _CT/MRI/PET scans_ & **10 times cheaper** than the _CA19-9 ELISA Blood test_.
* All the previous methods requires Serum as a bio-fluid which is obtained through a _minimally invasive procedure_ but our procedure requires _Saliva_ as the bio-fluid which is totally non-invasive. (can be performed at home as well). 
* We have integrated a smart web application based reader which easily distinguishes between _normals & Pancreatic Cancer patients_ and makes the process even more _Point of Care_.

Check out the full project synopsis at [Google Science Fair](https://www.googlesciencefair.com/projects/2018/1e2bf23dd1fad8110ab15c43dddaef4081c30fae2f40e613d6237f7bd049d1b6).
