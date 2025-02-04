'''

    Delay lines

'''


import numpy as ncp
from .neural_structure import NeuralStructure



class DelayLine(NeuralStructure):

    interfacable = 0


    def __init__(self, **kwargs):
        required_parameters = {'time_step', 'delay'}
        for required_parameter in required_parameters:
            assert required_parameter in kwargs.keys(), f"{required_parameter} is required in a {type(self)}"
        super().__init__(**kwargs)
        self.state["delay_in_compute_steps"] = int(self.delay / self.time_step)


    def interface(self, external_component):

        delay_in_compute_steps = self.state["delay_in_compute_steps"]



        self.external_component = external_component

        external_component_read_variable = self.external_component.interfacable

        external_component_read_variable_shape = external_component_read_variable.shape


        # read_variable should be a 2d array of spikes

        self.state["spike_source"] = ncp.zeros(

            external_component_read_variable_shape)
        spike_source = self.state["spike_source"]


        self.state["delay_line"] = ncp.zeros(

            (spike_source.shape[0], spike_source.shape[1], delay_in_compute_steps))

        self.state["new_spike_output"] = ncp.zeros(spike_source.shape)

        self.state["current_spike_output"] = ncp.zeros(spike_source.shape)


        self.interfacable = self.state["new_spike_output"]


    def set_state(self, state):
        self.state = state

        self.interfacable = self.state["new_spike_output"]


    def compute_new_values(self):

        delay_line = self.state["delay_line"]

        new_spike_output = self.state["new_spike_output"]
        spike_source = self.state["spike_source"]



        delay_line[:, :, :] = ncp.roll(delay_line, 1, axis=2)

        new_spike_output[:, :] = delay_line[:, :, -1]

        delay_line[:, :, 0] = spike_source

        # return ncp.amax(self.new_spike_output)

        # print("new")

        # return 1


    def update_current_values(self):
        current_spike_output = self.state["current_spike_output"]

        new_spike_output = self.state["new_spike_output"]
        spike_source = self.state["spike_source"]


        current_spike_output[:, :] = new_spike_output

        spike_source[:, :] = self.external_component.interfacable

        # print("update")

        # return 2

