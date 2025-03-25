import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from collections import defaultdict

"""
    Nc -- number of component
    t_begin
    t_end
    C_iM -- preventive cost
    C_s -- setup cost
    C_iP -- specific cost
    C_iU -- unavailability cost
    C_d -- a positive constant representing downtime cost rate related to production loss
    d_i -- maintenance duration of component i
    t_i -- execution time of component i
    N_RM -- number of repairmem
    G -- group
    B_S -- setup cost saving
    B_U -- unavailability cost saving
    P -- penalty cost
    EB -- cost benefit = B_S + B_U + P
"""

# Load the Excel file
file_path_1 = "dataset/data.xlsx"
file_path_2 = "dataset/activity.xlsx"
df1 = pd.read_excel(file_path_1)
df2 = pd.read_excel(file_path_2)
# Load input
component = df1['Component']
alpha = df1['Alpha']
d = df1['Average maintenance duration']
# cost = df1['Replacement cost']
beta = df1['Beta']

t = df2['Replacement time']
ID_activity = df2['ID activity']
ID_component = df2['ID component']
map_activity_to_IDcomponent = list(zip(ID_activity, ID_component))      # list of tuple (ID_component, ID_activity)   
map_activity_to_replacement_time = list(zip(ID_activity, t))            # list of tuple (ID_component, ID_activity)
t_begin = df2['Begin'][0]
t_end = df2['End'][0]

GENOME_LENGTH = 17                                                      # number of possible group
POPULATION_SIZE = 60
GENERATIONS = 500
p_c_min = 0.6
p_c_max = 0.9
p_m_min = 0.01
p_m_max = 0.1

C_s = 500
C_d = 100

m = 1                                                                   # Number of repairmen
w_max = 7                                                               # Maximum number of iterations for binary search

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
            value = df1.loc[df1['ID'] == d, 'Average maintenance duration'].iloc[0]
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
            value = df1.loc[df1['ID'] == d, 'Alpha'].iloc[0]
            alpha.append(value)
        group_to_alpha.append((group, alpha))
    return group_to_alpha


# mapping group of component to group of beta using output from mapping_activity_to_componentID()
def mapping_IDcomponent_to_beta(G_component):
    group_to_beta = []
    for group, id_component in G_component:
        beta = []
        for d in id_component:
            value = df1.loc[df1['ID'] == d, 'Beta'].iloc[0]
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

def mapping_to_UI(genome):
    N, G_activity = decode(genome)
    G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
    G_duration, _ = mapping_IDcomponent_to_duration(G_component)
    replacement_time = mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity)
    return G_duration, G_component, replacement_time


# ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## 
# # # ## ## ## ## ## ## ## ## ## ## ## # Test main # ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## 

# genome = random_genome(GENOME_LENGTH)
# print(genome)
# fitness_value = fitness_function(genome, C_s, C_d)
# print("Fitness value = ", fitness_value)


# def linear_ranking_selection(population, fitness_values):
#     sorted_population = [x for _, x in sorted(zip(fitness_values, population))]
#     probabilities = [(2*(i+1))/(POPULATION_SIZE*(POPULATION_SIZE+1)) for i in range(POPULATION_SIZE)]
#     print("prob",probabilities)
#     print(len(probabilities))
#     selected = random.choices(sorted_population, weights=probabilities, k=len(population))
#     return selected


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

# best_individual, best_fitness = genetic_algorithm(GENOME_LENGTH, m, POPULATION_SIZE, GENERATIONS, p_c_min, p_c_max, p_m_min, p_m_max, C_s, C_d)
# print(f"The best individual is: {best_individual} with fitness: {best_fitness}")

# G_duration, G_component, replacement_time = mapping_to_UI(best_individual)
# print(G_duration)

def build_component_dict(durations_in_group, components_in_each_group, replacement_time_in_group):
    """
    Build a dictionary keyed by component, where each component's value is a dict
    with two lists: 'duration' and 'replacement_time'.
    """
    
    # Convert the "durations in group" and "replacement time in group" tuples
    # into dictionaries keyed by group for easy lookup
    durations_dict = dict(durations_in_group)
    replacements_dict = dict(replacement_time_in_group)
    
    # Create a dictionary keyed by component
    # Each component will have a list of durations and replacement times
    component_dict = defaultdict(lambda: {"duration": [], "replacement_time": []})
    
    # Populate component_dict
    for group, comp_list in components_in_each_group:
        group_durations = durations_dict[group]
        group_replacements = replacements_dict[group]
        
        for i, comp in enumerate(comp_list):
            component_dict[comp]["duration"].append(group_durations[i])
            component_dict[comp]["replacement_time"].append(group_replacements[i])
    
    return dict(component_dict)

def plot_replacement_times(component_dict):
    
    # Create the figure and axis
    fig, ax = plt.subplots()

    # For each component, plot its replacement times on the x-axis
    # and the component ID (or name) on the y-axis.
    for comp_id, data in component_dict.items():
        replacements = data["replacement_time"]
        
        # We'll have one or more x-values (the replacements) and a matching list of y-values (comp_id repeated)
        y_values = [comp_id] * len(replacements)
        
        # Scatter plot for this component
        ax.scatter(replacements, y_values, color='blue', label = 'Estimated preventive maintenance')
    
    # Label axes
    ax.set_xlabel("Time")
    ax.set_ylabel("Component")

    # Optional: adjust the y-ticks to show each component distinctly (especially if comp_id are integers)
    # If you prefer integer ticks only:
    plt.yticks(sorted(component_dict.keys()))
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.title("Component Replacement Times")
    # plt.legend(loc='upper right')
    plt.show()

def plot_replacement_times_both_plans(individual_plan, estimate_plan):
    """Plot replacement times from both plans on a single horizontal scatter plot,
    using 'o' markers for the Individual Plan and 'x' markers for the Estimate Plan."""
    
    # We'll assume both plans have the same set of component names
    components = list(individual_plan.keys())
    
    plt.figure()
    
    for i, comp in enumerate(components):
        # Extract replacement times for both plans
        times_indiv = individual_plan[comp]['replacement_time']
        times_est = estimate_plan[comp]['replacement_time']
        
        # For the legend, we only set the label on the first component’s plots
        if i == 0:
            plt.scatter(times_indiv, [i]*len(times_indiv),
                        marker='o', label='Individual Plan')
            plt.scatter(times_est, [i]*len(times_est),
                        marker='x', label='Estimate Plan')
        else:
            plt.scatter(times_indiv, [i]*len(times_indiv), marker='o')
            plt.scatter(times_est, [i]*len(times_est), marker='x')
    
    # Label axes
    plt.xlabel('Replacement Time')
    plt.ylabel('Component')
    
    # Replace numeric y-ticks with component labels
    plt.yticks(range(len(components)), components)
    
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    # Add a legend so we can distinguish the two plans
    plt.legend()
    
    # Add a title (optional)
    plt.title('Replacement Times: Individual vs. Estimate Plans')
    
    # Show the figure
    plt.show()


def rename_dict_keys_with_excel(component_dict, excel_file_path):
    """
    Read an Excel file with columns 'ID' and 'Component'
    and convert the integer keys of component_dict to
    the corresponding component names. The rest of the
    structure remains unchanged.
    """
    # 1. Read the Excel file
    df = pd.read_excel(excel_file_path)  # Make sure 'ID' and 'Component' columns exist

    # 2. Build a lookup dict: {ID_value: Component_name}
    id_to_name = dict(zip(df['ID'], df['Component']))

    # 3. Create a new dictionary with keys = component names
    component_dict_renamed = {}
    for comp_id, comp_data in component_dict.items():
        # Look up the name of the component in the id_to_name dictionary
        comp_name = id_to_name.get(comp_id, f"Unknown_{comp_id}")
        component_dict_renamed[comp_name] = comp_data

    return component_dict_renamed

def calculate_info(genome):
    N, G_activity = decode(genome)
    G_duration, G_component, replacement_time = mapping_to_UI(genome)
    # print("G_duration: ", G_duration)
    # print("G_component: ", G_component)
    # print("replacement_time: ", replacement_time)
    component_dict = build_component_dict(
        G_duration, G_component, replacement_time
    )
    renamed_dict = rename_dict_keys_with_excel(component_dict, file_path_1)

    d_Gk = calculate_d_Gk(G_duration, m, w_max)
    _ , t_group = penalty_cost(G_activity)
    estimate_duration = convert_right_form(G_component, d_Gk)
    estimate_replacement_time = convert_right_form(G_component, t_group)
    estimate_component_dict = build_component_dict(
        estimate_duration, G_component, estimate_replacement_time
    )
    estimate_renamed_dict = rename_dict_keys_with_excel(estimate_component_dict, file_path_1)
    return renamed_dict, estimate_renamed_dict

def convert_right_form(components, durations):
    """
    Replaces the index list in each tuple in `components` with a list of the corresponding
    duration repeated as many times as there were indices.
    
    Parameters:
    - components (list[tuple[int, list[int]]]): 
        Each element is a tuple of the form (component_id, list_of_indices).
    - durations (list[float]): 
        Durations for each component, where durations[component_id - 1] is the duration.
        
    Returns:
    - list[tuple[int, list[float]]]: A new list of tuples with the second element replaced by 
      a list of repeated durations.
    """
    return [
        (comp_id, [durations[comp_id - 1]] * len(indices))
        for comp_id, indices in components
    ]