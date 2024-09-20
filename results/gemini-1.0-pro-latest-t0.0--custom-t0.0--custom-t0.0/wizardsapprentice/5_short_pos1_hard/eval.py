import os
import json
import csv

# Function to load the JSON data from a given file
def load_json(filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

# Function to extract Gandalf's points for each key in a single episode
def extract_gandalf_points(data):
    gandalf_points = []
    for key, value in data["points"].items():
        gandalf_points.append((key, value.get("Gandalf", 0)))  # Default to 0 if "Gandalf" key doesn't exist
    return dict(gandalf_points)

# Function to write all the episode data into a CSV file
def write_to_csv(all_gandalf_points, filename='gandalf_points_summary.csv'):
    # Get the keys from the first episode to use as row labels
    first_episode = next(iter(all_gandalf_points.values()))  # Get the first episode's data
    all_keys = sorted(first_episode.keys())  # Assuming all episodes have the same keys (1, 2, 3, etc.)

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write the header row
        header = ["Round"] + [f"{episode} Points" for episode in all_gandalf_points.keys()]
        writer.writerow(header)

        # Write the data rows for each key
        for key in all_keys:
            row = [key] + [all_gandalf_points[episode].get(key, 0) for episode in all_gandalf_points.keys()]
            writer.writerow(row)

    print(f"Data written to {filename}")

# Main script to process all subdirectories
def process_directory(root_dir):
    all_gandalf_points = {}

    # Loop through subdirectories (e.g., episode_0, episode_1, etc.)
    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        # Check if it's a directory and contains interactions.json
        if os.path.isdir(subdir_path) and "interactions.json" in os.listdir(subdir_path):
            json_filepath = os.path.join(subdir_path, "interactions.json")
            data = load_json(json_filepath)

            # Extract Gandalf's points for this episode
            gandalf_points = extract_gandalf_points(data)
            all_gandalf_points[subdir] = gandalf_points

    # Write the aggregated data to a CSV file
    if all_gandalf_points:
        write_to_csv(all_gandalf_points)
    else:
        print("No valid episodes found")

# Entry point for the script
if __name__ == "__main__":
    # Get the current directory
    root_directory = os.getcwd()  # This sets the root directory to the current working directory
    
    # Process the root directory and subdirectories
    process_directory(root_directory)
