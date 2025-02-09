import math
import simpy
import random
import os
import csv


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


def patient(env, patient_id, patient_type, registration, cw1, cw2, x_ray, plaster, stats, cw_limit):
    """
    Simulates a patients process through the emergency room (Task 2)
    """
    arrival_time = env.now  # Record arrival time

    # Registration: R ->
    with registration.request() as req:
        yield req
        reg_time = triangular_dist(0.2, 0.5, 1.0)
        yield env.timeout(reg_time)

    # Allocation to CW1 or CW2: -> CW ->
    casualty_ward = cw2 if random.random() < 0.4 and len(cw2.queue) < cw_limit else cw1

    # Wait until doctors arrive
    if env.now < 30:
        yield env.timeout(30-env.now)

    # Doctors handle patients in CW1/CW2
    with casualty_ward.request() as req:
        yield req
        cw_time = get_cw_time(cw1, cw2, casualty_ward)
        yield env.timeout(cw_time)

    # Type 1: Xray -> CW -> Exit
    if patient_type == 1: 
        with x_ray.request() as req:
            yield req
            x_time = triangular_dist(2.0, 2.8, 4.1)
            yield env.timeout(x_time)
        with casualty_ward.request() as req:
            yield req
            cw_time = get_cw_time(cw1, cw2, casualty_ward)
            yield env.timeout(cw_time)

    # Type 2: -> Plaster -> Exit
    elif patient_type == 2: 
        with plaster.request() as req:
            yield req
            plaster_time = triangular_dist(3.0, 3.8, 4.7)
            yield env.timeout(plaster_time)
    
    # Type 3: -> Xray -> Plaster -> Xray -> CW -> Exit
    elif patient_type == 3:  
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
        with casualty_ward.request() as req:
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


def generate_patients(env, num_patients, registration, cw1, cw2, x_ray, plaster, stats, cw_limit):
    """
    Generates patients arriving at the emergency department
    """
    for i in range(num_patients):
        interarrival_time = random.expovariate(1 / 0.3)
        yield env.timeout(interarrival_time)
        patient_type = random.choices([1, 2, 3, 4], weights=[35, 20, 5, 40], k=1)[0]
        env.process(patient(env, i, patient_type, registration, cw1, cw2, x_ray, plaster, stats, cw_limit))


def run_simulation(num_patients=250, cw_limit=1):
    
    """
    Runs emergency room simulation

    Paramters:
        num_patients (int): Number of patients for simulation
        cw_limit (int): Max queue size of casualty ward 2
    """
    env = simpy.Environment()

    # Sets seed for reproducibility
    random.seed(10) 

    # Defines resources
    registration = simpy.Resource(env, capacity=1)
    cw1 = simpy.Resource(env, capacity=2)
    cw2 = simpy.Resource(env, capacity=2)
    x_ray = simpy.Resource(env, capacity=2)
    plaster = simpy.Resource(env, capacity=1)

    # Statistics dictionary
    stats = {"patients": []}

    env.process(generate_patients(env, num_patients, registration, cw1, cw2, x_ray, plaster, stats, cw_limit))

    # Starts simulation
    env.run()

    # Calculate statistics and save it in CSV
    results = calc_statistics(stats, cw_limit)
    save_statistics(results)

def calc_statistics(stats, cw_limit):
    """
    Calulates and displays statistics of the simulation

    Parameters:
        stats (dict): Stats of each simulated patient
        cw_limit (int): Maximum siz of CW2 queue
    
    Results:
        dict: A dictionary containing the calculated statistics
    """
    total_patients = len(stats["patients"])
    print(f"Total patients processed: {total_patients}")
    print(f"Maximum size of CW2 queue: {cw_limit}")

    # Group patients by type
    types = {1: [], 2: [], 3: [], 4: []}
    for patient in stats["patients"]:
        types[patient["type"]].append(patient["total_time"])

    results = {"cw_limit": 0, "overall_avg_time": 0, "standard_deviation": 0, "types": {}}

    results["cw_limit"] = cw_limit

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


def save_statistics(results, filename = "results/Task2.csv"):
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
        "Count Type 4", "Avg. Time Type 4",
        "Casualty Ward 2 Limit"
    ]

    file_exists = os.path.exists(filename)

    with open(filename, "a" if file_exists else "w", newline="") as file:
        writer = csv.writer(file, delimiter=";")

        # Write header if the file is new
        if not file_exists:
            writer.writerow(header)

        # Write data from results
        row = [
            f"{results['overall_avg_time']:.2f}".replace(".", ","),
            f"{results['standard_deviation']:.2f}".replace(".", ","),
            results["types"][1]["count"], f"{results['types'][1]['avg_time']:.2f}".replace(".", ","),
            results["types"][2]["count"], f"{results['types'][2]['avg_time']:.2f}".replace(".", ","),
            results["types"][3]["count"], f"{results['types'][3]['avg_time']:.2f}".replace(".", ","),
            results["types"][4]["count"], f"{results['types'][4]['avg_time']:.2f}".replace(".", ","),
            results["cw_limit"]
        ]
        writer.writerow(row)

# Hauptprogramm
if __name__ == "__main__":
    run_simulation()
