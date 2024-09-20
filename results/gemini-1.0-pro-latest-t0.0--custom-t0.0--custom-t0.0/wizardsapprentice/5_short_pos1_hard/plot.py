import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
file_path = 'gandalf_points_summary.csv'
df = pd.read_csv(file_path)

# Calculate the average points across episodes for each round
df['Average Points'] = df[['episode_0 Points', 'episode_1 Points', 'episode_2 Points', 
                           'episode_3 Points', 'episode_4 Points', 'episode_5 Points']].mean(axis=1)

# Filter data from Round 1 to 12
df_filtered = df[(df['Round'] >= 1) & (df['Round'] <= 12)].sort_values(by='Round')

# Plot the data
plt.figure(figsize=(10, 6))
plt.plot(df_filtered['Round'], df_filtered['Average Points'], marker='o')
plt.xlabel('Round')
plt.ylabel('Average Points')
plt.title('Average Points per Round (Rounds 1-12)')
plt.grid(True)

# Save the plot to a PNG file
plt.savefig('average_points_rounds_1_to_12.png')

# Optionally, display the plot as well
plt.show()
