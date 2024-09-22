import os
import pandas as pd
import matplotlib.pyplot as plt

# Use the current directory as root
root_dir = os.getcwd()  # Gets the current working directory
dataframes = []
labels = []

# Loop through subdirectories
for subdir, _, _ in os.walk(root_dir):
    wizard_apprentice_dir = os.path.join(subdir, 'wizardsapprentice')
    csv_file = os.path.join(wizard_apprentice_dir, 'overall_average_errors.csv')
    
    if os.path.exists(csv_file):
        # Read the CSV file
        df = pd.read_csv(csv_file)
        df.set_index('Error Type', inplace=True)  # Set 'Error Type' as index
        dataframes.append(df['Average Count'])
        
        # Truncate the label at the second hyphen
        subdir_name = os.path.basename(subdir)
        truncated_label = '-'.join(subdir_name.split('-')[:2])  # Keep only the first two parts
        labels.append(truncated_label)

# Combine all dataframes into a single one
combined_df = pd.concat(dataframes, axis=1)
combined_df.columns = labels  # Set the column names to the truncated labels we collected

# First plot: Error Type grouped by subdirectory
fig, ax = plt.subplots(figsize=(15, 8))
combined_df.plot(kind='bar', ax=ax, width=0.8)
plt.title('Average Errors by Type Across Models')
plt.xlabel('Error Type')
plt.ylabel('Average Count')
plt.xticks(rotation=45)
plt.legend(title='Subdirectories', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add exact numbers on top of the bars
for container in ax.containers:
    ax.bar_label(container, fmt='%.2f', label_type='edge')

# Adjust layout to make room for the x-axis labels
plt.tight_layout()

# Save the first plot as PNG
plt.savefig('average_errors_plot.png')

# Second plot: Subdirectory grouped by Error Type
fig, ax = plt.subplots(figsize=(15, 8))
combined_df.T.plot(kind='bar', ax=ax, width=0.8)
plt.title('Average Errors by Model Across Error Types')
plt.xlabel('Subdirectory')
plt.ylabel('Average Count')
plt.xticks(rotation=45)
plt.legend(title='Error Types', bbox_to_anchor=(1.05, 1), loc='upper left')

# Add exact numbers on top of the bars
for container in ax.containers:
    ax.bar_label(container, fmt='%.2f', label_type='edge')

# Adjust layout to make room for the x-axis labels
plt.tight_layout()

# Save the second plot as PNG
plt.savefig('average_errors_by_subdirectory_plot.png')

# Show the plots
plt.show()
