import random
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

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

# # Load the Excel file
# file_path_1 = "../dataset/data.xlsx"
# file_path_2 = "../dataset/activity.xlsx"
# df1 = pd.read_excel(file_path_1)
# df2 = pd.read_excel(file_path_2)
# # Load input
# component = df1['Component']
# alpha = df1['Alpha']
# d = df1['Average maintenance duration']
# # cost = df1['Replacement cost']
# beta = df1['Beta']

# t = df2['Replacement time']
# ID_activity = df2['ID activity']

# # print(ID_activity)
# # print(type(ID_activity))
# ID_component = df2['ID component']
# map_activity_to_IDcomponent = list(zip(ID_activity, ID_component))      # list of tuple (ID_component, ID_activity)   
# map_activity_to_replacement_time = list(zip(ID_activity, t))            # list of tuple (ID_component, ID_activity)
# t_begin = df2['Begin'][0]
# t_end = df2['End'][0]
# print(map_activity_to_IDcomponent)


# Path to the JSON files
file_path_json_1 = '../dataset/component.json'
file_path_json_2 = '../dataset/activity.json'

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
print(map_activity_to_IDcomponent)
t_begin = data2['window']['Begin']
t_end = data2['window']['End']


GENOME_LENGTH = 17                                                      # number of possible group
POPULATION_SIZE = 60
MUTATION_RATE = 0.01
CROSSOVER_RATE = 0.7
GENERATIONS = 1500

C_s = 500
C_d = 100

m = 1                                                                   # Number of repairmen
w_max = 7                                                               # Maximum number of iterations for binary search




# Now `data` is a Python dictionary
# print(data['window'])        # Access the window block
# print(data['failure'])    # Access the first failure entry
# print(t_begin)
# print(t_end)



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

# # mapping group of component to group of alpha using output from mapping_activity_to_componentID()
# def mapping_IDcomponent_to_name(G_component):
#     group_to_name = []
#     for group, id_component in G_component:
#         name = []
#         for d in id_component:
#             value = df1.loc[df1['ID'] == d, 'Component'].iloc[0]
#             name.append(value)
#         group_to_name.append((group, name))
#     return group_to_name


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
    print(f"Components ID in group: {G_component}")
    G_duration, G_total_duration = mapping_IDcomponent_to_duration(G_component)
    print(f"Durations in group: {G_duration}")
    # print(f"Total durations in group: {G_total_duration}")
    d_Gk = calculate_d_Gk(G_duration, m, w_max)
    print(d_Gk)
    print("Unavailability period: ", sum(d_Gk))
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
        # print(f"Replacement time: {t_i_list}, Alpha: {alpha_i_list}, Beta: {beta_i_list}")
        # Initial guess for t
        initial_guess = [0.0]
        # Perform the minimization
        result = minimize(wrapper_P_Gk, initial_guess, args=(t_i_list, alpha_i_list, beta_i_list))
        # Print the results
        print("Minimum value of the function: ", np.round(result.fun, decimals=3))
        print("Value of t at the minimum: ", np.round(result.x, decimals=3))
        # print("---------------------------------------------------")
        P.append(np.round(result.fun, decimals=3))
        t_group.append(np.round(result.x, decimals=3))
    t_group = [float(arr[0]) for arr in t_group]
    return P, t_group

# cost benefit EB = B_S + B_U - P
def cost_benefit(B_S, B_U, P):
    EB = np.array(B_S) + np.array(B_U) - np.array(P)
    return EB

# # Test main
# genome = random_genome(GENOME_LENGTH)
# genome = [13, 15, 17, 9, 8, 13, 15, 14, 12, 2, 6, 4, 5, 3, 14, 5, 12]    #1496.6997279200023
genome = [16, 3, 2, 9, 1, 11, 3, 5, 10, 7, 16, 17, 8, 12, 9, 9, 10]
N, G_activity = decode(genome)
print(f"Genome: {genome}")
print(f"Activities in each group: {G_activity}")
B_S = saveup_cost_saving(G_activity, C_s)
print(f"Setup cost saving in each group: {B_S}")
B_U = unavailability_cost_saving(G_activity, C_d, m, w_max)
print(f"Unavailability cost saving in each group: {B_U}")

G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
print(f"Components in each group: {G_component}")

G_duration, _ = mapping_IDcomponent_to_duration(G_component)
print(f"Durations in group: {G_duration}")

G_alpha = mapping_IDcomponent_to_alpha(G_component)
print(f"Alpha in each group: {G_alpha}")

G_beta = mapping_IDcomponent_to_beta(G_component)
print(f"Beta in each group: {G_beta}")

replacement_time = mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity)
print(f"Replacement time in each group: {replacement_time}")

P, t_group = penalty_cost(G_activity)
print(f"Penalty cost: {P}")

EB = cost_benefit(B_S, B_U, P)
print(f"Cost benefit EB = B_S + B_U + P: {EB}")

def fitness(EB):
    return np.sum(EB)

a = fitness(EB)
print(a)



# import matplotlib.pyplot as plt

# def plot_replacement_times(component_dict):
#     """
#     Create a scatter plot where each component is on the y-axis and
#     its replacement times are plotted along the x-axis.
    
#     component_dict: dict with structure:
#         {
#           component_id: {
#             'duration': [...],
#             'replacement_time': [...]
#           },
#           ...
#         }
#     """
#     # Create the figure and axis
#     fig, ax = plt.subplots()

#     # For each component, plot its replacement times on the x-axis
#     # and the component ID (or name) on the y-axis.
#     for comp_id, data in component_dict.items():
#         replacements = data["replacement_time"]
        
#         # We'll have one or more x-values (the replacements) and a matching list of y-values (comp_id repeated)
#         y_values = [comp_id] * len(replacements)
        
#         # Scatter plot for this component
#         ax.scatter(replacements, y_values)
    
#     # Label axes
#     ax.set_xlabel("Time")
#     ax.set_ylabel("Component")

#     # Optional: adjust the y-ticks to show each component distinctly (especially if comp_id are integers)
#     # If you prefer integer ticks only:
#     plt.yticks(sorted(component_dict.keys()))
#     plt.grid(axis='y', linestyle='--', alpha=0.7)
#     plt.title("Component Replacement Times")
#     plt.show()


def mapping_to_UI(genome):
    N, G_activity = decode(genome)
    G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
    G_duration, _ = mapping_IDcomponent_to_duration(G_component)
    replacement_time = mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity)
    return G_duration, G_component, replacement_time

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
                "Module": comp_names,
                "Replacement time": rep_time,
                "Duration": duration
            }
            combined_data[group_key].append(entry)

    return combined_data

G_duration, G_component, replacement_time = mapping_to_UI(genome)
print("G_duration: ", G_duration)
print("G_component: ", G_component)
print("replacement_time: ", replacement_time)

G_component_named = convert_component_ids_to_names(G_component, file_path_json_1)
print(G_component_named)

result = combine_group_data(G_duration, G_component, replacement_time, G_component_named)
print(json.dumps(result, indent=4, ensure_ascii=False))

