import math
import simpy
import random
import os
import csv
import pandas as pd
import matplotlib.pyplot as plt

"""Task 3 is to implement a priority Que to the implementation of Task 1. 
    The only differences between the versions are the files the data gets saved in and the Priorities 
    chosen in the Patient function

    This is Version 3:
    Priorities are given to to every Patient determined by Time of Arrival.(Earlier Arrival will get priortized

    Changes in Priorities are in line:
    81,93,120
      
    Its important to admit, that priority que of simpy uses integer numbers and lower number get priortized
    """

# Sets seed for reproducibility
random.seed(10)

def triangular_dist(minimum, mode, maximum):
    """
    Wrapper for the random.triangular function.

    Parameters:
        minimum (float): lower bound of distribution
        mode (float): midpoint of distribution
        maximum (float): upper bound of distribution
    
    Returns: 
        float: random value of given triangular distribution
    """
    return random.triangular(minimum, mode, maximum)

def get_cw_time(cw1, cw2, casualty_ward):
    """
    Gets the treatment time for casualty ward 1 or casualty ward 2 depending on the set casualty ward for the patient

    Paramters:
        cw1 (Resource): resource for casualty ward 1
        cw2 (Resource): resource for casualty ward 2
        casualty_ward (Resource): set casualty ward for patient x

    Returns:
        float: treatment time for CW1/CW2 
    """
    if casualty_ward == cw1 :
        return triangular_dist(1.5, 3.2, 5.0)
    elif casualty_ward == cw2:
        return triangular_dist(2.8, 4.1, 6.3)
    else:
        return 0


def patient(env, patient_id, patient_type, registration, cw1, cw2, x_ray, plaster, stats, prio):
    """
    Simulates a patients process through the emergency room (Task 3)
    """
    arrival_time = env.now  # Record arrival time

    # Registration: R ->
    with registration.request() as req:
        yield req
        reg_time = triangular_dist(0.2, 0.5, 1.0)
        yield env.timeout(reg_time)

    # Allocation to CW1 or CW2: -> CW ->
    casualty_ward = cw1 if random.random() < 0.6 else cw2

    # Wait until doctors arrive
    if env.now < 30:
        yield env.timeout(30-env.now)

    # Doctors handle patients in CW1/CW2
    #Priority in Caualty wards get applied by the arrival time
    #The earlier a Patient arrives, the more he gets priortized
    with casualty_ward.request(priority=int(arrival_time)) as req:
        yield req
        cw_time = get_cw_time(cw1, cw2, casualty_ward)
        yield env.timeout(cw_time)

    # Type 1: Xray -> CW (Prio) -> Exit
    if patient_type == 1:
        with x_ray.request() as req:
            yield req
            x_time = triangular_dist(2.0, 2.8, 4.1)
            yield env.timeout(x_time)
            prio = -1
        with casualty_ward.request(priority=int(arrival_time)) as req:
                yield req
                cw_time = get_cw_time(cw1, cw2, casualty_ward)
                yield env.timeout(cw_time)

    # Type 2: -> Plaster -> Exit
    elif patient_type == 2: 
        with plaster.request() as req:
            yield req
            plaster_time = triangular_dist(3.0, 3.8, 4.7)
            yield env.timeout(plaster_time)

    # Type 3: -> Xray -> Plaster -> Xray -> CW (Prio) -> Exit
    elif patient_type == 3:  # Gips erneuern und Röntgen
        with x_ray.request() as req:
            yield req
            x_time = triangular_dist(2.0, 2.8, 4.1)
            yield env.timeout(x_time)
        with plaster.request() as req:
            yield req
            plaster_time = triangular_dist(3.0, 3.8, 4.7)
            yield env.timeout(plaster_time)
        with x_ray.request() as req:
            yield req
            x_time = triangular_dist(2.0, 2.8, 4.1)
            yield env.timeout(x_time)
            prio = -1
        with casualty_ward.request(priority=int(arrival_time)) as req:
            yield req
            cw_time = get_cw_time(cw1, cw2, casualty_ward)
            yield env.timeout(cw_time)
    
    # Type 4: -> Exit
    else:
        pass

    # Calculate time of patient
    departure_time = env.now
    total_time = departure_time - arrival_time
    # Save time in statistics dictionary
    stats["patients"].append({"id": patient_id, "type": patient_type, "total_time": total_time})



def generate_patients(env, num_patients, registration, cw1, cw2, x_ray, plaster, stats):
    """
    Generates patients arriving at the emergency department
    """
    for i in range(num_patients):
        interarrival_time = random.expovariate(1 / 0.3)
        yield env.timeout(interarrival_time)
        patient_type = random.choices([1, 2, 3, 4], weights=[35, 20, 5, 40], k=1)[0]

        env.process(patient(env, i, patient_type, registration, cw1, cw2, x_ray, plaster, stats, prio = 0))



# Simulationsumgebung
def run_simulation(num_patients=250):
    """
    Runs emergency room simulation

    Paramters:
        num_patients (int): Number of patients for simulation
    """
    env = simpy.Environment()

    # Defines resources
    registration = simpy.Resource(env, capacity=1)
    cw1 = simpy.PriorityResource(env, capacity=2)
    cw2 = simpy.PriorityResource(env, capacity=2)
    x_ray = simpy.Resource(env, capacity=2)
    plaster = simpy.Resource(env, capacity=1)

    # Statistics dictionary
    stats = {"patients": []}

    env.process(generate_patients(env, num_patients, registration, cw1, cw2, x_ray, plaster, stats))

    # Starts simulation
    env.run()

    # Calculate statistics and save it in CSV
    results = calc_statistics(stats)
    save_statistics(results)
    save_raw_data(stats)

def calc_statistics(stats):
    """
    Calulates and displays statistics of the simulation

    Parameters:
        stats (dict): Stats of each simulated patient
    
    Results:
        dict: A dictionary containing the calculated statistics
    """
    total_patients = len(stats["patients"])
    print(f"Total patients processed: {total_patients}")

    # Group patients by type
    types = {1: [], 2: [], 3: [], 4: []}
    for patient in stats["patients"]:
        types[patient["type"]].append(patient["total_time"])

    results = {"overall_avg_time": 0, "standard_deviation": 0, "types": {}}

    for patient_type, times in types.items():
        if times:
            avg_time = sum(times) / len(times)
            print(f"Type {patient_type}: {len(times)} patients, Avg. time = {avg_time:.2f} minutes")
            results["types"][patient_type] = {"count": len(times), "avg_time": avg_time}
        else:
            print(f"Type {patient_type}: 0 patients")
            results["types"][patient_type] = {"count": 0, "avg_time": 0}

    # Overall average time
    all_times = [patient["total_time"] for patient in stats["patients"]]
    overall_avg_time = sum(all_times) / total_patients
    print(f"Overall average treatment time: {overall_avg_time:.2f} minutes")
    results["overall_avg_time"] = overall_avg_time

    # Standard deviation
    squared_differences = []
    for patient in stats["patients"]:
        squared_differences.append(math.pow(patient["total_time"] - overall_avg_time, 2))
    standard_deviation = math.sqrt(sum(squared_differences) / (total_patients - 1))
    print(f"Standard deviation of treatment time: {standard_deviation:.2f} minutes")
    results["standard_deviation"] = standard_deviation

    return results

def save_raw_data(stats, filename = "results/raw_Task3v3.csv"):
    """
       Save the raw data to a defined CSV File in the results directory

        This was necesary for Task 3 as we want to take a look at Standard Deviation and
        calculating the overall Standard Deviation is way easier from the raww patient data.

       Parameters:
           stats (dict): patient data which want to be saved
           filename (str, optional): Path to the csv file, if doesnt exist will generate"""

    header = [
        "Total Time","Patient Type"
    ]

    file_exists = os.path.exists(filename)
    for patient in stats["patients"]:
        with open(filename, "a" if file_exists else "w", newline="") as file:
            writer = csv.writer(file, delimiter=";")

            # Write header if the file is new
            if not file_exists:
                writer.writerow(header)

            # Write data from stats

            row = [
                patient["total_time"], patient["type"]
            ]
            writer.writerow(row)
def save_statistics(results, filename = "results/Task3v3.csv"):
    """
    Save the calculated statistics to a defined CSV File in the results directory

    Parameters:
        results (dict): calculated statistics which want to be saved
        filename (str, optional): Path to the csv file, if doesnt exist will generate
    """
    header = [
        "Overall Average Time", "Standard Deviation",
        "Count Type 1", "Avg. Time Type 1",
        "Count Type 2", "Avg. Time Type 2",
        "Count Type 3", "Avg. Time Type 3",
        "Count Type 4", "Avg. Time Type 4"
    ]

    file_exists = os.path.exists(filename)

    with open(filename, "a" if file_exists else "w", newline="") as file:
        writer = csv.writer(file, delimiter=";")

        # Write header if the file is new
        if not file_exists:
            writer.writerow(header)

        # Write data from results
        row = [
            results['overall_avg_time'], results['standard_deviation'],
            results["types"][1]["count"], results['types'][1]['avg_time'],
            results["types"][2]["count"], results['types'][2]['avg_time'],
            results["types"][3]["count"], results['types'][3]['avg_time'],
            results["types"][4]["count"], results['types'][4]['avg_time']
        ]
        writer.writerow(row)

# Hauptprogramm
if __name__ == "__main__":
    # run simulation 100 times
    for i in range(0, 100):
        run_simulation()

    # read results from csv
    df = pd.read_csv(
        r'results\Task3v3.csv',
        engine='python', sep=';', header=0)


    # Plot Time overall and per Type
    plt.figure(figsize=(12, 8))
    boxplot1 = df.boxplot(
        column=["Overall Average Time", "Avg. Time Type 1", "Avg. Time Type 2", "Avg. Time Type 3", "Avg. Time Type 4"])
    plt.title('Average Time Overall/Per Patient Type', fontsize=20, pad=30)
    plt.xlabel("Patient Type", fontsize=16, labelpad=10)
    plt.ylabel("Average Time(min)", fontsize=16, labelpad=20)
    plt.show()

    # add a row with means
    df.loc['Mean'] = df.mean()

    # get the Maximum/Minimum of every column
    for c in df.columns:
        df.loc['Max {0}'.format(c)] = df.iloc[df[c].idxmax()]
        df.loc['Min {0}'.format(c)] = df.iloc[df[c].idxmin()]

    # add row with standard Deviation
    df.loc['Standard Deviation'] = df.std()

    # print the maxima/minima of Time and Patient Types
    df_test = df[['Overall Average Time', 'Standard Deviation', 'Avg. Time Type 1',
                  'Avg. Time Type 2', 'Avg. Time Type 3', 'Avg. Time Type 4', 'Count Type 1',
                  'Count Type 2', 'Count Type 3', 'Count Type 4']].tail(len(df.columns) * 2 + 2)
    print(df_test.to_string())