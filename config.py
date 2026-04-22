"""
F1 Telemetry Dashboard Configuration
Centralized configuration management for all dashboard settings.
"""

class Config:
    """Main configuration class for the F1 Telemetry Dashboard"""
    
    # ============================================================================
    # UDP SETTINGS
    # ============================================================================
    UDP_IP = "0.0.0.0"
    UDP_PORT = 20777
    UDP_BUFFER_SIZE = 2048
    
    # ============================================================================
    # PERFORMANCE SETTINGS
    # ============================================================================
    # Maximum telemetry history length (points)
    # At 20Hz, 2400 points = 120 seconds of history
    MAX_HISTORY_LENGTH = 2400
    
    # Maximum points to render in charts before downsampling
    CHART_MAX_POINTS = 5000
    
    # Enable WebGL rendering for better performance
    ENABLE_WEBGL = True
    
    # Cache size for memoization (number of function calls)
    CACHE_SIZE = 128
    
    # ============================================================================
    # UI SETTINGS
    # ============================================================================
    DEFAULT_THEME = "dark"
    
    # Chart update rate for live mode (milliseconds)
    CHART_UPDATE_RATE = 500
    
    # Animation update rate (milliseconds)
    ANIMATION_UPDATE_RATE = 100
    
    # Default port for Dash server
    SERVER_PORT = 8050
    SERVER_DEBUG = True
    
    # ============================================================================
    # DATA SETTINGS
    # ============================================================================
    # Default data file path
    DEFAULT_DATA_PATH = "data/example_telemetry.csv"
    
    # Required CSV columns
    REQUIRED_COLUMNS = ['driver', 'lap', 'time_stamp']
    
    # Optional CSV columns
    OPTIONAL_COLUMNS = [
        'speed_kph', 'rpm', 'throttle_pct', 'brake_pct', 
        'gear', 'drs', 'sector', 'sector_time_ms', 'lat', 'long'
    ]
    
    # ============================================================================
    # F1 THEME COLORS
    # ============================================================================
    COLORS = {
        # Core backgrounds
        'card_bg': '#0b0f12',
        'background': '#050505',
        
        # F1 Signature colors
        'f1_red': '#d90429',
        'f1_cyan': '#00e5ff',
        'f1_gold': '#b7ff2a',
        
        # Text colors
        'text_primary': '#f4f7fa',
        'text_secondary': '#a2acb8',
        'text_accent': '#00e5ff',
        'text_muted': '#68727d',
        
        # Chart colors
        'grid_line': 'rgba(255, 255, 255, 0.07)',
        'border': 'rgba(255, 255, 255, 0.12)',
        
        # Data series colors - F1 team inspired
        'series': ['#00e5ff', '#b7ff2a', '#ff335f', '#f5f7ff', '#ff8f00'],
        
        # Data state colors
        'positive': '#b7ff2a',
        'negative': '#ff335f',
        'warning': '#ff8f00',
        
        # Table colors
        'table_header': '#0a0c10',
        'table_row_even': '#0f1318',
        'table_row_odd': '#11171d',
        'header_gradient_start': '#00e5ff',
    }
    
    # ============================================================================
    # STYLE PRESETS
    # ============================================================================
    CARD_STYLE = {
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '10px',
        'padding': '20px',
        'marginBottom': '20px',
        'border': f'1px solid {COLORS["border"]}',
        'boxShadow': 'none',
    }
    
    SECTION_TITLE_STYLE = {
        'fontSize': '14px',
        'fontWeight': '700',
        'color': COLORS['text_primary'],
        'letterSpacing': '0.13em',
        'marginBottom': '15px',
        'textTransform': 'uppercase',
        'borderBottom': f'1px solid {COLORS["header_gradient_start"]}',
        'paddingBottom': '8px',
        'fontFamily': 'Orbitron, sans-serif',
    }
    
    METRIC_VALUE_STYLE = {
        'fontSize': '32px',
        'fontWeight': '700',
        'color': COLORS['f1_cyan'],
        'fontFamily': 'Orbitron, sans-serif',
        'textShadow': '0 0 16px rgba(0, 229, 255, 0.25)',
        'transition': 'text-shadow 0.3s ease',
    }
    
    METRIC_LABEL_STYLE = {
        'fontSize': '12px',
        'color': COLORS['text_secondary'],
        'marginTop': '5px',
        'textTransform': 'uppercase',
        'letterSpacing': '0.05em',
    }
    
    DROPDOWN_STYLE = {
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '6px',
        'border': f'1px solid {COLORS["border"]}',
    }
    
    @classmethod
    def get_chart_config(cls):
        """Returns standard configuration for Plotly charts"""
        return {
            'displayModeBar': False,
            'scrollZoom': False,
        }
    
    @classmethod
    def get_chart_layout_base(cls):
        """Returns base layout configuration for Plotly charts"""
        return {
            'template': 'plotly_dark',
            'paper_bgcolor': cls.COLORS['card_bg'],
            'plot_bgcolor': cls.COLORS['card_bg'],
            'font': {'color': cls.COLORS['text_secondary'], 'size': 11},
            'margin': {'l': 50, 'r': 20, 't': 40, 'b': 50},
            'xaxis': {'gridcolor': cls.COLORS['grid_line']},
            'yaxis': {'gridcolor': cls.COLORS['grid_line']},
            'hovermode': 'closest',
        }
