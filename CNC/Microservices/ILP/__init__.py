from ILP_Generator import *
from IACO_Generator import * # Importamos el algoritmo IACO
from Solutions_Visualizer import *
from time import time
import os
import json
from Rabbitmq_queues import *


'''
this is the list of input elements:


'Number_of_Streams',
'Network_links', 
'Link_order_Descriptor', 
'Streams_Period', 
'Hyperperiod', 
'Frames_per_Stream', 
'Max_frames', 
'Num_of_Frames', 
'Model_Descriptor', 
'Model_Descriptor_vector', 
'Deathline_Stream', 
'Repetitions', 
'Repetitions_Descriptor', 
'Frame_Duration', 
'unused_links'
'''
# Variable para seleccionar algoritmo
USE_IACO_ALGORITHM = False  # Cambiar a True para usar IACO

def restructuring_dictionary(dictionary):
    correct_keys = []
    for key in dictionary.keys():
        new_key = tuple(key.split("_"))
        new_key = [int(x) for x in new_key]
        new_key = tuple(new_key)
        correct_keys.append(new_key)
    new_values = dictionary.values()
    zip_iterator = zip(correct_keys, new_values)
    final_dictionary = dict(zip_iterator)
    return final_dictionary

if __name__ == "__main__":

    preprocessing_flag = os.path.exists('/var/preprocessing.txt')
    if(preprocessing_flag):
        with open('/var/preprocessing.txt') as preprocessing_json_file:
            Preprocessed_data = json.load(preprocessing_json_file)

        print(Preprocessed_data['Deathline_Stream'])
        print("______________")
        print(Preprocessed_data['Streams_Period'])

        Deathline_Stream = {int(k): v for k, v in Preprocessed_data['Deathline_Stream'].items()}
        Streams_Period = {int(k): v for k, v in Preprocessed_data['Streams_Period'].items()}
        Model_Descriptor = restructuring_dictionary(Preprocessed_data['Model_Descriptor'])
        Frame_Duration = restructuring_dictionary(Preprocessed_data['Frame_Duration'])
        Model_Descriptor_vector = Preprocessed_data['Model_Descriptor_vector']
        Num_of_Frames = Preprocessed_data['Num_of_Frames']
        Link_order_Descriptor = Preprocessed_data['Link_order_Descriptor']
        Network_links = Preprocessed_data['Network_links']
        Adjacency_Matrix = Preprocessed_data['Adjacency_Matrix']
        Stream_Source_Destination = Preprocessed_data['Stream_Source_Destination']
        Links_per_Stream = Preprocessed_data['Links_per_Stream']
        Frames_per_Stream = Preprocessed_data['Frames_per_Stream']
        Streams_size = Preprocessed_data['Streams_size']
        Repetitions_Descriptor = Preprocessed_data['Repetitions_Descriptor']
        identificator = Preprocessed_data["identificator"]
        interface_Matrix = Preprocessed_data["interface_Matrix"]
        Hyperperiod = Preprocessed_data['Hyperperiod']
        Streams_links_paths = Preprocessed_data['Streams_links_paths']
        Repetitions = Preprocessed_data['Repetitions']
        Sources = Preprocessed_data['Sources']
        Destinations = Preprocessed_data['Destinations']

        if USE_IACO_ALGORITHM:
            print("Running IACO...")

            topology = [tuple(link) for link in Preprocessed_data["Network_links"]]
            flows = {sid: tuple(sd) for sid, sd in enumerate(Preprocessed_data["Stream_Source_Destination"])}
            link_capacities = {tuple(link): 1000 for link in Preprocessed_data["Network_links"]}
            flow_bandwidths = {
                sid: Streams_size[sid] / Streams_Period[str(sid)]
                for sid in range(Preprocessed_data["Number_of_Streams"])
            }

            iaco_result = improved_aco_scheduler(
                topology,
                flows,
                link_capacities,
                flow_bandwidths
            )

            Clean_offsets_collector = iaco_result["schedule"]
            Repetitions_Descriptor = [[0, stream_id] for stream_id in range(Preprocessed_data["Number_of_Streams"])]  # Dummy para compatibilidad

            ilp = {
                "Clean_offsets": Clean_offsets_collector,
                "Repetitions_Descriptor": Repetitions_Descriptor,
                "Streams_Period": Streams_Period,
                "Hyperperiod": Hyperperiod,
                "identificator": identificator,
                "linksInterfaces": Preprocessed_data["linksInterfaces"],
                "Network_links": Preprocessed_data['Network_links'],
                "unused_links": Preprocessed_data['unused_links']
            }

            print(ilp)
            json_ilp_payload = json.dumps(ilp, indent=4)
            send_message(json_ilp_payload, 'ilp-south')

        else:
            # Algoritmo ILP
            scheduler = ILP_Raagard_solver(
                Preprocessed_data['Number_of_Streams'],
                Preprocessed_data['Network_links'],
                Preprocessed_data['Link_order_Descriptor'],
                Streams_Period,
                Preprocessed_data['Hyperperiod'],
                Preprocessed_data['Frames_per_Stream'],
                Preprocessed_data['Max_frames'],
                Preprocessed_data['Num_of_Frames'],
                Model_Descriptor,
                Preprocessed_data['Model_Descriptor_vector'],
                Deathline_Stream,
                Preprocessed_data['Repetitions'],
                Preprocessed_data['Repetitions_Descriptor'],
                Preprocessed_data['unused_links'],
                Frame_Duration
            )

            instance, results = scheduler.instance, scheduler.results
            Feasibility_indicator, Result_offsets, Clean_offsets_collector, Results_latencies = ILP_results_visualizer(instance, Model_Descriptor_vector)
            print('This is the feasibility you are looking for', Feasibility_indicator)

            Full_scheduled_data = dataframe_printer(
                instance,
                Clean_offsets_collector,
                Results_latencies,
                Feasibility_indicator,
                Adjacency_Matrix,
                Stream_Source_Destination,
                Link_order_Descriptor,
                Links_per_Stream,
                Frames_per_Stream,
                Deathline_Stream,
                Streams_Period,
                Streams_size,
                Hyperperiod,
                Repetitions_Descriptor,
                identificator,
                interface_Matrix
            )

            json_Full_scheduled_data = json.dumps(Full_scheduled_data, indent=4)
            print("Working")

            with open("results.txt", "w") as f:
                f.write(json_Full_scheduled_data)

            Feasibility_indicator, Result_offsets, Clean_offsets_collector, Results_latencies = ILP_results_visualizer(instance, Model_Descriptor_vector)
            plot_network = Generate_network_graphic(Sources, Destinations)
            df = gantt_chart_generator(Result_offsets, Repetitions, Streams_Period)
            information_generator(Num_of_Frames, Streams_Period, Link_order_Descriptor, Network_links, Streams_links_paths)

            ilp = {}
            ilp["Clean_offsets"] = Clean_offsets_collector
            ilp["Repetitions_Descriptor"] = Repetitions_Descriptor
            ilp["Streams_Period"] = Streams_Period
            ilp["Hyperperiod"] = Hyperperiod
            ilp["identificator"] = identificator
            ilp["linksInterfaces"] = Preprocessed_data["linksInterfaces"]
            ilp["Network_links"] = Preprocessed_data['Network_links']
            ilp["unused_links"] = Preprocessed_data['unused_links']

            print(ilp)
            json_ilp_payload = json.dumps(ilp, indent=4)
            send_message(json_ilp_payload, 'ilp-south')

    else:
        print("There is not input data, check the previous microservices or the RabbitMQ logs")