
import pandas as pd
import numpy as np

# Create a simple dataset with minimal columns
data = {
    'driver': ['TEST'] * 100,
    'lap': [1] * 100,
    'time_stamp': np.linspace(0, 80, 100),
    # speed_kph is MISSING
    # rpm is MISSING
    # throttle_pct is MISSING
}

df = pd.DataFrame(data)
output_path = 'data/test_missing_speed.csv'
df.to_csv(output_path, index=False)
print(f"Created {output_path}")
