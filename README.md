# Shooter do Mau

Space shooter written in Python and Pygame.

[![Shooter do Mau gameplay](http://i.ytimg.com/vi/GGLS71Fwk94/hqdefault.jpg)](https://www.youtube.com/watch?v=GGLS71Fwk94)

## Installing and running

> [!NOTE]
> This project requires the [UV](https://github.com/astral-sh/uv) Python tool.
>
> UV manages the dependencies. There is no need to use `pip` and `requirements.txt`.

Clone the repo.

```
git clone https://github.com/mhnagaoka/shooter-do-mau.git
cd shooter-do-mau
```

Run the code.

```
uv run main.py
```

## Developing

Create a virtual env and install its dependencies.

```sh
uv sync
```

Activate the virtual env.

```sh
source .venv/bin/activate
```

Run the code.

```sh
python main.py
```

You can also use the following environment variables:

- `SCALE_FACTOR` the factor to scale the game's native resolution to the screen
- `SPRITE_DEBUG` shows the sprite bounding boxes and hit boxes

### Sprite showcase

To see the rendered sprites and resulting animations, run the tool below.

```sh
python showcase.py
```

To check the program usage, pass the `--help` argument.

```sh
python showcase.py --help
```

### Spline tool

This tool is used to generate splines for the enemy trajectories.

To run it:

```sh
python spline_tool.py
```

How to use it:

- A: adds a spline control point
- D: when hovering a control point, deletes it
- mouse drag: drags a control point
- I: creates an aditional control point between the hovered one and the next
- H: show / hide spline drawing guides
- Enter: draws a ship following a trajectory and prints the control points on the console
