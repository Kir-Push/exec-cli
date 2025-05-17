# Training CLI

A command-line tool for tracking exercise activities.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Add an exercise
training add pushup --reps 20

# Set a goal
training goal pushup --daily 50

# List exercises
training list

# View progress graph
training graph

# Clear all data
training clear
```

## Features

- Track different types of exercises (push-ups, squats, curls, etc.)
- Set daily goals for each exercise type
- View your exercise history
- Visualize your progress with graphs
- Simple and intuitive command-line interface