"""
Goal command for the Training CLI application.
Allows setting goals for different exercise types.
"""
import click
from tabulate import tabulate
from training_cli.utils.data import load_data, save_data

@click.command()
@click.argument("exercise_type", required=False)
@click.option("--daily", type=int, help="Set a daily goal for the exercise type.")
@click.option("--weekly", type=int, help="Set a weekly goal for the exercise type.")
@click.option("--list", "list_goals", is_flag=True, help="List all current goals.")
def goal(exercise_type, daily, weekly, list_goals):
    """Set or view goals for your exercises."""
    data = load_data()
    
    # List all goals if requested
    if list_goals or (exercise_type is None and daily is None and weekly is None):
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
            
            # Format goals with units
            if daily_goal != "-":
                daily_goal = f"{daily_goal} {unit}"
            if weekly_goal != "-":
                weekly_goal = f"{weekly_goal} {unit}"
            
            table_data.append([ex_type, daily_goal, weekly_goal])
        
        # Display table
        headers = ["Exercise Type", "Daily Goal", "Weekly Goal"]
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
    
    # Initialize goals for this exercise type if not present
    if exercise_type not in data["goals"]:
        data["goals"][exercise_type] = {}
    
    # Set daily goal if provided
    if daily is not None:
        data["goals"][exercise_type]["daily"] = daily
        unit = data["exercise_types"][exercise_type]["unit"]
        click.echo(f"Set daily goal for {exercise_type}: {daily} {unit}")
    
    # Set weekly goal if provided
    if weekly is not None:
        data["goals"][exercise_type]["weekly"] = weekly
        unit = data["exercise_types"][exercise_type]["unit"]
        click.echo(f"Set weekly goal for {exercise_type}: {weekly} {unit}")
    
    # If no goals were provided, show current goals for this exercise type
    if daily is None and weekly is None:
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
    
    # Save changes
    save_data(data)