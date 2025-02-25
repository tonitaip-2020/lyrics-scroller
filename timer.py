import os
import csv

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Iterate over all .csv files in the current directory
for filename in os.listdir(current_directory):
    if filename.endswith('.csv'):
        # Full path to the file
        file_path = os.path.join(current_directory, filename)

        # Read the content of the CSV file
        with open(file_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            rows = list(reader)

        # Shift the times in the first column by 0.5 seconds
        for row in rows:
            try:
                # Modify the first column (time) by adding 0.5 seconds
                row[0] = str(float(row[0]) + 0.5)
            except ValueError:
                # In case of an empty or malformed row, skip modification
                continue

        # Write the updated content back to the same file
        with open(file_path, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(rows)

        print(f"Processed {filename}")
