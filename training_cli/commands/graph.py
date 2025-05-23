"""
Graph command for the Training CLI application.
Allows visualizing exercise data.
"""
import click
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from training_cli.utils.data import load_data
from training_cli.utils.helpers import get_today_date, validate_date

@click.command()
@click.option("--exercise", "-e", help="Exercise type to graph.")
@click.option("--days", "-d", type=int, default=7, help="Number of days to include in the graph.")
@click.option("--month", "-m", is_flag=True, help="Show data for the current month.")
@click.option("--compare", "-c", is_flag=True, help="Compare multiple exercise types.")
@click.option("--output", "-o", help="Save the graph to a file instead of displaying it.")
@click.option("--metric", type=click.Choice(["reps", "weight", "weight_per_rep"]), default="reps",
              help="Metric to display (reps, total weight, or weight per rep).")
def graph(exercise, days, month, compare, output, metric):
    """Visualize your exercise data."""
    data = load_data()

    # Determine the date range
    end_date = datetime.datetime.strptime(get_today_date(), "%Y-%m-%d")

    if month:
        # Start from the beginning of the month
        start_date = end_date.replace(day=1)
    else:
        # Start from 'days' days ago
        start_date = end_date - datetime.timedelta(days=days-1)

    # Format dates as strings
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Get all dates in the range
    date_range = []
    date_objects = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        date_objects.append(current_date)
        current_date += datetime.timedelta(days=1)

    # If comparing multiple exercise types
    if compare:
        # Get all exercise types with data in the date range
        exercise_types = set()
        for date in date_range:
            if date in data["entries"]:
                for entry in data["entries"][date]:
                    exercise_types.add(entry["exercise_type"])

        if not exercise_types:
            click.echo("No exercise data found in the selected date range.")
            return

        # Ask user to select exercise types to compare
        if not exercise:
            click.echo("Select exercise types to compare:")
            for i, ex_type in enumerate(sorted(exercise_types), 1):
                click.echo(f"{i}. {ex_type}")

            selected = click.prompt("Enter numbers separated by commas (or 'all' for all types)", default="all")

            if selected.lower() == "all":
                selected_types = sorted(exercise_types)
            else:
                try:
                    indices = [int(idx.strip()) - 1 for idx in selected.split(",")]
                    selected_types = [sorted(exercise_types)[idx] for idx in indices if 0 <= idx < len(exercise_types)]
                except ValueError:
                    click.echo("Invalid input. Using all exercise types.")
                    selected_types = sorted(exercise_types)
        else:
            # Use the specified exercise type and find similar ones
            selected_types = [ex_type for ex_type in exercise_types if exercise.lower() in ex_type.lower()]
            if not selected_types:
                click.echo(f"No data found for exercise types containing '{exercise}'.")
                return

        # Collect data for each selected exercise type
        exercise_data = {}
        for ex_type in selected_types:
            daily_totals = []
            for date in date_range:
                total_reps = 0
                total_weight = 0
                total_sets = 0
                if date in data["entries"]:
                    for entry in data["entries"][date]:
                        if entry["exercise_type"] == ex_type:
                            amount = entry["amount"]
                            weight = entry.get("weight", 0)
                            sets = entry.get("sets", 1)
                            total_reps += amount * sets
                            total_weight += amount * weight * sets
                            total_sets += sets

                # Determine which metric to use
                if metric == "reps":
                    daily_totals.append(total_reps)
                elif metric == "weight":
                    daily_totals.append(total_weight)
                elif metric == "weight_per_rep":
                    # Avoid division by zero
                    if total_reps > 0:
                        daily_totals.append(total_weight / total_reps)
                    else:
                        daily_totals.append(0)

            exercise_data[ex_type] = daily_totals

        # Create the graph
        plt.figure(figsize=(12, 6))

        # Plot data for each exercise type
        for ex_type, totals in exercise_data.items():
            plt.plot(date_objects, totals, marker='o', label=ex_type)

        # Add labels and title
        plt.xlabel("Date")

        # Set y-label based on metric
        if metric == "reps":
            plt.ylabel("Repetitions")
            plt.title(f"Exercise Comparison - Repetitions ({start_date_str} to {end_date_str})")
        elif metric == "weight":
            plt.ylabel("Total Weight (kg)")
            plt.title(f"Exercise Comparison - Total Weight ({start_date_str} to {end_date_str})")
        elif metric == "weight_per_rep":
            plt.ylabel("Weight per Rep (kg)")
            plt.title(f"Exercise Comparison - Weight per Rep ({start_date_str} to {end_date_str})")
        plt.legend()

        # Format x-axis dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(date_range)//10)))
        plt.gcf().autofmt_xdate()

        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)

        # Save or show the graph
        if output:
            plt.savefig(output)
            click.echo(f"Graph saved to {output}")
        else:
            plt.tight_layout()
            plt.show()

        return

    # Single exercise type graph
    if not exercise:
        # Get all exercise types with data in the date range
        exercise_types = set()
        for date in date_range:
            if date in data["entries"]:
                for entry in data["entries"][date]:
                    exercise_types.add(entry["exercise_type"])

        if not exercise_types:
            click.echo("No exercise data found in the selected date range.")
            return

        # Ask user to select an exercise type
        click.echo("Select an exercise type to graph:")
        for i, ex_type in enumerate(sorted(exercise_types), 1):
            click.echo(f"{i}. {ex_type}")

        selection = click.prompt("Enter the number of your choice", type=int, default=1)
        if selection < 1 or selection > len(exercise_types):
            click.echo("Invalid selection. Using the first exercise type.")
            exercise = sorted(exercise_types)[0]
        else:
            exercise = sorted(exercise_types)[selection - 1]

    # Collect data for the selected exercise type
    daily_totals = []
    daily_weights = []
    daily_weight_per_rep = []

    for date in date_range:
        total_reps = 0
        total_weight = 0
        total_sets = 0
        if date in data["entries"]:
            for entry in data["entries"][date]:
                if entry["exercise_type"].lower() == exercise.lower():
                    amount = entry["amount"]
                    weight = entry.get("weight", 0)
                    sets = entry.get("sets", 1)
                    total_reps += amount * sets
                    total_weight += amount * weight * sets
                    total_sets += sets

        daily_totals.append(total_reps)
        daily_weights.append(total_weight)
        # Avoid division by zero
        if total_reps > 0:
            daily_weight_per_rep.append(total_weight / total_reps)
        else:
            daily_weight_per_rep.append(0)

    # Determine which data to use based on metric
    if metric == "reps":
        plot_data = daily_totals
        if sum(plot_data) == 0:
            click.echo(f"No repetition data found for '{exercise}' in the selected date range.")
            return
    elif metric == "weight":
        plot_data = daily_weights
        if sum(plot_data) == 0:
            click.echo(f"No weight data found for '{exercise}' in the selected date range.")
            return
    elif metric == "weight_per_rep":
        plot_data = daily_weight_per_rep
        if sum(plot_data) == 0:
            click.echo(f"No weight per rep data found for '{exercise}' in the selected date range.")
            return

    # Get the unit for this exercise type
    unit = data["exercise_types"].get(exercise, {}).get("unit", "reps")

    # Create the graph
    plt.figure(figsize=(12, 6))

    # Plot the data
    plt.bar(date_objects, plot_data, color='skyblue')

    # Add labels and title
    plt.xlabel("Date")

    # Set y-label and title based on metric
    if metric == "reps":
        plt.ylabel(f"Repetitions ({unit})")
        plt.title(f"{exercise.capitalize()} - Repetitions ({start_date_str} to {end_date_str})")
    elif metric == "weight":
        plt.ylabel("Total Weight (kg)")
        plt.title(f"{exercise.capitalize()} - Total Weight ({start_date_str} to {end_date_str})")
    elif metric == "weight_per_rep":
        plt.ylabel("Weight per Rep (kg)")
        plt.title(f"{exercise.capitalize()} - Weight per Rep ({start_date_str} to {end_date_str})")

    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(date_range)//10)))
    plt.gcf().autofmt_xdate()

    # Add goal line if applicable
    if exercise in data["goals"]:
        goal_data = data["goals"][exercise]

        # Get goal history for this exercise
        goal_history = data.get("goal_history", {}).get(exercise, [])

        # Add current goal to history for processing
        all_goals = goal_history + [goal_data]

        # Sort goals by effective date
        all_goals.sort(key=lambda g: g.get("effective_date", "2023-01-01"))

        # Find applicable goals for each date in the range
        for i, date_obj in enumerate(date_objects):
            date_str = date_obj.strftime("%Y-%m-%d")

            # Find the most recent goal that was effective before or on this date
            applicable_goal = None
            for goal in all_goals:
                effective_date = goal.get("effective_date", "2023-01-01")
                if effective_date <= date_str:
                    applicable_goal = goal

            if applicable_goal and i == 0:  # Only add the line once
                if metric == "reps" and "daily" in applicable_goal:
                    daily_goal = applicable_goal["daily"]
                    sets = applicable_goal.get("sets", 1)
                    total_goal = daily_goal * sets
                    plt.axhline(y=total_goal, color='r', linestyle='--', 
                                label=f"Daily Goal ({daily_goal} {unit} x{sets})")
                    plt.legend()
                elif metric == "weight" and "daily" in applicable_goal:
                    daily_goal = applicable_goal["daily"]
                    sets = applicable_goal.get("sets", 1)
                    weight = applicable_goal.get("weight", 0)
                    if weight > 0:
                        total_weight_goal = daily_goal * sets * weight
                        plt.axhline(y=total_weight_goal, color='r', linestyle='--', 
                                    label=f"Daily Weight Goal ({total_weight_goal}kg)")
                        plt.legend()
                elif metric == "weight_per_rep" and "daily" in applicable_goal:
                    weight = applicable_goal.get("weight", 0)
                    if weight > 0:
                        plt.axhline(y=weight, color='r', linestyle='--', 
                                    label=f"Weight per Rep Goal ({weight}kg)")
                        plt.legend()

    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)

    # Save or show the graph
    if output:
        plt.savefig(output)
        click.echo(f"Graph saved to {output}")
    else:
        plt.tight_layout()
        plt.show()
