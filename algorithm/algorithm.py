import random
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import sys
import parameters
from datetime import datetime

shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'user_input'))
sys.path.append(shared_path)


# Path to the JSON files
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path_json_1 = os.path.join(base_dir, '..', 'dataset', 'component.json')
file_path_json_2 = os.path.join(base_dir, '..', 'dataset', 'activity.json')

# Open and load the files
with open(file_path_json_1, 'r', encoding='utf-8') as file:
    data1 = json.load(file)

data2 = {   
    "window":   {
                    "Begin": 0.0,
                    "End": 1000.0
                },
    "failure":  [
                    {
                        "ID activity": 1,
                        "Replacement time": 173.298,
                        "ID component": "0"
                    },
                    {
                        "ID activity": 2,
                        "Replacement time": 346.596,
                        "ID component": "0"
                    },
                    {
                        "ID activity": 3,
                        "Replacement time": 519.895,
                        "ID component": "0"
                    },
                    {
                        "ID activity": 4,
                        "Replacement time": 693.193,
                        "ID component": "0"
                    },
                    {
                        "ID activity": 5,
                        "Replacement time": 866.491,
                        "ID component": "0"
                    },
                    {
                        "ID activity": 6,
                        "Replacement time": 179.545,
                        "ID component": "1"
                    },
                    {
                        "ID activity": 7,
                        "Replacement time": 359.09,
                        "ID component": "1"
                    },
                    {
                        "ID activity": 8,
                        "Replacement time": 538.635,
                        "ID component": "1"

                    },
                    {
                        "ID activity": 9,
                        "Replacement time": 718.179,
                        "ID component": "1"
                    },
                    {
                        "ID activity": 10,
                        "Replacement time": 897.724,
                        "ID component": "1"
                    },
                    {
                        "ID activity": 11,
                        "Replacement time": 208.829,
                        "ID component": "2"
                    },
                    {
                        "ID activity": 12,
                        "Replacement time": 417.658,
                        "ID component": "2"
                    },
                    {
                        "ID activity": 13,
                        "Replacement time": 626.487,
                        "ID component": "2"
                    },
                    {
                        "ID activity": 14,
                        "Replacement time": 835.316,
                        "ID component": "2"
                    },
                    {
                        "ID activity": 15,
                        "Replacement time": 548.357,
                        "ID component": "3"
                    },
                    {
                        "ID activity": 16,
                        "Replacement time": 627.938,
                        "ID component": "4"
                    },
                    {
                        "ID activity": 17,
                        "Replacement time": 732.33,
                        "ID component": "5"
                    }
                ]
}

# Load input
component = [entry["Module"] for entry in data1["component_list"]]
alpha = [entry["Alpha"] for entry in data1["component_list"]]
beta = [entry["Beta"] for entry in data1["component_list"]]

t = [entry["Replacement time"] for entry in data2["failure"]]
ID_activity = [entry["ID activity"] for entry in data2["failure"]]
ID_component = [entry["ID component"] for entry in data2["failure"]]
map_activity_to_IDcomponent = list(zip(ID_activity, ID_component))      # list of tuple (ID_component, ID_activity)   
map_activity_to_replacement_time = list(zip(ID_activity, t))            # list of tuple (ID_component, ID_activity)

t_begin = data2['window']['Begin']
t_end = data2['window']['End']

# Load input
# component = [entry["Module"] for entry in components]
# alpha = [entry["Alpha"] for entry in components]
# beta = [entry["Beta"] for entry in components]

# t = [entry["Replacement time"] for entry in data2["failure"]]
# ID_activity = [entry["ID activity"] for entry in data2["failure"]]
# ID_component = [entry["ID component"] for entry in data2["failure"]]
# map_activity_to_IDcomponent = list(zip(ID_activity, ID_component))      # list of tuple (ID_component, ID_activity)   
# map_activity_to_replacement_time = list(zip(ID_activity, t))            # list of tuple (ID_component, ID_activity)

# t_begin = data2['window']['Begin']
# t_end = data2['window']['End']

# genetic_algorithm_v2(components, setup_cost, no_repairmen, downtime_cost_rate):
#   component = [entry["Module"] for entry in components]
#   alpha = [entry["Alpha"] for entry in components]
#   beta = [entry["Beta"] for entry in components]


# User input
C_s = data1['setup_cost']                          # Setup cost
C_d = data1['downtime_cost_rate']                  # Downtime cost rate
m = data1['no_repairmen']                          # Number of repairmen

# Algorithm parameter
GENOME_LENGTH = len(ID_activity)                                                    
POPULATION_SIZE = parameters.POPULATION_SIZE
GENERATIONS = parameters.GENERATIONS
p_c_min = parameters.p_c_min
p_c_max = parameters.p_c_max
p_m_min = parameters.p_m_min
p_m_max = parameters.p_m_max
w_max = parameters.w_max       



# initialize genome
def random_genome(length):
    return [random.randint(1, length) for _ in range(length)]
    
# initialize population
def init_population(population_size, genome_length):
    return [random_genome(genome_length) for _ in range(population_size)]

# evaluation
def decode(genome):
    # Dictionary to map original group to new group starting from 1
    group_mapping = {}
    new_group_number = 1

    # Create mapping from original group to new group numbers
    for group in genome:
        if group not in group_mapping:
            group_mapping[group] = new_group_number
            new_group_number += 1

    # Dictionary to store new groups and their respective activities
    group_activities = {}

    # Populate the dictionary using the new group numbers
    for activity, group in enumerate(genome, start=1):
        new_group = group_mapping[group]
        if new_group in group_activities:
            group_activities[new_group].append(activity)
        else:
            group_activities[new_group] = [activity]

    # items(): method to return the dictionary's key-value pairs
    # sorted: displaying the Keys in Sorted Order
    # for group, activities in sorted(group_activities.items()):
    #     print(f"Group {group}: Activities {activities}")

    number_of_groups = len(group_activities)
    G_activity = sorted(group_activities.items())                       # group and its activity
    return number_of_groups, G_activity


# mapping group of activity to group of component using list of tuple map_activity_to_IDcomponent defined above
def mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity):
    # Create a dictionary to map each activity to its ID component
    dict_map = {activity: component for activity, component in map_activity_to_IDcomponent}

    # Initialize the result list
    group_to_components = []

    # Process each group and its activities
    for group, activities in G_activity:
        # Find the ID components for each activity in the current group
        components = [dict_map[activity] for activity in activities if activity in dict_map]
        # Append the result as a tuple (group, list of components)
        group_to_components.append((group, components))
    return group_to_components


# mapping group of activity to group of replacement time using list of tuple map_activity_to_replacement_time defined above
def mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity):
    # Create a dictionary to map each activity to its replacement time t
    dict_map = {activity: t for activity, t in map_activity_to_replacement_time}

    # Initialize the result list
    group_to_replacement_time = []

    # Process each group and its activities
    for group, activities in G_activity:
        # Find the time list for each activity in the current group
        time_list = [dict_map[activity] for activity in activities if activity in dict_map]
        # Append the result as a tuple (group, time list)
        group_to_replacement_time.append((group, time_list))
    return group_to_replacement_time


# mapping group of component to group of duration using output from mapping_activity_to_componentID()
# and calculate total duration of each group
def mapping_IDcomponent_to_duration(G_component):
    group_to_duration = []
    total_duration = []
    for group, id_component in G_component:
        duration = []
        for d in id_component:
            value = next(item["Average maintenance duration"] for item in data1["component_list"] if item["Component"] == d)
            duration.append(value)
        group_to_duration.append((group, duration))
        total_duration.append(sum(duration))
    return group_to_duration, total_duration                            # total_duration: sum_di


# mapping group of component to group of alpha using output from mapping_activity_to_componentID()
def mapping_IDcomponent_to_alpha(G_component):
    group_to_alpha = []
    for group, id_component in G_component:
        alpha = []
        for d in id_component:
            value = next(item["Alpha"] for item in data1["component_list"] if item["Component"] == d)
            alpha.append(value)
        group_to_alpha.append((group, alpha))
    return group_to_alpha


# mapping group of component to group of beta using output from mapping_activity_to_componentID()
def mapping_IDcomponent_to_beta(G_component):
    group_to_beta = []
    for group, id_component in G_component:
        beta = []
        for d in id_component:
            value = next(item["Beta"] for item in data1["component_list"] if item["Component"] == d)
            beta.append(value)
        group_to_beta.append((group, beta))
    return group_to_beta


# First Fit Decreasing (FFD) method
def first_fit_decreasing(durations, m, D):
    durations = sorted(durations, reverse=True)
    repairmen = [0] * m
    for duration in durations:
        # Find the first repairman who can take this activity
        for i in range(m):
            if repairmen[i] + duration <= D:
                repairmen[i] += duration
                break
        else:
            return False
    return repairmen

# Binary search for optimal total maintenance duration
def multifit(durations, m, w_max):
    durations = sorted(durations, reverse=True)
    D_low = max(durations[0], sum(durations) / m)
    D_up = max(durations[0], 2 * sum(durations) / m)
    
    for w in range(w_max):
        D = (D_up + D_low) / 2
        repairmen = first_fit_decreasing(durations, m, D)
        if repairmen:
            D_up = D
            min_maintenance_duration = max(repairmen)
        else:
            D_low = D
    return min_maintenance_duration

def calculate_d_Gk(G_duration, m, w_max):
    d_Gk = []
    for _, durations in G_duration:
        optimal_duration = multifit(durations, m, w_max)
        optimal_duration = round(optimal_duration, 3)
        d_Gk.append(optimal_duration)
    return d_Gk

# setup cost saving
def saveup_cost_saving(G_activity, C_s):
    B_S = []
    for group, activity in G_activity:
        buffer = (len(activity) - 1) * C_s
        B_S.append(buffer)
    return B_S                                                          # shape(B_S) = number of group

# unavailability cost saving
def unavailability_cost_saving(G_activity, C_d, m, w_max):
    G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
    G_duration, G_total_duration = mapping_IDcomponent_to_duration(G_component)
    d_Gk = calculate_d_Gk(G_duration, m, w_max)
    B_U = (np.array(G_total_duration) - np.array(d_Gk)) * C_d
    return B_U

# Define the piecewise function
def P_i(t, t_i, alpha_i, beta_i):
    delta_t = t - t_i
    if delta_t <= 0:
        return alpha_i * (delta_t)**2
    else:
        return beta_i * (delta_t)**2

# Define the sum function P_Gk
def P_Gk(t, t_i_list, alpha_i_list, beta_i_list):
    total_sum = 0
    for t_i, alpha_i, beta_i in zip(t_i_list, alpha_i_list, beta_i_list):
        total_sum += P_i(t, t_i, alpha_i, beta_i)
    return total_sum

# Define the wrapper function for minimization
def wrapper_P_Gk(t, t_i_list, alpha_i_list, beta_i_list):
    return P_Gk(t[0], t_i_list, alpha_i_list, beta_i_list)

# penalty cost
def penalty_cost(G_activity):
    G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
    G_alpha = mapping_IDcomponent_to_alpha(G_component)
    G_beta = mapping_IDcomponent_to_beta(G_component)
    replacement_time = mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity)
    P = []                                                                  # penalty cost in each group
    t_group = []                                                            # optimal time to minimize penalty cost in each group
    for i in range(len(G_alpha)):
        group, alpha_i_list = G_alpha[i]
        _, beta_i_list = G_beta[i]
        _, t_i_list = replacement_time[i]
        # Initial guess for t
        initial_guess = [0.0]
        # Perform the minimization
        result = minimize(wrapper_P_Gk, initial_guess, args=(t_i_list, alpha_i_list, beta_i_list))
        P.append(np.round(result.fun, decimals=3))
        t_group.append(np.round(result.x, decimals=3))
    t_group = [float(arr[0]) for arr in t_group]
    return P, t_group

# cost benefit EB = B_S + B_U + P
def cost_benefit(B_S, B_U, P):
    EB = np.array(B_S) + np.array(B_U) - np.array(P)
    return EB

# fitness function
def fitness_function(genome, C_s, C_d):
    N, G_activity = decode(genome)  
    B_S = saveup_cost_saving(G_activity, C_s)
    B_U = unavailability_cost_saving(G_activity, C_d, m, w_max)
    P, _ = penalty_cost(G_activity)
    EB = cost_benefit(B_S, B_U, P)
    fitness_value = np.sum(EB)
    return fitness_value


def linear_ranking_selection(population, fitness_values, num_groups=5):
    population_size = len(population)
    # Sort the population based on fitness
    sorted_population = [x for _, x in sorted(zip(fitness_values, population))]
    # Determine the size of each group
    group_size = population_size // num_groups
    # Assign selection probabilities to each group
    group_probabilities = [0.05, 0.10, 0.15, 0.25, 0.45]
    # Ensure that the sum of group probabilities is 1
    assert sum(group_probabilities) == 1, "Group probabilities must sum to 1"
    # Initialize list for selected individuals
    selected = []
    for _ in range(population_size):
        # Select a group based on the group probabilities
        group_index = random.choices(range(num_groups), weights=group_probabilities, k=1)[0]
        # Determine the start and end indices of the group in the sorted population
        start_index = group_index * group_size
        end_index = start_index + group_size
        # Handle the case where the last group may have fewer members due to integer division
        if group_index == num_groups - 1:
            end_index = population_size
        # Select a random individual from the chosen group
        selected_individual = random.choice(sorted_population[start_index:end_index])
        selected.append(selected_individual)
    return selected


def crossover(parent1, parent2, p_c):
    if random.random() < p_c:
        point1 = random.randint(1, len(parent1) - 2)
        point2 = random.randint(point1, len(parent1) - 1)
        child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
        child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]
        return child1, child2
    else:
        return parent1, parent2

def mutate(genome, p_m):
    if random.random() < p_m:
        i, j = random.sample(range(len(genome)), 2)
        genome[i], genome[j] = genome[j], genome[i]
    return genome

def genetic_algorithm(genome_length, m, population_size, generations, p_c_min, p_c_max, p_m_min, p_m_max, C_s, C_d):
    population = init_population(population_size, genome_length)
    best_solution = None
    best_fitness_value = -float('inf')
    for generation in range(generations):
        fitness_values = [fitness_function(genome, C_s, C_d) for genome in population]
        map_fitness_to_population = sorted(zip(fitness_values, population), reverse=True)
        # print("map value: ", list(map_fitness_to_population))
        # Update best solution
        current_best_fitness = map_fitness_to_population[0][0]
        current_best_genome = map_fitness_to_population[0][1]
        
        if current_best_fitness >= best_fitness_value:
            best_fitness_value = current_best_fitness
            best_solution = current_best_genome
        
        print(f"Generation {generation} | Best fitness = {best_fitness_value} | Best genome: {best_solution}")

        # Elitism
        sorted_population = [x for _, x in map_fitness_to_population]
        new_population = sorted_population[:2]
   
        f_avg = np.mean(fitness_values)
        f_max = np.max(fitness_values)

        # Linear ranking selection and crossover
        selected = linear_ranking_selection(population, fitness_values)
      
        for i in range(2, len(selected), 2):
            parent1 = selected[i]
            parent2 = selected[i+1]
            f_c = max(fitness_function(parent1, C_s, C_d), fitness_function(parent2, C_s, C_d))
            p_c = p_c_max - ((p_c_max - p_c_min) * (f_c - f_avg) / (f_max - f_avg)) if f_c > f_avg else p_c_max
            child1, child2 = crossover(parent1, parent2, p_c)
            new_population.extend([child1, child2])
        # Mutation
        for i in range(2, len(new_population)):
            f_m = fitness_function(new_population[i], C_s, C_d)
            p_m = p_m_max - ((p_m_max - p_m_min) * (f_max - f_m) / (f_max - f_avg)) if f_m > f_avg else p_m_max
            new_population[i] = mutate(new_population[i], p_m)
        
        population = new_population

    return best_solution, best_fitness_value

def convert_right_form(components, durations):
    return [
        (comp_id, [durations[comp_id - 1]] * len(indices))
        for comp_id, indices in components
    ]


def mapping_to_UI(genome):
    N, G_activity = decode(genome)
    G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
    G_duration, _ = mapping_IDcomponent_to_duration(G_component)
    replacement_time = mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity)
    
    d_Gk = calculate_d_Gk(G_duration, m, w_max)
    _ , t_group = penalty_cost(G_activity)
    estimate_duration = convert_right_form(G_component, d_Gk)
    estimate_replacement_time = convert_right_form(G_component, t_group)
    return G_duration, G_component, replacement_time, estimate_duration, estimate_replacement_time

def convert_component_ids_to_names(G_component, json_path):
    # Load the JSON file with component info
    with open(json_path, 'r', encoding='utf-8') as f:
        component_data = json.load(f)

    # Create a mapping from ID to Component name
    id_to_name = {entry["Component"]: entry["Module"] for entry in component_data["component_list"]}

    # Replace component IDs with names
    G_component_named = []
    for group_id, component_ids in G_component:
        names = [id_to_name[comp_id] for comp_id in component_ids]
        G_component_named.append((group_id, names))

    return G_component_named

def combine_group_data(G_duration, G_component, replacement_time, G_component_named):
    combined_data = {}

    for (g_id, durations), (_, components), (_, replacements), (_, names) in zip(G_duration, G_component, replacement_time, G_component_named):
        group_key = f"Group {g_id}"
        combined_data[group_key] = []

        for comp_id, rep_time, duration, comp_names in zip(components, replacements, durations, names):
            entry = {
                "Component": comp_id,
                "Equipment name": comp_names,
                "Replacement time": rep_time,
                "Duration": duration
            }
            combined_data[group_key].append(entry)

    return combined_data

def output_json_file(best_individual, best_fitness, t_begin, t_end):
    _, G_component, _, estimate_duration, estimate_replacement_time = mapping_to_UI(best_individual)
    G_duration_individual, G_component_individual, replacement_time_individual, _, _ = mapping_to_UI(ID_activity) 

    G_component_named = convert_component_ids_to_names(G_component, file_path_json_1)
    group_maintenance = combine_group_data(estimate_duration, G_component, estimate_replacement_time, G_component_named)

    G_component_named_individual = convert_component_ids_to_names(G_component_individual, file_path_json_1)
    individual_maintenance = combine_group_data(G_duration_individual, G_component_individual, replacement_time_individual, G_component_named_individual)
    final_output = {
                        "Cost savings": best_fitness,
                        "Grouping maintenance": group_maintenance,
                        "Individual maintenance": individual_maintenance,
                        "Time window": {
                            "Begin": t_begin,
                            "End": t_end
                        }
                   }

    # Define your folder and filename
    output_folder = "../output"
    output_filename = "result.json"

    # Create the folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Create the full path
    output_path = os.path.join(output_folder, output_filename)

    # Write the JSON file with correct formatting
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)

    print(f"File saved to: {output_path}")

# Function to convert the algorithm output to the proper format
def format_output(best_individual, best_fitness, t_begin, t_end):
    """
    Convert the algorithm output to the proper format for JSON output.
    Args:
        best_individual (list): The best individual from the genetic algorithm.
        best_fitness (float): The fitness value of the best individual.
        t_begin (float): The beginning of the time window.
        t_end (float): The end of the time window.
    Returns:
        dict: A dictionary containing the formatted output.
    """
    # Call your existing mapping functions
    _, G_component, _, estimate_duration, estimate_replacement_time = mapping_to_UI(best_individual)
    G_duration_individual, G_component_individual, replacement_time_individual, _, _ = mapping_to_UI(ID_activity)
    
    # Convert component IDs to names
    G_component_named = convert_component_ids_to_names(G_component, file_path_json_1)
    group_maintenance = combine_group_data(estimate_duration, G_component, estimate_replacement_time, G_component_named)
    
    G_component_named_individual = convert_component_ids_to_names(G_component_individual, file_path_json_1)
    individual_maintenance = combine_group_data(G_duration_individual, G_component_individual, replacement_time_individual, G_component_named_individual)
    
    # Create output dictionary with proper key names to match the expected format
    output = {
        "Cost savings": best_fitness,
        "Grouping maintenance": group_maintenance,
        "Individual maintenance": individual_maintenance,
        "Time window": {
            "Begin": t_begin,
            "End": t_end
        }
    }

    return output

# Function to process API request and prepare Kafka event data
def async_processing_grouping_maintenance_request(
    setup_cost: float,
    downtime_cost_rate: float,
    no_repairmen: int,
    components: list,
    smart_service: str,
    production_module: str):
    """
    Process grouping maintenance request and prepare for Kafka publishing.
    This function is called from the API and handles the complete workflow:
    1. Run genetic algorithm with provided parameters
    2. Format output using existing format_output function
    3. Prepare Kafka event data with results
    
    Args:
        setup_cost (float): Setup cost for maintenance operations
        downtime_cost_rate (float): Downtime cost rate
        no_repairmen (int): Number of available repairmen
        components (list): List of component data from API request
        smart_service (str): Smart service identifier
        production_module (str): Production module identifier
        
    Returns:
        dict: Event data ready for Kafka publishing
    """
    try:
        # Algorithm parameters (using components length or default)
        genome_length = len(components) if components else 10
        population_size = 50
        generations = 100
        p_c_min, p_c_max = 0.5, 0.9
        p_m_min, p_m_max = 0.01, 0.1
        t_begin, t_end = 0.0, 1000.0
        
        # Run the genetic algorithm
        best_individual, best_fitness = genetic_algorithm(
            genome_length,
            no_repairmen,
            population_size,
            generations,
            p_c_min, p_c_max,
            p_m_min, p_m_max,
            setup_cost,
            downtime_cost_rate
        )
        
        # Format the algorithm output
        algorithm_results = format_output(best_individual, best_fitness, t_begin, t_end)
        
        # Prepare Kafka event data
        event_data = {
            "description": "The grouping maintenance optimization has been successfully completed for the production module '{}'.".format(production_module),
            "module": production_module,
            "timestamp": datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "priority": "MID", # Should be handled appropriately from the algorithm
            "eventType": "Grouping Maintenance Process Completion",
            "sourceComponent": "Predictive Maintenance",
            "smartService": smart_service,
            "topic": "smart-service-event",
            "results": algorithm_results
        }
        
        return event_data
        
    except Exception as e:
        # Prepare error event data
        error_event_data = {
            "description": f"Grouping maintenance optimization failed: {str(e)}",
            "module": production_module,
            "timestamp": datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "priority": "MID",
            "eventType": "Grouping Maintenance Process Error",
            "sourceComponent": "Predictive Maintenanc",
            "smartService": smart_service,
            "topic": "smart-service-event",
            "results": None
        }
        
        return error_event_data

####### Execution ########

# Create a List of Components - data1['component_list']
# Defined setup_cost, no_repairement etc..
# Create a duplicate genetic algorithm that will take these as input
# .. = genetic_algorithm_v2(components, setup_cost, no_repairmen, downtime_cost_rate)
best_individual, best_fitness = genetic_algorithm(GENOME_LENGTH, m, POPULATION_SIZE, GENERATIONS, p_c_min, p_c_max, p_m_min, p_m_max, C_s, C_d)
print(f"The best individual is: {best_individual} with fitness: {best_fitness}")

output_json_file(best_individual, best_fitness, t_begin, t_end)

