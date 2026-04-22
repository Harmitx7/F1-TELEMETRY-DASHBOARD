from dash import html


def get_icon(name, size=24, color="currentColor", className="", aria_label=None):
    """
    Returns a Dash component that renders an SVG icon using CSS masks.
    This allows coloring the icon via 'backgroundColor' without inline SVG parsing issues.

    Args:
        name: Icon name (maps to /assets/icons/{name}.svg)
        size: Icon size in pixels (int) or CSS string
        color: CSS color value
        className: Additional CSS classes
        aria_label: Accessible label for the icon. If None, the icon is treated
                    as decorative (aria-hidden="true").
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

    # Accessibility: if no label, mark as decorative; otherwise add role="img"
    aria_props = {}
    if aria_label:
        aria_props['role'] = 'img'
        aria_props['aria-label'] = aria_label
    else:
        aria_props['aria-hidden'] = 'true'

    return html.Div(
        style=style,
        className=f"icon-mask {className}",
        **aria_props,
    )
