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

def create_progress_bar(percentage, width=20, fill_char='█', empty_char='░'):
    """
    Create an ASCII progress bar.

    Args:
        percentage (int): The percentage of completion (0-100)
        width (int): The width of the progress bar in characters
        fill_char (str): The character to use for filled portion
        empty_char (str): The character to use for empty portion

    Returns:
        str: A string representing the progress bar
    """
    filled_width = int(width * percentage / 100)
    empty_width = width - filled_width
    return fill_char * filled_width + empty_char * empty_width

def calculate_total_by_exercise(entries, date=None):
    """
    Calculate the total reps/duration for each exercise type on a given date.

    Args:
        entries (dict): The entries dictionary from the data file
        date (str, optional): The date to calculate totals for. If None, uses today's date.

    Returns:
        dict: A dictionary with exercise types as keys and dictionaries containing:
            - amount: total reps/duration
            - weight_total: total weight lifted (amount * weight * sets)
            - sets_total: total sets
    """
    if date is None:
        date = get_today_date()

    totals = {}
    if date in entries:
        for entry in entries[date]:
            exercise_type = entry["exercise_type"]
            amount = entry["amount"]
            weight = entry.get("weight", 0)
            sets = entry.get("sets", 1)

            # Calculate total weight
            weight_total = amount * weight * sets

            # Initialize if not present
            if exercise_type not in totals:
                totals[exercise_type] = {
                    "amount": 0,
                    "weight_total": 0,
                    "sets_total": 0
                }

            # Update totals
            totals[exercise_type]["amount"] += amount * sets
            totals[exercise_type]["weight_total"] += weight_total
            totals[exercise_type]["sets_total"] += sets

    return totals

def calculate_progress(totals, goals):
    """
    Calculate progress towards goals for each exercise type.

    Args:
        totals (dict): Dictionary with exercise types as keys and dictionaries containing amount, weight_total, and sets_total
        goals (dict): Dictionary with exercise types as keys and goal dictionaries as values

    Returns:
        dict: A dictionary with exercise types as keys and dictionaries containing:
            - reps: progress percentage for reps
            - weight: progress percentage for weight (if applicable)
            - weekly_goal_only: True if this exercise only has a weekly goal
            - weekly_goal_met: True if the weekly goal has been met
    """
    progress = {}

    for exercise_type, goal_data in goals.items():
        daily_goal = goal_data.get("daily", 0)
        weekly_goal = goal_data.get("weekly", 0)
        goal_sets = goal_data.get("sets", 1)
        goal_weight = goal_data.get("weight", 0)

        # Initialize progress for this exercise type
        progress[exercise_type] = {
            "reps": 0,
            "weight": 0,
            "weekly_goal_only": False,
            "weekly_goal_met": False
        }

        # Check if this exercise only has a weekly goal
        if daily_goal == 0 and weekly_goal > 0:
            progress[exercise_type]["weekly_goal_only"] = True

        # Calculate progress for reps
        if daily_goal > 0 and exercise_type in totals:
            total_amount = totals[exercise_type]["amount"]
            total_goal = daily_goal * goal_sets
            progress[exercise_type]["reps"] = min(100, int((total_amount / total_goal) * 100))
        elif weekly_goal > 0 and exercise_type in totals:
            # Use weekly goal for progress calculation
            total_amount = totals[exercise_type]["amount"]
            total_goal = weekly_goal * goal_sets
            progress[exercise_type]["reps"] = min(100, int((total_amount / total_goal) * 100))

            # Check if weekly goal has been met
            if total_amount >= total_goal:
                progress[exercise_type]["weekly_goal_met"] = True

        # Calculate progress for weight if applicable
        if goal_weight > 0 and exercise_type in totals:
            total_weight = totals[exercise_type]["weight_total"]
            if daily_goal > 0:
                total_weight_goal = daily_goal * goal_sets * goal_weight
            else:
                total_weight_goal = weekly_goal * goal_sets * goal_weight

            if total_weight_goal > 0:
                progress[exercise_type]["weight"] = min(100, int((total_weight / total_weight_goal) * 100))

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
