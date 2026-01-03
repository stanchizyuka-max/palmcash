from datetime import datetime, date
from django.conf import settings
from django.db.models import Q

def get_system_launch_date():
    """Get the system launch date from settings"""
    launch_date_str = getattr(settings, 'SYSTEM_LAUNCH_DATE', '2025-09-30')
    return datetime.strptime(launch_date_str, '%Y-%m-%d').date()

def get_system_queryset_filter():
    """Get a Q filter for data from system launch date onwards"""
    launch_date = get_system_launch_date()
    return Q(created_at__date__gte=launch_date)

def get_system_date_filter(date_field='created_at'):
    """Get a date filter for a specific field from system launch date onwards"""
    launch_date = get_system_launch_date()
    return {f'{date_field}__date__gte': launch_date}

def get_monthly_periods_since_launch():
    """Get list of monthly periods since system launch"""
    launch_date = get_system_launch_date()
    current_date = date.today()
    
    periods = []
    year = launch_date.year
    month = launch_date.month
    
    while (year < current_date.year) or (year == current_date.year and month <= current_date.month):
        periods.append({
            'year': year,
            'month': month,
            'month_name': date(year, month, 1).strftime('%B'),
            'period_label': f"{date(year, month, 1).strftime('%B %Y')}"
        })
        
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    return periods

def format_system_period(start_date=None, end_date=None):
    """Format a period description relative to system launch"""
    launch_date = get_system_launch_date()
    
    if not start_date:
        start_date = launch_date
    if not end_date:
        end_date = date.today()
    
    # Ensure we don't go before launch date
    if start_date < launch_date:
        start_date = launch_date
    
    return f"From {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"

def get_system_age_in_days():
    """Get the number of days since system launch"""
    launch_date = get_system_launch_date()
    return (date.today() - launch_date).days

def get_system_age_description():
    """Get a human-readable description of system age"""
    days = get_system_age_in_days()
    
    if days < 30:
        return f"{days} days"
    elif days < 365:
        months = days // 30
        remaining_days = days % 30
        if remaining_days > 0:
            return f"{months} months, {remaining_days} days"
        else:
            return f"{months} months"
    else:
        years = days // 365
        remaining_days = days % 365
        months = remaining_days // 30
        if months > 0:
            return f"{years} year{'s' if years > 1 else ''}, {months} months"
        else:
            return f"{years} year{'s' if years > 1 else ''}"