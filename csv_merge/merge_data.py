import pandas as pd
from pathlib import Path

# File location
folder = Path('./data')
output_filename = "merged_stats.csv"

# Data init
all_data_frames = []
file_count = 0

print("Starting processing...")

# Read inputs
for file in folder.iterdir():
    if file.is_file() and file.suffix.lower() in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip() # Clean whitespace
            
            # Check the columns
            required_cols = ['Movement', 'Finger', 'C0', 'C1', 'C2', 'C3']
            if all(col in df.columns for col in required_cols):
                all_data_frames.append(df)
                file_count += 1
                print(f"Loaded: {file.name}")
            else:
                print(f"Skipping {file.name}: Missing required columns.")
                
        except Exception as e:
            print(f"Error reading {file.name}: {e}")

if file_count > 0:
    # Combine data
    full_df = pd.concat(all_data_frames, ignore_index=True)

    for col in ['C0', 'C1', 'C2', 'C3']:
        full_df[col] = pd.to_numeric(full_df[col], errors='coerce')

    results = []

    # 3 Group data
    grouped = full_df.groupby(['Movement', 'Finger'])

    print(f"Processing {len(grouped)} unique groups...")

    for (movement, finger), group in grouped:
        
        mvmt_check = str(movement).strip().lower()
        #Push pull
        if mvmt_check in ['push', 'pull']:
            vals = group['C3'].dropna()
            
            if not vals.empty:
                results.append({
                    'Movement': movement,
                    'Finger': finger,
                    'Phalange': "-",
                    'Avg': f"{vals.mean():.2f}",
                    'Min': f"{vals.min():.2f}",
                    'Max': f"{vals.max():.2f}"
                })

        # Lateral
        else:
            # We iterate 1, 2, 3 mapping them to C0, C1, C2
            sensor_map = {1: 'C0', 2: 'C1', 3: 'C2'}
            
            for p_num, col_name in sensor_map.items():
                vals = group[col_name].dropna()
                
                if not vals.empty:
                    results.append({
                        'Movement': movement,
                        'Finger': finger,
                        'Phalange': p_num,
                        'Avg': f"{vals.mean():.2f}",
                        'Min': f"{vals.min():.2f}",
                        'Max': f"{vals.max():.2f}"
                    })

    # 4. Write data
    if results:
        result_df = pd.DataFrame(results)
        
        cols = ["Movement", "Finger", "Phalange", "Avg", "Min", "Max"]
        result_df = result_df[cols]
        
        result_df.to_csv(output_filename, sep=';', index=False)
        print(f"\nSuccess! Stats merged into '{output_filename}'")
    else:
        print("\nProcessed files but found no valid data rows.")

else:
    print("No valid Excel files found to process.")

input("\nPress Enter to exit...")