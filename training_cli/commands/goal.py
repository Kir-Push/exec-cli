"""
Goal command for the Training CLI application.
Allows setting goals for different exercise types.
"""
import click
from tabulate import tabulate
from training_cli.utils.data import load_data, save_data
from training_cli.utils.helpers import get_today_date

@click.command()
@click.argument("exercise_type", required=False)
@click.option("--daily", type=int, help="Set a daily goal for the exercise type.")
@click.option("--weekly", type=int, help="Set a weekly goal for the exercise type.")
@click.option("--sets", type=int, help="Set the number of sets for the exercise.")
@click.option("--weight", type=float, help="Set the weight in kg for the exercise.")
@click.option("--list", "list_goals", is_flag=True, help="List all current goals.")
@click.option("--delete", is_flag=True, help="Delete the goal for the exercise type.")
def goal(exercise_type, daily, weekly, sets, weight, list_goals, delete):
    """Set, view, or delete goals for your exercises."""
    data = load_data()

    # List all goals if requested
    if list_goals or (exercise_type is None and daily is None and weekly is None and sets is None and weight is None and not delete):
        goals = data.get("goals", {})
        if not goals:
            click.echo("No goals set yet.")
            return

        # Prepare table data
        table_data = []
        for ex_type, goal_data in goals.items():
            # Get the unit for this exercise type
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")

            daily_goal = goal_data.get("daily", "-")
            weekly_goal = goal_data.get("weekly", "-")
            sets_count = goal_data.get("sets", "-")
            weight_amount = goal_data.get("weight", "-")
            effective_date = goal_data.get("effective_date", "-")

            # Format goals with units
            if daily_goal != "-":
                daily_goal = f"{daily_goal} {unit}"
            if weekly_goal != "-":
                weekly_goal = f"{weekly_goal} {unit}"
            if weight_amount != "-":
                weight_amount = f"{weight_amount} kg"

            table_data.append([ex_type, daily_goal, weekly_goal, sets_count, weight_amount, effective_date])

        # Display table
        headers = ["Exercise Type", "Daily Goal", "Weekly Goal", "Sets", "Weight", "Effective Date"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
        return

    # Ensure exercise_type is provided if setting goals
    if exercise_type is None:
        click.echo("Error: Exercise type is required when setting goals.")
        return

    # Check if exercise type exists
    if exercise_type not in data["exercise_types"]:
        click.echo(f"Exercise type '{exercise_type}' not found.")
        click.echo("Available exercise types:")
        for ex_type in data["exercise_types"]:
            click.echo(f"- {ex_type}")
        return

    # Handle delete flag
    if delete:
        if exercise_type in data["goals"]:
            # Store the goal in history before deleting
            if exercise_type not in data["goal_history"]:
                data["goal_history"][exercise_type] = []
            data["goal_history"][exercise_type].append(data["goals"][exercise_type].copy())

            # Delete the goal
            del data["goals"][exercise_type]
            click.echo(f"Deleted goal for {exercise_type}.")
            save_data(data)
            return
        else:
            click.echo(f"No goal found for {exercise_type}.")
            return

    # Initialize goals for this exercise type if not present
    if exercise_type not in data["goals"]:
        data["goals"][exercise_type] = {
            "sets": 3,
            "weight": 0,
            "effective_date": get_today_date()
        }

    # Check if we need to store goal history
    goal_changed = False
    current_goal = data["goals"].get(exercise_type, {}).copy()

    # Set daily goal if provided
    if daily is not None:
        goal_changed = True
        data["goals"][exercise_type]["daily"] = daily
        unit = data["exercise_types"][exercise_type]["unit"]
        click.echo(f"Set daily goal for {exercise_type}: {daily} {unit}")

    # Set weekly goal if provided
    if weekly is not None:
        goal_changed = True
        data["goals"][exercise_type]["weekly"] = weekly
        unit = data["exercise_types"][exercise_type]["unit"]
        click.echo(f"Set weekly goal for {exercise_type}: {weekly} {unit}")

    # Set sets if provided
    if sets is not None:
        goal_changed = True
        data["goals"][exercise_type]["sets"] = sets
        click.echo(f"Set sets for {exercise_type}: {sets}")

    # Set weight if provided
    if weight is not None:
        goal_changed = True
        data["goals"][exercise_type]["weight"] = weight
        click.echo(f"Set weight for {exercise_type}: {weight} kg")

    # Update effective date and store goal history if any goal was changed
    if goal_changed:
        today = get_today_date()
        data["goals"][exercise_type]["effective_date"] = today

        # Initialize goal history for this exercise type if not present
        if exercise_type not in data["goal_history"]:
            data["goal_history"][exercise_type] = []

        # Store the previous goal in history
        if current_goal:
            data["goal_history"][exercise_type].append(current_goal)

    # If no goals were provided, show current goals for this exercise type
    if daily is None and weekly is None and sets is None and weight is None and not delete:
        if exercise_type not in data["goals"]:
            click.echo(f"No goals set for {exercise_type}.")
            return

        goal_data = data["goals"][exercise_type]
        unit = data["exercise_types"][exercise_type]["unit"]

        if "daily" in goal_data:
            click.echo(f"Daily goal for {exercise_type}: {goal_data['daily']} {unit}")
        else:
            click.echo(f"No daily goal set for {exercise_type}.")

        if "weekly" in goal_data:
            click.echo(f"Weekly goal for {exercise_type}: {goal_data['weekly']} {unit}")
        else:
            click.echo(f"No weekly goal set for {exercise_type}.")

        if "sets" in goal_data:
            click.echo(f"Sets for {exercise_type}: {goal_data['sets']}")
        else:
            click.echo(f"No sets set for {exercise_type}.")

        if "weight" in goal_data:
            click.echo(f"Weight for {exercise_type}: {goal_data['weight']} kg")
        else:
            click.echo(f"No weight set for {exercise_type}.")

        if "effective_date" in goal_data:
            click.echo(f"Effective date: {goal_data['effective_date']}")

    # Save changes
    save_data(data)
