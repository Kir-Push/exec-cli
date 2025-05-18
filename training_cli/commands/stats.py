"""
Stats command for the Training CLI application.
Provides comprehensive statistics for exercises.
"""
import click
import datetime
from tabulate import tabulate
from collections import defaultdict
from training_cli.utils.data import load_data
from training_cli.utils.helpers import get_today_date, validate_date, calculate_total_by_exercise, format_exercise_amount

@click.command()
@click.option("--days", "-d", type=int, default=30, help="Number of days to include in the statistics.")
@click.option("--month", "-m", is_flag=True, help="Show statistics for the current month.")
@click.option("--exercise", "-e", help="Filter statistics by exercise type.")
@click.option("--muscle", "-g", help="Filter statistics by muscle group.")
@click.option("--output", "-o", help="Save the statistics to a file.")
def stats(days, month, exercise, muscle, output):
    """Show comprehensive statistics for your exercises."""
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
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += datetime.timedelta(days=1)
    
    # Filter entries by date range and exercise/muscle group if specified
    filtered_entries = {}
    for entry_date, entries in data["entries"].items():
        if start_date_str <= entry_date <= end_date_str:
            filtered_entries[entry_date] = []
            for entry in entries:
                # Filter by exercise type if specified
                if exercise and entry["exercise_type"].lower() != exercise.lower():
                    continue
                
                # Filter by muscle group if specified
                if muscle:
                    exercise_type = entry["exercise_type"]
                    muscle_groups = data["exercise_types"].get(exercise_type, {}).get("muscle_groups", [])
                    if muscle.lower() not in [m.lower() for m in muscle_groups]:
                        continue
                
                filtered_entries[entry_date].append(entry)
            
            # Remove dates with no entries after filtering
            if not filtered_entries[entry_date]:
                del filtered_entries[entry_date]
    
    # Check if there are any entries to analyze
    if not filtered_entries:
        if exercise and muscle:
            click.echo(f"No entries found for exercise '{exercise}' and muscle group '{muscle}' in the selected date range.")
        elif exercise:
            click.echo(f"No entries found for exercise '{exercise}' in the selected date range.")
        elif muscle:
            click.echo(f"No entries found for muscle group '{muscle}' in the selected date range.")
        else:
            click.echo("No entries found for the selected date range.")
        return
    
    # Display header
    if exercise and muscle:
        click.echo(f"Exercise Statistics for '{exercise}' (Muscle Group: {muscle}) - {start_date_str} to {end_date_str}:")
    elif exercise:
        click.echo(f"Exercise Statistics for '{exercise}' - {start_date_str} to {end_date_str}:")
    elif muscle:
        click.echo(f"Exercise Statistics for Muscle Group '{muscle}' - {start_date_str} to {end_date_str}:")
    else:
        click.echo(f"Exercise Statistics - {start_date_str} to {end_date_str}:")
    
    # Calculate exercise summary
    exercise_summary = defaultdict(lambda: {"total_reps": 0, "total_sets": 0, "total_weight": 0, "days": 0, "max_weight": 0})
    
    for entry_date, entries in filtered_entries.items():
        # Track unique exercises per day
        exercises_on_date = set()
        
        for entry in entries:
            exercise_type = entry["exercise_type"]
            amount = entry["amount"]
            weight = entry.get("weight", 0)
            sets = entry.get("sets", 1)
            
            # Update summary
            exercise_summary[exercise_type]["total_reps"] += amount * sets
            exercise_summary[exercise_type]["total_sets"] += sets
            exercise_summary[exercise_type]["total_weight"] += amount * weight * sets
            
            # Track max weight
            if weight > exercise_summary[exercise_type]["max_weight"]:
                exercise_summary[exercise_type]["max_weight"] = weight
            
            # Add to unique exercises for this day
            exercises_on_date.add(exercise_type)
        
        # Update days count for each exercise
        for ex in exercises_on_date:
            exercise_summary[ex]["days"] += 1
    
    # Calculate muscle group summary
    muscle_summary = defaultdict(lambda: {"total_reps": 0, "total_weight": 0, "exercises": set()})
    
    for exercise_type, summary in exercise_summary.items():
        muscle_groups = data["exercise_types"].get(exercise_type, {}).get("muscle_groups", [])
        for muscle_group in muscle_groups:
            muscle_summary[muscle_group]["total_reps"] += summary["total_reps"]
            muscle_summary[muscle_group]["total_weight"] += summary["total_weight"]
            muscle_summary[muscle_group]["exercises"].add(exercise_type)
    
    # Calculate weight progression
    weight_progression = {}
    
    for exercise_type in exercise_summary:
        weight_progression[exercise_type] = []
        
        for entry_date in sorted(filtered_entries.keys()):
            max_weight_for_day = 0
            for entry in filtered_entries[entry_date]:
                if entry["exercise_type"] == exercise_type:
                    weight = entry.get("weight", 0)
                    if weight > max_weight_for_day:
                        max_weight_for_day = weight
            
            if max_weight_for_day > 0:
                weight_progression[exercise_type].append((entry_date, max_weight_for_day))
    
    # Calculate goal achievement
    goal_achievement = {}
    
    for exercise_type, goal_data in data["goals"].items():
        if exercise and exercise.lower() != exercise_type.lower():
            continue
        
        if muscle:
            muscle_groups = data["exercise_types"].get(exercise_type, {}).get("muscle_groups", [])
            if muscle.lower() not in [m.lower() for m in muscle_groups]:
                continue
        
        daily_goal = goal_data.get("daily", 0)
        if daily_goal > 0:
            days_with_goal = 0
            days_achieved = 0
            
            for entry_date in date_range:
                days_with_goal += 1
                
                # Calculate total for this date
                if entry_date in filtered_entries:
                    total_reps = 0
                    for entry in filtered_entries[entry_date]:
                        if entry["exercise_type"] == exercise_type:
                            amount = entry["amount"]
                            sets = entry.get("sets", 1)
                            total_reps += amount * sets
                    
                    # Check if goal was achieved
                    goal_sets = goal_data.get("sets", 1)
                    if total_reps >= daily_goal * goal_sets:
                        days_achieved += 1
            
            if days_with_goal > 0:
                achievement_pct = int((days_achieved / days_with_goal) * 100)
                goal_achievement[exercise_type] = {
                    "days_with_goal": days_with_goal,
                    "days_achieved": days_achieved,
                    "achievement_pct": achievement_pct
                }
    
    # Calculate streak analysis
    streak_analysis = {}
    
    for exercise_type in exercise_summary:
        current_streak = 0
        longest_streak = 0
        last_date = None
        
        for entry_date in sorted(date_range):
            has_exercise = False
            
            if entry_date in filtered_entries:
                for entry in filtered_entries[entry_date]:
                    if entry["exercise_type"] == exercise_type:
                        has_exercise = True
                        break
            
            if has_exercise:
                if last_date is None or (datetime.datetime.strptime(entry_date, "%Y-%m-%d") - 
                                         datetime.datetime.strptime(last_date, "%Y-%m-%d")).days == 1:
                    current_streak += 1
                else:
                    current_streak = 1
                
                longest_streak = max(longest_streak, current_streak)
                last_date = entry_date
            else:
                current_streak = 0
                last_date = None
        
        streak_analysis[exercise_type] = {
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }
    
    # Display exercise summary
    click.echo("\nExercise Summary:")
    exercise_table = []
    
    for exercise_type, summary in sorted(exercise_summary.items()):
        unit = data["exercise_types"].get(exercise_type, {}).get("unit", "reps")
        total_reps = format_exercise_amount(summary["total_reps"], unit)
        avg_reps_per_day = format_exercise_amount(summary["total_reps"] / summary["days"] if summary["days"] > 0 else 0, unit)
        
        exercise_table.append([
            exercise_type,
            total_reps,
            summary["total_sets"],
            f"{summary['total_weight']:.1f} kg" if summary["total_weight"] > 0 else "-",
            summary["days"],
            avg_reps_per_day,
            f"{summary['max_weight']:.1f} kg" if summary["max_weight"] > 0 else "-"
        ])
    
    headers = ["Exercise", "Total", "Sets", "Weight", "Days", "Avg/Day", "Max Weight"]
    click.echo(tabulate(exercise_table, headers=headers, tablefmt="simple"))
    
    # Display muscle group summary
    if not exercise:  # Only show if not filtered by exercise
        click.echo("\nMuscle Group Summary:")
        muscle_table = []
        
        for muscle_group, summary in sorted(muscle_summary.items()):
            if muscle and muscle.lower() != muscle_group.lower():
                continue
                
            muscle_table.append([
                muscle_group,
                summary["total_reps"],
                f"{summary['total_weight']:.1f} kg" if summary["total_weight"] > 0 else "-",
                len(summary["exercises"]),
                ", ".join(sorted(summary["exercises"]))
            ])
        
        headers = ["Muscle Group", "Total Reps", "Total Weight", "Exercises", "Exercise Types"]
        click.echo(tabulate(muscle_table, headers=headers, tablefmt="simple"))
    
    # Display weight progression
    click.echo("\nWeight Progression:")
    for exercise_type, progression in sorted(weight_progression.items()):
        if progression:
            click.echo(f"\n{exercise_type}:")
            
            # Check if weight has increased
            if len(progression) >= 2:
                first_weight = progression[0][1]
                last_weight = progression[-1][1]
                
                if last_weight > first_weight:
                    increase = last_weight - first_weight
                    increase_pct = (increase / first_weight) * 100
                    click.echo(f"  Weight increased by {increase:.1f} kg ({increase_pct:.1f}%) from {first_weight:.1f} kg to {last_weight:.1f} kg")
                elif last_weight < first_weight:
                    decrease = first_weight - last_weight
                    decrease_pct = (decrease / first_weight) * 100
                    click.echo(f"  Weight decreased by {decrease:.1f} kg ({decrease_pct:.1f}%) from {first_weight:.1f} kg to {last_weight:.1f} kg")
                else:
                    click.echo(f"  Weight remained constant at {first_weight:.1f} kg")
            
            # Show progression table
            progression_table = []
            for date, weight in progression:
                progression_table.append([date, f"{weight:.1f} kg"])
            
            headers = ["Date", "Weight"]
            click.echo(tabulate(progression_table, headers=headers, tablefmt="simple"))
    
    # Display goal achievement
    if goal_achievement:
        click.echo("\nGoal Achievement:")
        goal_table = []
        
        for exercise_type, achievement in sorted(goal_achievement.items()):
            goal_table.append([
                exercise_type,
                achievement["days_achieved"],
                achievement["days_with_goal"],
                f"{achievement['achievement_pct']}%"
            ])
        
        headers = ["Exercise", "Days Achieved", "Days with Goal", "Achievement"]
        click.echo(tabulate(goal_table, headers=headers, tablefmt="simple"))
    
    # Display streak analysis
    click.echo("\nStreak Analysis:")
    streak_table = []
    
    for exercise_type, streaks in sorted(streak_analysis.items()):
        streak_table.append([
            exercise_type,
            streaks["current_streak"],
            streaks["longest_streak"]
        ])
    
    headers = ["Exercise", "Current Streak", "Longest Streak"]
    click.echo(tabulate(streak_table, headers=headers, tablefmt="simple"))
    
    # Save to file if requested
    if output:
        with open(output, "w") as f:
            f.write(f"Exercise Statistics - {start_date_str} to {end_date_str}\n\n")
            
            f.write("Exercise Summary:\n")
            f.write(tabulate(exercise_table, headers=headers, tablefmt="simple"))
            f.write("\n\n")
            
            if not exercise:
                f.write("Muscle Group Summary:\n")
                f.write(tabulate(muscle_table, headers=["Muscle Group", "Total Reps", "Total Weight", "Exercises", "Exercise Types"], tablefmt="simple"))
                f.write("\n\n")
            
            f.write("Weight Progression:\n")
            for exercise_type, progression in sorted(weight_progression.items()):
                if progression:
                    f.write(f"\n{exercise_type}:\n")
                    
                    if len(progression) >= 2:
                        first_weight = progression[0][1]
                        last_weight = progression[-1][1]
                        
                        if last_weight > first_weight:
                            increase = last_weight - first_weight
                            increase_pct = (increase / first_weight) * 100
                            f.write(f"  Weight increased by {increase:.1f} kg ({increase_pct:.1f}%) from {first_weight:.1f} kg to {last_weight:.1f} kg\n")
                        elif last_weight < first_weight:
                            decrease = first_weight - last_weight
                            decrease_pct = (decrease / first_weight) * 100
                            f.write(f"  Weight decreased by {decrease:.1f} kg ({decrease_pct:.1f}%) from {first_weight:.1f} kg to {last_weight:.1f} kg\n")
                        else:
                            f.write(f"  Weight remained constant at {first_weight:.1f} kg\n")
                    
                    progression_table = []
                    for date, weight in progression:
                        progression_table.append([date, f"{weight:.1f} kg"])
                    
                    f.write(tabulate(progression_table, headers=["Date", "Weight"], tablefmt="simple"))
                    f.write("\n")
            
            if goal_achievement:
                f.write("\nGoal Achievement:\n")
                f.write(tabulate(goal_table, headers=["Exercise", "Days Achieved", "Days with Goal", "Achievement"], tablefmt="simple"))
                f.write("\n\n")
            
            f.write("Streak Analysis:\n")
            f.write(tabulate(streak_table, headers=["Exercise", "Current Streak", "Longest Streak"], tablefmt="simple"))
            
            click.echo(f"Statistics saved to {output}")