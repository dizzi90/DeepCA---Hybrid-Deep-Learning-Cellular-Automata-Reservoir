# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 14:13:26 2020

Demonstration 1

@author: trymlind
"""

import numpy as np
import cv2
import framework_module as fm

pop_x = 400
pop_y = 400

neighboyrhood_template_1 = np.ones((7,7))
neighboyrhood_template_2 = np.ones((7,7))
neighboyrhood_template_2[3:5,3:5] = 0
neighboyrhood_template_2[0,:] = 0
neighboyrhood_template_2[1,:] = 0

population_1 = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_1, weight_mean= 0.5, weight_SD = 0.3)
population_2 = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_1, weight_mean= 0.5, weight_SD = 0.3)
population_3 = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_1, weight_mean= 0.5, weight_SD = 0.3)
population_4 = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_1, weight_mean= 0.5, weight_SD = 0.3)

population_1_inhib = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_2, weight_mean= 0.5, weight_SD = 0.3)
population_2_inhib = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_2, weight_mean= 0.5, weight_SD = 0.3)
population_3_inhib = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_2, weight_mean= 0.5, weight_SD = 0.3)
population_4_inhib = fm.Soma_AS_with_projection_weights(membrane_decay = 0.9, treshold_decay = 0.8, membrane_treshold_resting_distance = 0.5, population_size_x = pop_x, population_size_y = pop_y, neighbourhood_template = neighboyrhood_template_2, weight_mean= 0.5, weight_SD = 0.3)

pop_list = [population_1, population_2, population_3, population_4]
pop_list_inhib = [population_1_inhib, population_2_inhib, population_3_inhib, population_4_inhib]
input_pattern = np.zeros((pop_x, pop_y))
#input_pattern[200,200] = 1

t = 0
k = 0
while True:
    
    if t > 20 and k > 10:
        input_pattern[np.random.randint(0,400), np.random.randint(0,400)] = 1
        k = 0
    
    t += 1
    k += 1
        
    for index, pop in enumerate(pop_list):
        if index == 0:
            pop.membrane_additive_input(input_pattern)
            pop.send_spikes_to_synapses(pop_list[index].spiked_neurons)
            pop.membrane_additive_input(np.sum(pop.spike_array, 2))
            pop.compute_spikes()
        else:
            pop.send_spikes_to_synapses(pop_list[index - 1].spiked_neurons)
            pop.membrane_additive_input(np.sum(pop.spike_array, 2))
            pop.compute_spikes()
            pop.threshold_additive_input(np.sum(pop.spike_array, 2)**2)
    
    
    video_1 = np.concatenate((population_1.spiked_neurons, population_2.spiked_neurons), 1)
    video_2 = np.concatenate((population_3.spiked_neurons, population_4.spiked_neurons), 1)
    video = np.uint8(np.concatenate((video_1, video_2), 1))*255
    cv2.imshow('frame', video)
    
    #network.network_state[0,:] = 0
 
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break