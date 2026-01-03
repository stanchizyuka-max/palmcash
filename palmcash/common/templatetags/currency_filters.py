from django import template

register = template.Library()

@register.filter
def zmw_currency(value):
    """Format value as ZMW currency with K symbol"""
    if value is None:
        return "K0.00"
    
    try:
        # Convert to float and format with 2 decimal places
        amount = float(value)
        formatted = f"{amount:,.2f}"
        return f"K{formatted}"
    except (ValueError, TypeError):
        return "K0.00"

@register.filter
def zmw_currency_no_decimal(value):
    """Format value as ZMW currency with K symbol, no decimals for whole numbers"""
    if value is None:
        return "K0"
    
    try:
        amount = float(value)
        if amount == int(amount):
            # If it's a whole number, don't show decimals
            formatted = f"{int(amount):,}"
            return f"K{formatted}"
        else:
            # Show decimals for non-whole numbers
            formatted = f"{amount:,.2f}"
            return f"K{formatted}"
    except (ValueError, TypeError):
        return "K0"