"""
Add command for the Training CLI application.
Allows adding an exercise to the tracker.
"""
import click
import datetime
from tabulate import tabulate
from training_cli.utils.data import load_data, save_data
from training_cli.utils.helpers import get_today_date, validate_date, format_exercise_amount

@click.command()
@click.argument("exercise_type")
@click.option("--date", "-d", default=None, help="Date for the entry (YYYY-MM-DD). Defaults to today.")
@click.option("--reps", type=int, default=None, help="Number of repetitions for the exercise.")
@click.option("--time", type=int, default=None, help="Duration in seconds for the exercise.")
@click.option("--distance", type=float, default=None, help="Distance in kilometers for the exercise.")
@click.option("--custom", "-c", is_flag=True, help="Add a custom exercise type.")
def add(exercise_type, date, reps, time, distance, custom):
    """Add an exercise to your tracker."""
    # Set the date (default to today if not provided)
    if date is None:
        date = get_today_date()
    else:
        # Validate date format
        if not validate_date(date):
            click.echo("Error: Date must be in YYYY-MM-DD format.")
            return

    # Load data
    data = load_data()
    
    # Handle custom exercise type
    if custom and exercise_type not in data["exercise_types"]:
        # Ask for unit type
        unit_options = ["reps", "seconds", "km"]
        click.echo("Select the unit type for this exercise:")
        for i, unit in enumerate(unit_options, 1):
            click.echo(f"{i}. {unit}")
        
        unit_choice = click.prompt("Enter the number of your choice", type=int, default=1)
        if unit_choice < 1 or unit_choice > len(unit_options):
            click.echo("Invalid choice. Using 'reps' as default.")
            unit = "reps"
        else:
            unit = unit_options[unit_choice - 1]
        
        # Ask for muscle groups
        muscle_groups = click.prompt("Enter muscle groups (comma-separated)", default="general")
        muscle_groups = [group.strip() for group in muscle_groups.split(",")]
        
        # Add to exercise types
        data["exercise_types"][exercise_type] = {
            "unit": unit,
            "muscle_groups": muscle_groups
        }
        
        click.echo(f"Added new exercise type: {exercise_type}")
    
    # Check if exercise type exists
    if exercise_type not in data["exercise_types"]:
        click.echo(f"Exercise type '{exercise_type}' not found.")
        click.echo("Available exercise types:")
        for ex_type in data["exercise_types"]:
            click.echo(f"- {ex_type}")
        click.echo("To add a custom exercise type, use the --custom flag.")
        return
    
    # Get the unit for this exercise type
    unit = data["exercise_types"][exercise_type]["unit"]
    
    # Determine the amount based on the unit
    amount = None
    if unit == "reps" and reps is not None:
        amount = reps
    elif unit == "seconds" and time is not None:
        amount = time
    elif unit == "km" and distance is not None:
        amount = distance
    
    # If amount is not provided, prompt the user
    if amount is None:
        if unit == "reps":
            amount = click.prompt(f"Enter number of {exercise_type} repetitions", type=int)
        elif unit == "seconds":
            amount = click.prompt(f"Enter duration of {exercise_type} in seconds", type=int)
        elif unit == "km":
            amount = click.prompt(f"Enter distance of {exercise_type} in kilometers", type=float)
    
    # Add to data file
    if date not in data["entries"]:
        data["entries"][date] = []
    
    entry = {
        "exercise_type": exercise_type,
        "amount": amount,
        "unit": unit,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    }
    data["entries"][date].append(entry)
    save_data(data)
    
    # Display confirmation
    formatted_amount = format_exercise_amount(amount, unit)
    click.echo(f"Added {exercise_type}: {formatted_amount} for {date}")
    
    # Check if there's a goal for this exercise type
    if exercise_type in data["goals"]:
        daily_goal = data["goals"][exercise_type].get("daily", 0)
        if daily_goal > 0:
            # Calculate total for today
            total = 0
            for entry in data["entries"].get(date, []):
                if entry["exercise_type"] == exercise_type:
                    total += entry["amount"]
            
            # Calculate progress
            progress = min(100, int((total / daily_goal) * 100))
            
            # Display progress
            click.echo(f"Progress towards daily goal: {progress}% ({total}/{daily_goal} {unit})")