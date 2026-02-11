from dash import html

def get_icon(name, size=24, color="currentColor", className=""):
    """
    Returns a Dash component that renders an SVG icon using CSS masks.
    This allows coloring the icon via 'backgroundColor' without inline SVG parsing issues.
    """
    
    # Ensure size has units
    if isinstance(size, int):
        size_str = f"{size}px"
    else:
        size_str = size
        
    style = {
        'display': 'inline-block',
        'width': size_str,
        'height': size_str,
        'backgroundColor': color,
        'maskImage': f'url("/assets/icons/{name}.svg")',
        'WebkitMaskImage': f'url("/assets/icons/{name}.svg")',
        'maskSize': 'contain',
        'WebkitMaskSize': 'contain',
        'maskRepeat': 'no-repeat',
        'WebkitMaskRepeat': 'no-repeat',
        'maskPosition': 'center',
        'WebkitMaskPosition': 'center',
        'verticalAlign': 'middle',
    }
    
    return html.Div(style=style, className=f"icon-mask {className}")
