import random
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

# Load the Excel file
file_path_1 = 'data.xlsx'
file_path_2 = 'activity.xlsx'
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
POPULATION_SIZE = 100
MUTATION_RATE = 0.01
CROSSOVER_RATE = 0.7
GENERATIONS = 1500

C_s = 50
C_d = 10

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
    # print(f"Components ID in group: {G_component}")
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
genome = [15, 13, 10, 1, 17, 12, 10, 11, 3, 8, 14, 7, 3, 9, 5, 6, 11]
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


"""

# Create a DataFrame based on the provided data
data2 = {
    "Cost saving": [26638.497, 27061.693, 27061.693, 27061.693, 27061.693, 27061.693, 27061.693],
    "Number of repairmen": [1, 2, 3, 4, 5, 6, 7]
}

df3 = pd.DataFrame(data2)

# Plotting the line chart
plt.figure(figsize=(10, 6))
plt.plot(df3["Number of repairmen"], df3["Cost saving"], marker='o', linestyle='--', color='b')
plt.xlabel('Number of repairmen')
plt.ylabel('Cost saving [euros]')
plt.xticks(df3["Number of repairmen"])
plt.show()



import pandas as pd
import matplotlib.pyplot as plt


# Create a DataFrame based on the provided data
data2 = {
    "Number of repairmen": [1, 2, 3, 4, 5, 6, 7],
    "Unavailability period [hours]": [30.996, 22.532, 22.532, 22.532, 22.532, 22.532, 22.532]
}

df2 = pd.DataFrame(data2)

# Plotting the line chart
plt.figure(figsize=(10, 6))
plt.plot(df2["Number of repairmen"], df2["Unavailability period [hours]"], marker='o', linestyle='--', color='b')
plt.xlabel('Number of repairmen')
plt.ylabel('Unavailability period [hours]')
plt.xticks(df2["Number of repairmen"])


plt.show()
"""





from collections import defaultdict

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



import matplotlib.pyplot as plt

def plot_replacement_times(component_dict):
    """
    Create a scatter plot where each component is on the y-axis and
    its replacement times are plotted along the x-axis.
    
    component_dict: dict with structure:
        {
          component_id: {
            'duration': [...],
            'replacement_time': [...]
          },
          ...
        }
    """
    # Create the figure and axis
    fig, ax = plt.subplots()

    # For each component, plot its replacement times on the x-axis
    # and the component ID (or name) on the y-axis.
    for comp_id, data in component_dict.items():
        replacements = data["replacement_time"]
        
        # We'll have one or more x-values (the replacements) and a matching list of y-values (comp_id repeated)
        y_values = [comp_id] * len(replacements)
        
        # Scatter plot for this component
        ax.scatter(replacements, y_values)
    
    # Label axes
    ax.set_xlabel("Time")
    ax.set_ylabel("Component")

    # Optional: adjust the y-ticks to show each component distinctly (especially if comp_id are integers)
    # If you prefer integer ticks only:
    plt.yticks(sorted(component_dict.keys()))
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.title("Component Replacement Times")
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

def mapping_to_UI(genome):
    N, G_activity = decode(genome)
    G_component = mapping_activity_to_componentID(map_activity_to_IDcomponent, G_activity)
    G_duration, _ = mapping_IDcomponent_to_duration(G_component)
    replacement_time = mapping_activity_to_replacement_time(map_activity_to_replacement_time, G_activity)
    return G_duration, G_component, replacement_time


def calculate_info(genome):
    G_duration, G_component, replacement_time = mapping_to_UI(genome)
    print("G_duration: ", G_duration)
    print("G_component: ", G_component)
    print("replacement_time: ", replacement_time)

    component_dict = build_component_dict(
        G_duration, G_component, replacement_time
    )

    renamed_dict = rename_dict_keys_with_excel(component_dict, file_path_1)

    d_Gk = calculate_d_Gk(G_duration, m, w_max)
    print("d_Gk: ", d_Gk)
    _ , t_group = penalty_cost(G_activity)
    print("t_group: ", t_group)
    estimate_duration = convert_right_form(G_component, d_Gk)
    print("estimate_duration: ", estimate_duration)
    estimate_replacement_time = convert_right_form(G_component, t_group)
    print("estimate_replacement_time: ", estimate_replacement_time)

    estimate_component_dict = build_component_dict(
        estimate_duration, G_component, estimate_replacement_time
    )
    estimate_renamed_dict = rename_dict_keys_with_excel(estimate_component_dict, file_path_1)
    print(renamed_dict)
    print(estimate_renamed_dict)

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

# # Example: print the data for component 0
# # print("Component 0:", component_dict[1])
# print(component_dict)

# renamed_dict = rename_dict_keys_with_excel(component_dict, file_path_1)

# # Now the dictionary keys match the "Component" names from the spreadsheet
# print(renamed_dict)

# plot_replacement_times(renamed_dict)

renamed_dict, estimate_renamed_dict = calculate_info(genome)

# component_dict = build_component_dict(
#         G_duration, G_component, replacement_time
#     )
# print(component_dict)

# print(f"Optimal replacement time for each group: {t_group}")
# print("t_group:", t_group)
# print(np.shape(t_group))

# d_Gk = calculate_d_Gk(G_duration, m, w_max)
# print(d_Gk)

