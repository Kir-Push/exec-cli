"""
List command for the Training CLI application.
Allows listing exercise entries and viewing progress.
"""
import click
import datetime
from tabulate import tabulate
from training_cli.utils.data import load_data
from training_cli.utils.helpers import get_today_date, validate_date, calculate_total_by_exercise, calculate_progress, format_exercise_amount

@click.command(name="list")
@click.option("--date", "-d", default=None, help="Date to list entries for (YYYY-MM-DD). Defaults to today.")
@click.option("--week", "-w", is_flag=True, help="List entries for the current week.")
@click.option("--month", "-m", is_flag=True, help="List entries for the current month.")
@click.option("--exercise", "-e", default=None, help="Filter entries by exercise type.")
@click.option("--summary", "-s", is_flag=True, help="Show only summary information.")
def list_exercises(date, week, month, exercise, summary):
    """List your exercise entries and view progress."""
    data = load_data()
    
    # Determine the date range to display
    today = get_today_date()
    
    if week:
        # Calculate the start of the week (Monday)
        today_date = datetime.datetime.strptime(today, "%Y-%m-%d")
        start_of_week = today_date - datetime.timedelta(days=today_date.weekday())
        start_date = start_of_week.strftime("%Y-%m-%d")
        end_date = today
        date_range_str = f"Week of {start_date} to {end_date}"
    elif month:
        # Calculate the start of the month
        today_date = datetime.datetime.strptime(today, "%Y-%m-%d")
        start_of_month = today_date.replace(day=1)
        start_date = start_of_month.strftime("%Y-%m-%d")
        end_date = today
        date_range_str = f"Month of {start_date} to {end_date}"
    elif date:
        # Validate date format
        if not validate_date(date):
            click.echo("Error: Date must be in YYYY-MM-DD format.")
            return
        start_date = date
        end_date = date
        date_range_str = date
    else:
        # Default to today
        start_date = today
        end_date = today
        date_range_str = "Today"
    
    # Filter entries by date range
    filtered_entries = {}
    for entry_date, entries in data["entries"].items():
        if start_date <= entry_date <= end_date:
            if exercise:
                # Filter by exercise type if specified
                filtered_entries[entry_date] = [
                    entry for entry in entries
                    if entry["exercise_type"].lower() == exercise.lower()
                ]
                # Skip dates with no matching entries
                if not filtered_entries[entry_date]:
                    del filtered_entries[entry_date]
            else:
                filtered_entries[entry_date] = entries
    
    # Check if there are any entries to display
    if not filtered_entries:
        if exercise:
            click.echo(f"No entries found for exercise '{exercise}' in the selected date range.")
        else:
            click.echo("No entries found for the selected date range.")
        return
    
    # Display header
    if exercise:
        click.echo(f"Exercise entries for '{exercise}' - {date_range_str}:")
    else:
        click.echo(f"Exercise entries - {date_range_str}:")
    
    # Calculate totals by exercise type
    all_totals = {}
    for entry_date, entries in filtered_entries.items():
        date_totals = calculate_total_by_exercise({"entries": {entry_date: entries}}, entry_date)
        for ex_type, total in date_totals.items():
            if ex_type in all_totals:
                all_totals[ex_type] += total
            else:
                all_totals[ex_type] = total
    
    # Calculate progress towards goals
    progress = calculate_progress(all_totals, data["goals"])
    
    # If summary mode, just show the totals and progress
    if summary:
        # Prepare summary table
        summary_data = []
        for ex_type, total in all_totals.items():
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")
            formatted_total = format_exercise_amount(total, unit)
            
            # Get goal information
            goal_str = "-"
            progress_str = "-"
            if ex_type in data["goals"]:
                if week and "weekly" in data["goals"][ex_type]:
                    goal = data["goals"][ex_type]["weekly"]
                    goal_str = f"{goal} {unit}"
                    progress_pct = progress.get(ex_type, 0)
                    progress_str = f"{progress_pct}%"
                elif not week and "daily" in data["goals"][ex_type]:
                    goal = data["goals"][ex_type]["daily"]
                    goal_str = f"{goal} {unit}"
                    progress_pct = progress.get(ex_type, 0)
                    progress_str = f"{progress_pct}%"
            
            summary_data.append([ex_type, formatted_total, goal_str, progress_str])
        
        # Display summary table
        headers = ["Exercise Type", "Total", "Goal", "Progress"]
        click.echo(tabulate(summary_data, headers=headers, tablefmt="simple"))
        return
    
    # Display detailed entries
    for entry_date in sorted(filtered_entries.keys()):
        click.echo(f"\nDate: {entry_date}")
        
        # Prepare table data for this date
        table_data = []
        for entry in filtered_entries[entry_date]:
            ex_type = entry["exercise_type"]
            amount = entry["amount"]
            unit = entry["unit"]
            timestamp = entry.get("timestamp", "")
            
            formatted_amount = format_exercise_amount(amount, unit)
            table_data.append([timestamp, ex_type, formatted_amount])
        
        # Display table for this date
        headers = ["Time", "Exercise", "Amount"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
        
        # Show totals for this date
        date_totals = calculate_total_by_exercise({"entries": {entry_date: filtered_entries[entry_date]}}, entry_date)
        click.echo("\nTotals:")
        for ex_type, total in date_totals.items():
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")
            formatted_total = format_exercise_amount(total, unit)
            click.echo(f"- {ex_type}: {formatted_total}")
    
    # Show overall totals if multiple dates
    if len(filtered_entries) > 1:
        click.echo("\nOverall Totals:")
        for ex_type, total in all_totals.items():
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")
            formatted_total = format_exercise_amount(total, unit)
            
            # Show progress if applicable
            progress_str = ""
            if ex_type in progress:
                progress_pct = progress[ex_type]
                if progress_pct > 0:
                    progress_str = f" ({progress_pct}% of goal)"
            
            click.echo(f"- {ex_type}: {formatted_total}{progress_str}")