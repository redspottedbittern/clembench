import os
import json
import csv
import pandas as pd
import matplotlib.pyplot as plt

def load_json(filepath):
    """Loads JSON data from a given file path."""
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data

def extract_errors_and_round(data):
    """Extracts the error statistics and last round from the data."""
    error_keys = ["error_card_not_in_hand", "error_card_doesnt_follow_suit", 
                  "error_card_not_comprehensible", "error_prediction_int_not_possible"]

    # Extracting errors for the current episode
    errors = {error_key: data.get(error_key, 0) for error_key in error_keys}
    
    # Add the last round to the data
    errors["last_round"] = int(data.get("last_round", 0))
    
    return errors

def write_errors_to_csv(all_error_stats, filename='error_summary.csv'):
    """Writes the extracted error data, including last round, to a CSV file."""
    if not all_error_stats:
        print("No valid data to write.")
        return

    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write header with the error keys + last round
        header = ["Episode"] + list(next(iter(all_error_stats.values())).keys())
        writer.writerow(header)

        for episode, error_data in all_error_stats.items():
            row = [episode] + [error_data.get(key, 0) for key in error_data.keys()]
            writer.writerow(row)

    print(f"Data written to {filename}")

def process_directory(root_dir):
    """Processes each episode directory and generates a CSV and plots for error statistics."""
    all_error_stats = {}

    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        if os.path.isdir(subdir_path):
            for episode_subdir in sorted(os.listdir(subdir_path)):
                episode_path = os.path.join(subdir_path, episode_subdir)

                if os.path.isdir(episode_path) and "interactions.json" in os.listdir(episode_path):
                    json_filepath = os.path.join(episode_path, "interactions.json")
                    data = load_json(json_filepath)

                    error_stats = extract_errors_and_round(data)
                    all_error_stats[episode_subdir] = error_stats

            if all_error_stats:
                csv_filename = os.path.join(subdir_path, 'error_summary.csv')
                write_errors_to_csv(all_error_stats, filename=csv_filename)

                #plot_individual_errors(csv_filename, subdir_path)
                plot_directory_average_errors(csv_filename, subdir_path)
            else:
                print(f"No valid episodes found in {subdir_path}")

def plot_individual_errors(csv_file_path, output_dir):
    """Plots individual error statistics per episode from the CSV using barplots."""
    df = pd.read_csv(csv_file_path)

    episodes = df['Episode']
    df_errors = df.drop(columns=['Episode'])

    # Creating the bar plot for errors per episode
    ax = df_errors.plot(kind='bar', stacked=False, figsize=(12, 6), colormap='Set3')

    plt.xticks(range(len(episodes)), episodes, rotation=45, ha='right')
    plt.xlabel('Episode')
    plt.ylabel('Error Count')
    plt.title(f'Error Count per Episode - {os.path.basename(output_dir)}')
    plt.legend(title='Error Type')
    plt.tight_layout()  # Adjust layout to avoid clipping

    output_file = os.path.join(output_dir, 'errors_per_episode.png')
    plt.savefig(output_file)
    plt.show()

def plot_directory_average_errors(csv_file_path, output_dir):
    """Plots the average error count per directory over the episodes."""
    df = pd.read_csv(csv_file_path)

    # Calculating the average error counts across episodes, including the last round
    average_errors = df.drop(columns=['Episode']).mean().reset_index()
    average_errors.columns = ['Error Type', 'Average Count']

    # Creating the bar plot for average errors per directory
    plt.figure(figsize=(10, 6))

    colors = plt.cm.get_cmap('tab10', len(average_errors))  # Different colors for each bar
    bars = plt.bar(average_errors['Error Type'], average_errors['Average Count'], color=colors(range(len(average_errors))))

    plt.xlabel('Error Type')
    plt.ylabel('Average Count')
    plt.title(f'{os.path.basename(output_dir)}')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()  # Adjust layout to avoid clipping

    # Adding numbers on top of the bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')

    output_file = os.path.join(output_dir, 'average_errors_per_directory.png')
    plt.savefig(output_file)
    plt.show()


def plot_average_errors(root_dir):
    """Aggregates and plots the overall average error counts across all episodes as a colorful barplot."""
    all_data = pd.DataFrame()

    for subdir in sorted(os.listdir(root_dir)):
        subdir_path = os.path.join(root_dir, subdir)

        if os.path.isdir(subdir_path) and 'error_summary.csv' in os.listdir(subdir_path):
            file_path = os.path.join(subdir_path, 'error_summary.csv')
            df = pd.read_csv(file_path)

            all_data = pd.concat([all_data, df])

    if not all_data.empty:
        # Calculating the overall average errors, including last round
        average_errors = all_data.drop(columns=['Episode']).mean().reset_index()
        average_errors.columns = ['Error Type', 'Average Count']

        # Save the averaged error data to a CSV in the root directory
        avg_csv_filename = os.path.join(root_dir, 'overall_average_errors.csv')
        average_errors.to_csv(avg_csv_filename, index=False)
        print(f"Overall average error data saved to {avg_csv_filename}")

        # Plotting the overall average error counts, including last round
        plt.figure(figsize=(10, 6))

        colors = plt.cm.get_cmap('tab10', len(average_errors))  # Using a color map
        bars = plt.bar(average_errors['Error Type'], average_errors['Average Count'], color=colors(range(len(average_errors))))

        plt.xlabel('Error Type')
        plt.ylabel('Average Count')
        plt.title('Overall Average Errors per Episode')
        plt.grid(True)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()  # Adjust layout to avoid clipping

        # Adding numbers on top of the bars
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval, round(yval, 2), ha='center', va='bottom')

        plt.savefig('overall_average_errors_per_episode.png')
        plt.show()


if __name__ == "__main__":
    root_directory = os.getcwd()
    
    process_directory(root_directory)
    plot_average_errors(root_directory)
