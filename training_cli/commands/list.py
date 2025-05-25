"""
List command for the Training CLI application.
Allows listing exercise entries and viewing progress.
"""
import click
import datetime
from tabulate import tabulate
from training_cli.utils.data import load_data
from training_cli.utils.helpers import get_today_date, validate_date, calculate_total_by_exercise, calculate_progress, format_exercise_amount, create_progress_bar

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
        # If we're looking at today's data and there are no entries, we'll show exercises with goals
        if start_date == end_date and end_date == today and not exercise:
            # We'll continue and show exercises with goals that haven't been logged
            pass
        else:
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
        date_totals = calculate_total_by_exercise({entry_date: entries}, entry_date)
        for ex_type, total in date_totals.items():
            if ex_type in all_totals:
                all_totals[ex_type]["amount"] += total["amount"]
                all_totals[ex_type]["weight_total"] += total["weight_total"]
                all_totals[ex_type]["sets_total"] += total["sets_total"]
            else:
                all_totals[ex_type] = total

    # If we're looking at today's data, add exercises with goals that haven't been logged
    if start_date == end_date and end_date == today and not exercise:
        # Check if today is the last day of the week (Sunday)
        today_date = datetime.datetime.strptime(today, "%Y-%m-%d")
        is_last_day_of_week = today_date.weekday() == 6  # 6 is Sunday

        for ex_type, goal_data in data["goals"].items():
            # Check if this exercise has a weekly goal but no daily goal
            has_weekly_goal_only = "weekly" in goal_data and ("daily" not in goal_data or goal_data["daily"] == 0)

            # If it has a weekly goal only, we need to check if the weekly goal has been met
            if has_weekly_goal_only:
                # Calculate the start of the week (Monday)
                start_of_week = today_date - datetime.timedelta(days=today_date.weekday())
                start_date_str = start_of_week.strftime("%Y-%m-%d")

                # Calculate total for the week
                weekly_total = 0
                weekly_weight_total = 0
                weekly_sets_total = 0

                for date_str in data["entries"]:
                    if start_date_str <= date_str <= today:
                        for entry in data["entries"][date_str]:
                            if entry["exercise_type"] == ex_type:
                                amount = entry["amount"]
                                weight = entry.get("weight", 0)
                                sets = entry.get("sets", 1)
                                weekly_total += amount * sets
                                weekly_weight_total += amount * weight * sets
                                weekly_sets_total += sets

                # Check if weekly goal has been met
                weekly_goal = goal_data["weekly"]
                goal_sets = goal_data.get("sets", 1)
                weekly_goal_met = weekly_total >= weekly_goal * goal_sets

                # If weekly goal has not been met, add it to all_totals
                if not weekly_goal_met:
                    # Initialize with weekly values
                    all_totals[ex_type] = {
                        "amount": weekly_total,
                        "weight_total": weekly_weight_total,
                        "sets_total": weekly_sets_total,
                        "weekly_goal_only": True,  # Flag to indicate this exercise has only a weekly goal
                        "weekly_goal_met": False,  # Flag to indicate the weekly goal has not been met
                        "is_last_day_of_week": is_last_day_of_week  # Flag to indicate if today is the last day of the week
                    }
            elif ex_type not in all_totals:
                # Initialize with zero values for exercises with daily goals
                all_totals[ex_type] = {
                    "amount": 0,
                    "weight_total": 0,
                    "sets_total": 0,
                    "not_logged": True  # Flag to indicate this exercise hasn't been logged
                }

    # Calculate progress towards goals
    progress = calculate_progress(all_totals, data["goals"])

    # If summary mode, just show the totals and progress
    if summary:
        # Prepare summary table
        summary_data = []
        for ex_type, total in all_totals.items():
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")
            # Check if this exercise hasn't been logged or has a weekly goal only
            not_logged = total.get("not_logged", False)
            weekly_goal_only = total.get("weekly_goal_only", False)
            is_last_day_of_week = total.get("is_last_day_of_week", False)

            if not_logged:
                formatted_total = "Not logged"
            elif weekly_goal_only:
                formatted_total = format_exercise_amount(total["amount"], unit)
                if is_last_day_of_week:
                    formatted_total += " (WEEKLY GOAL NOT MET - LAST DAY!)"
                else:
                    formatted_total += " (Weekly goal not met)"
            else:
                formatted_total = format_exercise_amount(total["amount"], unit)

            # Get goal information
            goal_str = "-"
            progress_str = "-"
            progress_bar = ""
            if ex_type in data["goals"]:
                if week and "weekly" in data["goals"][ex_type]:
                    goal = data["goals"][ex_type]["weekly"]
                    sets = data["goals"][ex_type].get("sets", 1)
                    weight = data["goals"][ex_type].get("weight", 0)
                    goal_str = f"{goal} {unit}"
                    if sets > 1:
                        goal_str += f" x{sets}"
                    if weight > 0:
                        goal_str += f" ({weight}kg)"

                    if ex_type in progress:
                        progress_pct = progress[ex_type]["reps"]
                        progress_str = f"{progress_pct}%"
                        progress_bar = create_progress_bar(progress_pct)

                        # Add weight progress if applicable
                        if weight > 0 and progress[ex_type]["weight"] > 0:
                            weight_pct = progress[ex_type]["weight"]
                            progress_str += f" (Weight: {weight_pct}%)"

                elif not week and "daily" in data["goals"][ex_type]:
                    goal = data["goals"][ex_type]["daily"]
                    sets = data["goals"][ex_type].get("sets", 1)
                    weight = data["goals"][ex_type].get("weight", 0)
                    goal_str = f"{goal} {unit}"
                    if sets > 1:
                        goal_str += f" x{sets}"
                    if weight > 0:
                        goal_str += f" ({weight}kg)"

                    if ex_type in progress:
                        progress_pct = progress[ex_type]["reps"]
                        progress_str = f"{progress_pct}%"
                        progress_bar = create_progress_bar(progress_pct)

                        # Add weight progress if applicable
                        if weight > 0 and progress[ex_type]["weight"] > 0:
                            weight_pct = progress[ex_type]["weight"]
                            progress_str += f" (Weight: {weight_pct}%)"

            summary_data.append([ex_type, formatted_total, goal_str, progress_str, progress_bar])

        # Display summary table
        headers = ["Exercise Type", "Total", "Goal", "Progress", "Graph"]
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
            sets = entry.get("sets", 1)
            weight = entry.get("weight", 0)

            formatted_amount = format_exercise_amount(amount, unit)
            if sets > 1:
                formatted_amount += f" x{sets}"
            if weight > 0:
                formatted_amount += f" ({weight}kg)"
            table_data.append([timestamp, ex_type, formatted_amount])

        # Display table for this date
        headers = ["Time", "Exercise", "Amount"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

        # Show totals for this date
        date_totals = calculate_total_by_exercise({entry_date: filtered_entries[entry_date]}, entry_date)

        # If we're looking at today's data, add exercises with goals that haven't been logged
        if entry_date == today:
            # Check if today is the last day of the week (Sunday)
            today_date = datetime.datetime.strptime(today, "%Y-%m-%d")
            is_last_day_of_week = today_date.weekday() == 6  # 6 is Sunday

            for ex_type, goal_data in data["goals"].items():
                # Check if this exercise has a weekly goal but no daily goal
                has_weekly_goal_only = "weekly" in goal_data and ("daily" not in goal_data or goal_data["daily"] == 0)

                # If it has a weekly goal only, we need to check if the weekly goal has been met
                if has_weekly_goal_only:
                    # Calculate the start of the week (Monday)
                    start_of_week = today_date - datetime.timedelta(days=today_date.weekday())
                    start_date_str = start_of_week.strftime("%Y-%m-%d")

                    # Calculate total for the week
                    weekly_total = 0
                    weekly_weight_total = 0
                    weekly_sets_total = 0

                    for date_str in data["entries"]:
                        if start_date_str <= date_str <= today:
                            for entry in data["entries"][date_str]:
                                if entry["exercise_type"] == ex_type:
                                    amount = entry["amount"]
                                    weight = entry.get("weight", 0)
                                    sets = entry.get("sets", 1)
                                    weekly_total += amount * sets
                                    weekly_weight_total += amount * weight * sets
                                    weekly_sets_total += sets

                    # Check if weekly goal has been met
                    weekly_goal = goal_data["weekly"]
                    goal_sets = goal_data.get("sets", 1)
                    weekly_goal_met = weekly_total >= weekly_goal * goal_sets

                    # If weekly goal has not been met, add it to date_totals
                    if not weekly_goal_met:
                        # Initialize with weekly values
                        date_totals[ex_type] = {
                            "amount": weekly_total,
                            "weight_total": weekly_weight_total,
                            "sets_total": weekly_sets_total,
                            "weekly_goal_only": True,  # Flag to indicate this exercise has only a weekly goal
                            "weekly_goal_met": False,  # Flag to indicate the weekly goal has not been met
                            "is_last_day_of_week": is_last_day_of_week  # Flag to indicate if today is the last day of the week
                        }
                elif ex_type not in date_totals:
                    # Initialize with zero values for exercises with daily goals
                    date_totals[ex_type] = {
                        "amount": 0,
                        "weight_total": 0,
                        "sets_total": 0,
                        "not_logged": True  # Flag to indicate this exercise hasn't been logged
                    }

        date_progress = calculate_progress(date_totals, data["goals"])
        click.echo("\nTotals:")
        for ex_type, total_data in date_totals.items():
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")

            # Check if this exercise hasn't been logged or has a weekly goal only
            not_logged = total_data.get("not_logged", False)
            weekly_goal_only = total_data.get("weekly_goal_only", False)
            is_last_day_of_week = total_data.get("is_last_day_of_week", False)

            if not_logged:
                formatted_total = "Not logged"
            elif weekly_goal_only:
                formatted_total = format_exercise_amount(total_data["amount"], unit)

                # Add sets information if more than 1
                if total_data["sets_total"] > 1:
                    formatted_total += f" (in {total_data['sets_total']} sets)"

                # Add weight information if applicable
                if total_data["weight_total"] > 0:
                    formatted_total += f" - Total weight: {total_data['weight_total']}kg"

                # Add weekly goal notification
                if is_last_day_of_week:
                    formatted_total += " (WEEKLY GOAL NOT MET - LAST DAY!)"
                else:
                    formatted_total += " (Weekly goal not met)"
            else:
                formatted_total = format_exercise_amount(total_data["amount"], unit)

                # Add sets information if more than 1
                if total_data["sets_total"] > 1:
                    formatted_total += f" (in {total_data['sets_total']} sets)"

                # Add weight information if applicable
                if total_data["weight_total"] > 0:
                    formatted_total += f" - Total weight: {total_data['weight_total']}kg"

            # Show progress if applicable
            progress_str = ""
            progress_bar = ""
            if ex_type in date_progress:
                progress_data = date_progress[ex_type]
                progress_pct = progress_data["reps"]
                progress_str = f" ({progress_pct}% of goal)"
                progress_bar = create_progress_bar(progress_pct)

                # Add weight progress if applicable
                if progress_data["weight"] > 0:
                    progress_str += f" (Weight: {progress_data['weight']}% of goal)"

            click.echo(f"- {ex_type}: {formatted_total}{progress_str}")
            if progress_bar:
                click.echo(f"  {progress_bar}")

    # Show overall totals if multiple dates
    if len(filtered_entries) > 1:
        click.echo("\nOverall Totals:")
        for ex_type, total_data in all_totals.items():
            unit = data["exercise_types"].get(ex_type, {}).get("unit", "reps")

            # Check if this exercise hasn't been logged or has a weekly goal only
            not_logged = total_data.get("not_logged", False)
            weekly_goal_only = total_data.get("weekly_goal_only", False)
            is_last_day_of_week = total_data.get("is_last_day_of_week", False)

            if not_logged:
                formatted_total = "Not logged"
            elif weekly_goal_only:
                formatted_total = format_exercise_amount(total_data["amount"], unit)

                # Add sets information if more than 1
                if total_data["sets_total"] > 1:
                    formatted_total += f" (in {total_data['sets_total']} sets)"

                # Add weight information if applicable
                if total_data["weight_total"] > 0:
                    formatted_total += f" - Total weight: {total_data['weight_total']}kg"

                # Add weekly goal notification
                if is_last_day_of_week:
                    formatted_total += " (WEEKLY GOAL NOT MET - LAST DAY!)"
                else:
                    formatted_total += " (Weekly goal not met)"
            else:
                formatted_total = format_exercise_amount(total_data["amount"], unit)

                # Add sets information if more than 1
                if total_data["sets_total"] > 1:
                    formatted_total += f" (in {total_data['sets_total']} sets)"

                # Add weight information if applicable
                if total_data["weight_total"] > 0:
                    formatted_total += f" - Total weight: {total_data['weight_total']}kg"

            # Show progress if applicable
            progress_str = ""
            progress_bar = ""
            if ex_type in progress:
                progress_data = progress[ex_type]
                progress_pct = progress_data["reps"]
                progress_str = f" ({progress_pct}% of goal)"
                progress_bar = create_progress_bar(progress_pct)

                # Add weight progress if applicable
                if progress_data["weight"] > 0:
                    progress_str += f" (Weight: {progress_data['weight']}% of goal)"

            click.echo(f"- {ex_type}: {formatted_total}{progress_str}")
            if progress_bar:
                click.echo(f"  {progress_bar}")
