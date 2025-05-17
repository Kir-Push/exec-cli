"""
Helper utilities for the Training CLI application.
Contains utility functions for formatting and calculations.
"""
import datetime

def get_today_date():
    """Get today's date in YYYY-MM-DD format."""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def validate_date(date_str):
    """Validate that a string is in YYYY-MM-DD format."""
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def calculate_total_by_exercise(entries, date=None):
    """
    Calculate the total reps/duration for each exercise type on a given date.
    
    Args:
        entries (dict): The entries dictionary from the data file
        date (str, optional): The date to calculate totals for. If None, uses today's date.
    
    Returns:
        dict: A dictionary with exercise types as keys and total reps/duration as values
    """
    if date is None:
        date = get_today_date()
    
    totals = {}
    
    if date in entries:
        for entry in entries[date]:
            exercise_type = entry["exercise_type"]
            amount = entry["amount"]
            
            if exercise_type in totals:
                totals[exercise_type] += amount
            else:
                totals[exercise_type] = amount
    
    return totals

def calculate_progress(totals, goals):
    """
    Calculate progress towards goals for each exercise type.
    
    Args:
        totals (dict): Dictionary with exercise types as keys and total reps/duration as values
        goals (dict): Dictionary with exercise types as keys and goal dictionaries as values
    
    Returns:
        dict: A dictionary with exercise types as keys and progress percentages as values
    """
    progress = {}
    
    for exercise_type, goal_data in goals.items():
        daily_goal = goal_data.get("daily", 0)
        
        if daily_goal > 0:
            total = totals.get(exercise_type, 0)
            progress[exercise_type] = min(100, int((total / daily_goal) * 100))
        else:
            progress[exercise_type] = 0
    
    return progress

def format_exercise_amount(amount, unit):
    """Format an exercise amount with its unit."""
    if unit == "seconds":
        # Format seconds as minutes:seconds if >= 60 seconds
        if amount >= 60:
            minutes = amount // 60
            seconds = amount % 60
            return f"{minutes}m {seconds}s"
        else:
            return f"{amount}s"
    elif unit == "km":
        return f"{amount:.2f} km"
    else:
        return f"{amount} {unit}"