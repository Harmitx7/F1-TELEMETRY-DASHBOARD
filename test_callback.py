import traceback
import pandas as pd, io
from app import update_correlation_heatmap

try:
    df = pd.read_csv('data/example_telemetry.csv')
    stored_data = df.to_json(orient='split', date_format='iso')
    update_correlation_heatmap(stored_data)
    print("Success")
except Exception as e:
    traceback.print_exc()
