import os
import json
import csv
from pathlib import Path

def read_csv(file_path):
    csv_data = []
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row.pop(next(iter(row)))
            csv_data.append(row)
    return csv_data

def update_csv_data(csv_data, model, experiment, episode, extracted_data):
    csv_data_to_append = []
    for row in csv_data:
        if (row['model'] == model and 
            row['experiment'] == experiment and 
            row['episode'] == episode):

            for metric, value in extracted_data.items():
                new_row = {
                'game': 'wizardsapprentice',
                'model': model,
                'experiment': experiment,
                'episode': episode,
                'metric': metric,
                'value': value
                }
                csv_data_to_append.append(new_row)
        else:
            continue

    csv_data.append(csv_data_to_append)
            
def process_json_file(json_file, per_episode = False):
    with open(json_file, 'r') as f:
        data = json.load(f)

        if per_episode == True:
            required_fields = [
                "last_round",
                "predictions",
                "tricks_per_player",
                "points",
            ]

            extracted_data = {field: data.get(field, "N/A") for field in required_fields}
            output = []
            limit = 100
            for field, value in extracted_data.items():
                if field == "last_round":
                    limit = int(value)
                    continue
                for key, value in value.items():
                    if int(key) < limit:
                        new_row = {
                            'round': str(key),
                            str(field): str(value['Gandalf'])
                        }
                        output.append(new_row)
                    else:
                        pass

            return output
            
        else:
            required_fields = [
                "last_round",
                "error_card_not_in_hand",
                "error_card_doesnt_follow_suit",
                "error_card_not_comprehensible",
                "error_prediction_int_not_possible",
                "forced_card",
            ]
            
            extracted_data = {field: data.get(field, "N/A") for field in required_fields}

            extracted_data['syntax_errors'] = extracted_data['error_card_not_comprehensible']
            extracted_data['semantics_errors'] = extracted_data['error_card_not_in_hand'] + extracted_data['error_card_doesnt_follow_suit'] + extracted_data['error_prediction_int_not_possible']

            return extracted_data


def process_model_folder(results_path, empty_csv, per_episode=False):
    for experiment_folder in os.listdir(results_path):
        model = str(experiment_folder)
        experiment_path = os.path.join(results_path, experiment_folder)
        if os.path.isdir(experiment_path):
            experiment_path = os.path.join(experiment_path, 'wizardsapprentice/')
            for experiment_folder in os.listdir(experiment_path):
                experiment = experiment_folder
                episode_path = os.path.join(experiment_path, experiment_folder)
                if os.path.isdir(episode_path):
                    for episode_folder in os.listdir(episode_path):
                        episode = str(episode_folder)
                        json_path = os.path.join(episode_path, episode_folder)
                        if os.path.isdir(json_path):
                            for file in os.listdir(json_path):
                                if file == "interactions.json":
                                    if per_episode == True:
                                        json_file = os.path.join(json_path, file)
                                        extracted_data = process_json_file(json_file, per_episode == True)

                                        combined_data = {}

                                        for entry in extracted_data:

                                            round_num = entry['round']

                                            # If the round is not in the combined_data, initialize an empty dictionary
                                            if round_num not in combined_data:
                                                combined_data[round_num] = {
                                                    'game': 'wizardsapprentice',
                                                    'model': model,
                                                    'experiment': experiment,
                                                    'episode': episode,
                                                    'round': str(round_num),
                                                    'predictions': None,
                                                    'tricks_per_player': None,
                                                    'points': None
                                                }

                                            # Based on the available keys, populate the appropriate field
                                            if 'predictions' in entry:
                                                combined_data[round_num]['predictions'] = str(entry['predictions'])
                                            elif 'tricks_per_player' in entry:
                                                combined_data[round_num]['tricks_per_player'] = str(entry['tricks_per_player'])
                                            elif 'points' in entry:
                                                combined_data[round_num]['points'] = str(entry['points'])
                                            else:
                                                raise KeyError
                                            
                                            if None not in combined_data[round_num].values():
                                                empty_csv.append(combined_data[round_num])

                                    else:
                                        json_file = os.path.join(json_path, file)
                                        extracted_data = process_json_file(json_file)
                                        for metric, value in extracted_data.items():
                                            new_row = {
                                            'game': 'wizardsapprentice',
                                            'model': model,
                                            'experiment': experiment,
                                            'episode': episode,
                                            'metric': metric,
                                            'value': str(value)
                                            }
                                            empty_csv.append(new_row)

def write_csv(file_path, csv_data):
    if csv_data:
        fieldnames = csv_data[0].keys()
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in csv_data:
                writer.writerow(row)

def main():
    results_path = "./results"
    results_csv = "./results/raw.csv"
    output_csv = "./results/raw_episodes.csv"
        
    # Read existing CSV data
    csv_data = read_csv(results_csv)

    # Process JSON files and update CSV data
    empty_csv = []
    process_model_folder(results_path, empty_csv)
    print(len(csv_data))
    print(len(empty_csv))
    csv_data = csv_data + empty_csv
    print(len(csv_data))

    write_csv(output_csv, csv_data)


if __name__ == "__main__":
    main()