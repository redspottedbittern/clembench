import json
import csv

# Load the JSON data from the "interactions.json" file
def load_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

# Function to extract Gandalf's points for each key
def extract_gandalf_points(data):
    gandalf_points = []
    for key, value in data["points"].items():
        gandalf_points.append((key, value.get("Gandalf", 0)))  # Default to 0 if "Gandalf" key doesn't exist
    return gandalf_points

# Write Gandalf's points to a CSV file
def write_to_csv(gandalf_points, filename='gandalf_points.csv'):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Key", "Gandalf's Points"])
        writer.writerows(gandalf_points)
    print(f"Data written to {filename}")

# Main script
if __name__ == "__main__":
    # Load data from interactions.json
    data = load_json('interactions.json')

    # Extract Gandalf's points
    gandalf_points = extract_gandalf_points(data)

    # Write the result to CSV
    write_to_csv(gandalf_points)
