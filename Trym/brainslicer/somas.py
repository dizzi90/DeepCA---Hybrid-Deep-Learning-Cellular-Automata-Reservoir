import numpy as ncp
import sys
from .neural_structure import NeuralStructure
from .support_classes import InterfacableArray
from .membrane_equations import IntegrateAndFireNeuronMembraneFunction
from .differential_equation_solvers import RungeKutta2
from .membrane_equations import CircuitEquation, IzhivechikEquation
from .help_functions import remove_neg_values


'''
Somas
'''

class BaseIntegrateAndFireSoma(NeuralStructure):
    interfacable = 0
    current_somatic_voltages = 0
    current_spiked_neurons = 0
    new_spiked_neurons = 0
    new_somatic_voltages = 0
    current_u = 0
    summed_inputs = 0
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if len(self.population_size) != 2:
            print(
                "Population size must be size 2 and give population size in x and y dimensions")
            sys.exit(0)
        population_size = self.population_size
        refractory_period = self.refractory_period

        self.state["time_since_last_spike"] = ncp.ones(
            population_size) + refractory_period + 1
        self.state["new_spiked_neurons"] = ncp.zeros(population_size)
        self.state["current_spiked_neurons"] = ncp.zeros(population_size)
        # needs fixing
        self.inputs = InterfacableArray(population_size)
        self.state["connected_components"] = []
        self.state["summed_inputs"] = ncp.zeros(population_size)
        # self.membrane_solver.set_initial_condition(self.current_somatic_voltages)
        self.state["dead_cells_location"] = 1
        self.interfacable = self.state["new_spiked_neurons"]
        # self.set_membrane_function()
    def set_state(self, state):
        self.state = state
        self.interfacable = self.state["new_spiked_neurons"]
        self.summed_inputs = self.state["summed_inputs"]
        self.set_membrane_function()
    def set_membrane_function(self):
        raise NotImplementedError
        sys.exit(1)
    def reconstruct_interface(self, external_component):
        self.inputs.interface(external_component)
    def interface(self, external_component):
        self.inputs.interface(external_component)
        self.state["connected_components"].append(
            external_component.parameters["ID"])
    def set_dead_cells(self, dead_cells_location):
        self.state["dead_cells_location"] = dead_cells_location == 0
    def cap_array(self, array, upper_limit):
        below_upper_limit = array < upper_limit
        array *= below_upper_limit
        array += (below_upper_limit == 0)*upper_limit
        return array
    def reset_spiked_neurons(self):
        new_spiked_neurons = self.state["new_spiked_neurons"]
        time_since_last_spike = self.state["time_since_last_spike"]
        new_somatic_voltages = self.state["new_somatic_voltages"]
        reset_voltage = self.state["reset_voltage"]
        non_spike_mask = new_spiked_neurons == 0
        time_since_last_spike *= non_spike_mask
        new_somatic_voltages *= non_spike_mask
        new_somatic_voltages += new_spiked_neurons * reset_voltage
    def kill_dead_values(self):
        new_somatic_voltages = self.state["new_somatic_voltages"]
        dead_cells_location = self.state["dead_cells_location"]
        new_spiked_neurons = self.state["new_spiked_neurons"]
        # destroy values in dead cells
        new_somatic_voltages *= dead_cells_location
        new_spiked_neurons *= dead_cells_location
    def set_refractory_values(self):
        new_somatic_voltages = self.state["new_somatic_voltages"]
        time_since_last_spike = self.state["time_since_last_spike"]
        refractory_period = self.refractory_period
        reset_voltage = self.state["reset_voltage"]
        # set somatic voltages to the reset value if within refractory period
        new_somatic_voltages *= time_since_last_spike > refractory_period
        new_somatic_voltages += (time_since_last_spike <=
                                 refractory_period) * reset_voltage
    def compile_data(self):
        data = {"parameters": self.__dict__, "state": self.state}
        return self.ID, data
    def compute_new_values(self):
        raise NotImplementedError
        sys.exit(1)
    def update_current_values(self):
        summed_inputs = self.state["summed_inputs"]
        current_somatic_voltages = self.state["current_somatic_voltages"]
        current_spiked_neurons = self.state["current_spiked_neurons"]
        new_somatic_voltages = self.state["new_somatic_voltages"]
        new_spiked_neurons = self.state["new_spiked_neurons"]
        self.inputs.update()
        summed_inputs[:, :] = self.inputs.get_sum()
        #print("summed inputs in update_current_values ",ncp.amax(summed_inputs))
        current_somatic_voltages[:, :] = new_somatic_voltages[:, :]
        current_spiked_neurons[:, :] = new_spiked_neurons[:, :]
        # print("update")
        return(2)

class CircuitEquationIntegrateAndFireSoma(BaseIntegrateAndFireSoma):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        population_size = self.population_size

        if self.reset_voltage["distribution"] == "homogenous":
            self.state["reset_voltage"] = self.reset_voltage["value"]
        elif self.reset_voltage["distribution"] == "normal":
            mean = self.reset_voltage["mean"]
            SD = self.reset_voltage["SD"]
            self.state["reset_voltage"] = ncp.random.normal(
                mean, SD, population_size)
            reset_voltage = self.state["reset_voltage"]
            if self.reset_voltage["pos_neg_uniformity"] == "positive":
                remove_neg_values(reset_voltage, mean, SD)
        elif self.reset_voltage["distribution"] == "uniform":
            low = self.reset_voltage["low"]
            high = self.reset_voltage["high"]
            self.state["reset_voltage"] = ncp.random.uniform(
                low, high, population_size)
        elif self.reset_voltage["distribution"] == "Izhikevich":
            self.state["reset_voltage"] = ncp.zeros(population_size)
            self.state["reset_voltage"] += self.reset_voltage["base_value"]
            membrane_recovery_multiplier = self.reset_voltage["multiplier_value"]

            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            membrane_recovery_variance = membrane_recovery_multiplier * random_variable
            self.state["reset_voltage"] += membrane_recovery_variance
        if self.membrane_time_constant["distribution"] == "homogenous":
            self.state["membrane_time_constant"] = self.membrane_time_constant["value"]
        elif self.membrane_time_constant["distribution"] == "normal":
            mean = self.membrane_time_constant["mean"]
            SD = self.membrane_time_constant["SD"]
            self.state["membrane_time_constant"] = ncp.random.normal(
                mean, SD, population_size)

            membrane_time_constant = self.state["membrane_time_constant"]
            if self.membrane_time_constant["pos_neg_uniformity"] == "positive":
                remove_neg_values(membrane_time_constant, mean, SD)
        elif self.membrane_time_constant["distribution"] == "uniform":
            low = self.membrane_time_constant["low"]
            high = self.membrane_time_constant["high"]
            self.state["membrane_time_constant"] = ncp.random.uniform(
                low, high, population_size)
        elif self.membrane_time_constant["distribution"] == "Izhikevich":
            self.state["membrane_time_constant"] = ncp.zeros(population_size)
            self.state["membrane_time_constant"] += self.membrane_time_constant["base_value"]
            
            membrane_recovery_multiplier = self.membrane_time_constant["multiplier_value"]
            
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            membrane_recovery_variance = membrane_recovery_multiplier * random_variable
            self.state["membrane_time_constant"] += membrane_recovery_variance
        if self.input_resistance["distribution"] == "homogenous":
            self.state["input_resistance"] = self.input_resistance["value"]
        elif self.input_resistance["distribution"] == "normal":
            
            mean = self.input_resistance["mean"]
            SD = self.input_resistance["SD"]
            
            self.state["input_resistance"] = ncp.random.normal(
                mean, SD, population_size)
            
            input_resistance = self.state["input_resistance"]
            
            if self.input_resistance["pos_neg_uniformity"] == "positive":
                remove_neg_values(input_resistance, mean, SD)
        elif self.input_resistance["distribution"] == "uniform":
            
            low = self.input_resistance["low"]
            high = self.input_resistance["high"]
            
            self.state["input_resistance"] = ncp.random.uniform(
                low, high, population_size)
        elif self.input_resistance["distribution"] == "Izhikevich":
            self.state["input_resistance"] = ncp.zeros(population_size)
            self.state["input_resistance"] += self.input_resistance["base_value"]
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            membrane_recovery_multiplier = self.input_resistance["multiplier_value"]
            membrane_recovery_variance = membrane_recovery_multiplier * random_variable
            self.state["input_resistance"] += membrane_recovery_variance
        if self.threshold["distribution"] == "homogenous":
            self.state["threshold"] = self.threshold["value"]
        elif self.threshold["distribution"] == "normal":
            mean = self.threshold["mean"]
            SD = self.threshold["SD"]
            self.state["threshold"] = ncp.random.normal(
                mean, SD, population_size)

            threshold = self.state["threshold"]
            if self.threshold["pos_neg_uniformity"] == "positive":
                remove_neg_values(threshold, mean, SD)
        elif self.threshold["distribution"] == "uniform":
            low = self.threshold["low"]
            high = self.threshold["high"]
            self.state["threshold"] = ncp.random.uniform(
                low, high, population_size)
        elif self.threshold["distribution"] == "Izhikevich":
            self.state["threshold"] = ncp.zeros(population_size)
            self.state["threshold"] += self.threshold["base_value"]
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            membrane_recovery_multiplier = self.threshold["multiplier_value"]
            membrane_recovery_variance = membrane_recovery_multiplier * random_variable
            self.state["threshold"] += membrane_recovery_variance
        if self.background_current["distribution"] == "homogenous":
            self.state["background_current"] = self.background_current["value"]
        elif self.background_current["distribution"] == "normal":
            mean = self.background_current["mean"]
            SD = self.background_current["SD"]
            self.state["background_current"] = ncp.random.normal(
                mean, SD, population_size)
            
            background_current = self.state["background_current"]
            
            if self.background_current["pos_neg_uniformity"] == "positive":
                remove_neg_values(background_current, mean, SD)
        elif self.background_current["distribution"] == "uniform":
            low = self.background_current["low"]
            high = self.background_current["high"]
            self.state["background_current"] = ncp.random.uniform(
                low, high, population_size)
        elif self.background_current["distribution"] == "Izhikevich":
            self.state["background_current"] = ncp.zeros(population_size)
            self.state["background_current"] += self.background_current["base_value"]
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            background_current_multiplier = self.background_current["multiplier_value"]
            background_current_variance = background_current_multiplier * random_variable
            self.state["background_current"] += background_current_variance
        
        reset_voltage = self.state["reset_voltage"]
        
        self.state["current_somatic_voltages"] = ncp.ones(
            population_size) * reset_voltage
        self.state["new_somatic_voltages"] = ncp.ones(
            population_size) * reset_voltage
        self.set_membrane_function()
    def set_membrane_function(self):
        input_resistance = self.state["input_resistance"]
        membrane_time_constant = self.state["membrane_time_constant"]
        background_current = self.state["background_current"]
        
        membrane_function = CircuitEquation(
            input_resistance, membrane_time_constant, self.summed_inputs, background_current)
        self.membrane_solver = RungeKutta2(
            membrane_function, self.time_step)
    def compute_new_values(self):
        '''
            
        '''
        time_step = self.time_step
        upper_limit = self.temporal_upper_limit
        time_since_last_spike = self.state["time_since_last_spike"]
        current_somatic_voltages = self.state["current_somatic_voltages"]
        new_somatic_voltages = self.state["new_somatic_voltages"]
        new_spiked_neurons = self.state["new_spiked_neurons"]
        threshold = self.state["threshold"]
        dead_cells_location = self.state["dead_cells_location"]
        time_since_last_spike += time_step
        new_somatic_voltages += self.membrane_solver.advance(
            current_somatic_voltages, t=0)
        # set somatic values for neurons that have fired within the refractory period to zero
        #self.new_somatic_voltages *= self.time_since_last_spike > self.refractory_period
        self.set_refractory_values()
        new_spiked_neurons[:, :] = new_somatic_voltages > threshold
        self.reset_spiked_neurons()
        new_somatic_voltages *= dead_cells_location
        new_spiked_neurons *= dead_cells_location
        # set this to avoid overlflow
        time_since_last_spike = self.cap_array(
            time_since_last_spike, upper_limit)
        self.state["time_since_last_spike"] = time_since_last_spike
        # print("new")
        # return 1

class IzhikevichSoma(BaseIntegrateAndFireSoma):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        population_size = self.population_size
        self.state["current_u"] = ncp.zeros(population_size)
        self.state["new_u"] = ncp.zeros(population_size)
        # check if homogenous distributions for all parameters
        print("Checking distributions")
        if self.membrane_recovery["distribution"] == "homogenous":
            self.state["membrane_recovery"] = self.membrane_recovery["value"]
            print("membrane recovery was homogenous")
        if self.resting_potential_variable["distribution"] == "homogenous":
            self.state["resting_potential_variable"] = self.resting_potential_variable["value"]

        if self.reset_voltage["distribution"] == "homogenous":
            self.state["reset_voltage"] = self.reset_voltage["value"]

        if self.reset_recovery_variable["distribution"] == "homogenous":
            self.state["reset_recovery_variable"] = self.reset_recovery_variable["value"]

        # Check if Izhikevich dependnet (a,b)
        if self.membrane_recovery["distribution"] == "Izhikevich":
            self.state["membrane_recovery"] = ncp.zeros(population_size)
            self.state["membrane_recovery"] += self.membrane_recovery["base_value"]
               
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            membrane_recovery_multiplier = self.membrane_recovery["multiplier_value"]
            membrane_recovery_variance = membrane_recovery_multiplier * random_variable
            self.state["membrane_recovery"] += membrane_recovery_variance

            if self.resting_potential_variable["distribution"] == "Izhikevich" and self.resting_potential_variable["dependent"] == "membrane_recovery":
                self.state["resting_potential_variable"] = ncp.zeros(
                    population_size)
                self.state["resting_potential_variable"] += self.resting_potential_variable["base_value"]
                #random_variable = ncp.random.uniform(0,1,population_size)

                resting_potential_multiplier = self.resting_potential_variable["multiplier_value"]
                resting_potential_variance = random_variable * resting_potential_multiplier
                self.state["resting_potential_variable"] += resting_potential_variance

        if self.resting_potential_variable["distribution"] == "Izhikevich" and not (self.resting_potential_variable["dependent"] == "membrane_recovery"):
            self.state["resting_potential_variable"] = ncp.zeros(
                population_size)
            self.state["resting_potential_variable"] += self.resting_potential_variable["base_value"]
            #random_variable = ncp.random.uniform(0,1,population_size)
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2

            resting_potential_multiplier = self.resting_potential_variable["multiplier_value"]
            resting_potential_variance = random_variable * resting_potential_multiplier
            self.state["resting_potential_variable"] += resting_potential_variance

        # check if dependent Izhikevich distribution, (c,d)
        if self.reset_recovery_variable["distribution"] == "Izhikevich":
            self.state["reset_recovery_variable"] = ncp.zeros(population_size)
            self.state["reset_recovery_variable"] += self.reset_recovery_variable["base_value"]
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2
            reset_recovery_multiplier = self.reset_recovery_variable["multiplier_value"]
            reset_recovery_variance = reset_recovery_multiplier * random_variable
            self.state["reset_recovery_variable"] += reset_recovery_variance

            if self.reset_voltage["distribution"] == "Izhikevich" and self.reset_voltage["dependent"] == "reset_recovery_variable":
                self.state["reset_voltage"] = ncp.zeros(population_size)
                self.state["reset_voltage"] += self.reset_voltage["base_value"]
                #random_variable = ncp.random.uniform(0,1,population_size)

                reset_voltage_multiplier = self.reset_voltage["multiplier_value"]
                reset_voltage_variance = random_variable * reset_voltage_multiplier
                self.state["reset_voltage"] += reset_voltage_variance

        if self.reset_voltage["distribution"] == "Izhikevich" and not (self.reset_voltage["dependent"] == "reset_recovery_variable"):
            self.state["reset_voltage"] = ncp.zeros(population_size)
            self.state["reset_voltage"] += self.reset_voltage["base_value"]
            #random_variable = ncp.random.uniform(0,1,population_size)
            random_variable = ncp.random.uniform(0, 1, population_size)
            random_variable = random_variable**2

            reset_voltage_multiplier = self.reset_voltage["multiplier_value"]
            reset_voltage_variance = random_variable * reset_voltage_multiplier
            self.state["reset_voltage"] += reset_voltage_variance

        reset_voltage = self.state["reset_voltage"]


        self.state["current_somatic_voltages"] = ncp.ones(
            population_size) * reset_voltage

        self.state["new_somatic_voltages"] = ncp.ones(
            population_size) * reset_voltage

        #self.state["current_u"][:,:] = self.state["reset_recovery_variable"] * self.state["current_somatic_voltages"]
        #self.state["new_u"][:,:] = self.state["reset_recovery_variable"] * self.state["current_somatic_voltages"]

        self.set_membrane_function()

    def set_membrane_function(self):
        time_step = self.time_step
        population_size = self.population_size
        summed_inputs = self.state["summed_inputs"]
        membrane_recovery = self.state["membrane_recovery"]
        resting_potential_variable = self.state["resting_potential_variable"]


        membrane_function = IzhivechikEquation(
            membrane_recovery, resting_potential_variable, summed_inputs, population_size)
        self.membrane_solver = RungeKutta2(membrane_function, time_step)

    def compute_new_values(self):
        time_step = self.time_step
        threshold = self.threshold
        upper_limit = self.temporal_upper_limit

        current_somatic_voltages = self.state["current_somatic_voltages"]
        current_u = self.state["current_u"]
        dead_cells_location = self.state["dead_cells_location"]
        new_somatic_voltages = self.state["new_somatic_voltages"]
        new_u = self.state["new_u"]
        new_spiked_neurons = self.state["new_spiked_neurons"]
        summed_inputs = self.state["summed_inputs"]
        time_since_last_spike = self.state["time_since_last_spike"]
        reset_recovery_variable = self.state["reset_recovery_variable"]


        time_since_last_spike += time_step

        v_u = ncp.concatenate(
            (current_somatic_voltages[:, :, ncp.newaxis], current_u[:, :, ncp.newaxis]), axis=2)
        delta_v_u = self.membrane_solver.advance(v_u, t=0)

        new_somatic_voltages += delta_v_u[:, :, 0]
        new_u += delta_v_u[:, :, 1]

        # set somatic values for neurons that have fired within the refractory period to zero
        #self.new_somatic_voltages *= self.time_since_last_spike > self.refractory_period
        self.set_refractory_values()
        new_spiked_neurons[:, :] = new_somatic_voltages > threshold
        new_u += new_spiked_neurons*reset_recovery_variable

        self.reset_spiked_neurons()

        # destroy values in dead cells
        new_somatic_voltages *= dead_cells_location
        new_spiked_neurons *= dead_cells_location

        # set this to avoid overlflow
        time_since_last_spike = self.cap_array(
            time_since_last_spike, upper_limit)
        new_u[:, :] = self.cap_array(new_u, upper_limit)
        # return "Summed inputs", ncp.amax(summed_inputs)
        #print("summed inputs in compute_new_values ",ncp.amax(summed_inputs))
        #print("new somatic voltages in compute_new_values ",ncp.amax(new_somatic_voltages))
        # print("new")
        # return 1

    def update_current_values(self):
        current_u = self.state["current_u"]
        new_u = self.state["new_u"]

        super().update_current_values()
        current_u[:, :] = new_u[:, :]
        # print("update")
        # return 2
