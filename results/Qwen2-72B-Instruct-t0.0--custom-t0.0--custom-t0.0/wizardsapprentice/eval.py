import os
import json
import csv
import pandas as pd
import matplotlib.pyplot as plt

def load_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def extract_gandalf_points(data):
    gandalf_points = []
    for key, value in data["points"].items():
        gandalf_points.append((key, value.get("Gandalf", 0)))
        if key == data["last_round"]:
            break
    return dict(gandalf_points)

def write_to_csv(all_gandalf_points, filename='gandalf_points_summary.csv', limit_rounds=False):
    if not all_gandalf_points:
        print("No valid data to write.")
        return

    first_episode = next(iter(all_gandalf_points.values()))
    all_keys = sorted(first_episode.keys(), key=lambda x: int(x)) 

    if limit_rounds:
        all_keys = [key for key in all_keys if int(key) <= 9]

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        header = ["Round"] + [f"{episode} Points" for episode in all_gandalf_points.keys()]
        writer.writerow(header)

        for key in all_keys:
            row = [key] + [all_gandalf_points[episode].get(key, 0) for episode in all_gandalf_points.keys()]
            writer.writerow(row)

    print(f"Data written to {filename}")


def process_directory(root_dir):
    all_gandalf_points = {}

    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        if os.path.isdir(subdir_path):
            for episode_subdir in sorted(os.listdir(subdir_path)):
                episode_path = os.path.join(subdir_path, episode_subdir)

                if os.path.isdir(episode_path) and "interactions.json" in os.listdir(episode_path):
                    json_filepath = os.path.join(episode_path, "interactions.json")
                    data = load_json(json_filepath)

                    gandalf_points = extract_gandalf_points(data)
                    all_gandalf_points[episode_subdir] = gandalf_points

            if all_gandalf_points:
                csv_filename = os.path.join(subdir_path, 'gandalf_points_summary.csv')
                write_to_csv(all_gandalf_points, filename=csv_filename)

                plot_individual_csv(csv_filename, subdir_path)
            else:
                print(f"No valid episodes found in {subdir_path}")

def plot_individual_csv(csv_file_path, output_dir):
    df = pd.read_csv(csv_file_path)

    df['Average Points'] = df[['episode_1 Points', 'episode_2 Points', 'episode_3 Points', 
                               'episode_4 Points', 'episode_5 Points']].mean(axis=1)

    #df_filtered = df[(df['Round'] >= 1) & (df['Round'] <= 12)].sort_values(by='Round')

    plt.figure(figsize=(10, 6))
    plt.plot(df['Round'], df['Average Points'], marker='o')
    plt.xlabel('Round')
    plt.ylabel('Average Points')
    plt.title(f'Average Points per Round - {os.path.basename(output_dir)}')
    plt.grid(True)

    output_file = os.path.join(output_dir, 'average_points_rounds.png')
    plt.savefig(output_file)
    plt.show()

def plot_average_points(root_dir):
    all_data = pd.DataFrame()

    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        if os.path.isdir(subdir_path) and 'gandalf_points_summary.csv' in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, 'gandalf_points_summary.csv')
            df = pd.read_csv(file_path)

            df['Average Points'] = df[['episode_1 Points', 'episode_2 Points', 'episode_3 Points', 
                                       'episode_4 Points', 'episode_5 Points']].mean(axis=1)

            #df_filtered = df[(df['Round'] >= 1) & (df['Round'] <= 12)]
            
            all_data = pd.concat([all_data, df])

    overall_avg_points = all_data.groupby('Round')['Average Points'].mean().reset_index()

    plt.figure(figsize=(10, 6))
    plt.plot(overall_avg_points['Round'], overall_avg_points['Average Points'], marker='o')
    plt.xlabel('Round')
    plt.ylabel('Average Points')
    plt.title('Overall Average Points per Round')
    plt.grid(True)

    plt.savefig('overall_average_points_rounds.png')
    plt.show()

if __name__ == "__main__":
    root_directory = os.getcwd()
    
    process_directory(root_directory)

    plot_average_points(root_directory)
