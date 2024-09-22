import os
import json
import csv
import pandas as pd
import matplotlib.pyplot as plt

def load_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def extract_scores(data):
    scores = {
        "Request Count": data["episode scores"].get("Request Count", 0),
        "Parsed Request Count": data["episode scores"].get("Parsed Request Count", 0),
        "Violated Request Count": data["episode scores"].get("Violated Request Count", 0)
    }
    return scores

def write_to_csv(all_scores, filename='scores_summary.csv'):
    if not all_scores:
        print("No valid data to write.")
        return

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        header = ["Episode", "Request Count", "Parsed Request Count", "Violated Request Count"]
        writer.writerow(header)

        for episode, scores in all_scores.items():
            row = [episode, scores["Request Count"], scores["Parsed Request Count"], scores["Violated Request Count"]]
            writer.writerow(row)

    print(f"Data written to {filename}")

def process_directory(root_dir):
    all_scores = {}

    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        if os.path.isdir(subdir_path):
            for episode_subdir in sorted(os.listdir(subdir_path)):
                episode_path = os.path.join(subdir_path, episode_subdir)

                if os.path.isdir(episode_path) and "scores.json" in os.listdir(episode_path):
                    json_filepath = os.path.join(episode_path, "scores.json")
                    data = load_json(json_filepath)

                    scores = extract_scores(data)
                    all_scores[episode_subdir] = scores

            if all_scores:
                csv_filename = os.path.join(subdir_path, 'scores_summary.csv')
                write_to_csv(all_scores, filename=csv_filename)

                plot_individual_csv(csv_filename, subdir_path)
            else:
                print(f"No valid episodes found in {subdir_path}")

def plot_individual_csv(csv_file_path, output_dir):
    df = pd.read_csv(csv_file_path)

    # Bar plot
    df.plot(x='Episode', y=['Request Count', 'Parsed Request Count', 'Violated Request Count'], 
            kind='bar', figsize=(10, 6))

    plt.xlabel('Episode')
    plt.ylabel('Counts')
    plt.title(f'Request, Parsed, and Violated Counts - {os.path.basename(output_dir)}')
    plt.grid(True, axis='y')

    output_file = os.path.join(output_dir, 'request_counts.png')
    plt.savefig(output_file)
    plt.show()

def plot_average_counts(root_dir):
    all_data = pd.DataFrame()

    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        if os.path.isdir(subdir_path) and 'scores_summary.csv' in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, 'scores_summary.csv')
            df = pd.read_csv(file_path)
            
            all_data = pd.concat([all_data, df])

    average_counts = all_data.groupby('Episode').mean().reset_index()

    # Bar plot
    average_counts.plot(x='Episode', y=['Request Count', 'Parsed Request Count', 'Violated Request Count'], 
                        kind='bar', figsize=(10, 6))

    plt.xlabel('Episode')
    plt.ylabel('Average Counts')
    plt.title('Average Request, Parsed, and Violated Counts per Episode')
    plt.grid(True, axis='y')

    plt.savefig('overall_average_counts.png')
    plt.show()

if __name__ == "__main__":
    root_directory = os.getcwd()
    
    process_directory(root_directory)

    plot_average_counts(root_directory)
