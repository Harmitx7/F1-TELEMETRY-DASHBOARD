"""
Data Export Functionality
Export telemetry data in various formats (CSV, JSON).
"""
import pandas as pd
import json
from typing import Dict, Any, Optional
from datetime import datetime
import base64
import io


class DataExporter:
    """Handles exporting telemetry data to various formats"""
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame) -> str:
        """
        Convert DataFrame to CSV format for download
        
        Args:
            df: DataFrame to export
            
        Returns:
            Base64 encoded CSV string for Dash download
        """
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_bytes = csv_string.encode('utf-8')
        b64 = base64.b64encode(csv_bytes).decode()
        return f"data:text/csv;base64,{b64}"
    
    @staticmethod
    def export_to_json(df: pd.DataFrame,  pretty: bool = True) -> str:
        """
        Convert DataFrame to JSON format for download
        
        Args:
            df: DataFrame to export
            pretty: Whether to pretty-print JSON
            
        Returns:
            Base64 encoded JSON string for Dash download
        """
        json_string = df.to_json(orient='records', indent=2 if pretty else None)
        json_bytes = json_string.encode('utf-8')
        b64 = base64.b64encode(json_bytes).decode()
        return f"data:application/json;base64,{b64}"
    
    @staticmethod
    def create_filename(prefix: str, extension: str) -> str:
        """
        Generate timestamped filename
        
        Args:
            prefix: File prefix (e.g., "telemetry", "comparison")
            extension: File extension without dot
            
        Returns:
            Formatted filename with timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"
    
    @staticmethod
    def export_comparison_report(
        lap_a_data: pd.DataFrame,
        lap_b_data: pd.DataFrame,
        driver: str,
        lap_a: int,
        lap_b: int,
        delta_summary: Dict[str, Any]
    ) -> str:
        """
        Create a comprehensive comparison report in JSON format
        
        Args:
            lap_a_data: DataFrame for lap A
            lap_b_data: DataFrame for lap B
            driver: Driver code
            lap_a: Lap A number
            lap_b: Lap B number
            delta_summary: Dictionary containing delta analysis
            
        Returns:
            Base64 encoded JSON report
        """
        report = {
            "metadata": {
                "driver": driver,
                "lap_a": lap_a,
                "lap_b": lap_b,
                "generated_at": datetime.now().isoformat(),
            },
            "summary": delta_summary,
            "lap_a_telemetry": lap_a_data.to_dict('records'),
            "lap_b_telemetry": lap_b_data.to_dict('records'),
        }
        
        json_string = json.dumps(report, indent=2)
        json_bytes = json_string.encode('utf-8')
        b64 = base64.b64encode(json_bytes).decode()
        return f"data:application/json;base64,{b64}"
    
    @staticmethod
    def filter_dataframe(
        df: pd.DataFrame,
        driver: Optional[str] = None,
        laps: Optional[list[int]] = None,
        time_range: Optional[tuple[float, float]] = None
    ) -> pd.DataFrame:
        """
        Filter DataFrame by driver, laps, or time range
        
        Args:
            df: Input DataFrame
            driver: Driver code to filter by
            laps: List of lap numbers to include
            time_range: Tuple of (min_time, max_time) to filter by
            
        Returns:
            Filtered DataFrame
        """
        result = df.copy()
        
        if driver:
            result = result[result['driver'] == driver]
        
        if laps:
            result = result[result['lap'].isin(laps)]
        
        if time_range:
            min_time, max_time = time_range
            result = result[
                (result['time_stamp'] >= min_time) & 
                (result['time_stamp'] <= max_time)
            ]
        
        return result
