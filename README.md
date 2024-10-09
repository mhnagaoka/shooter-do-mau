# Shooter do Mau

Space shooter written in Python and Pygame.

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

### Spline tool

There is a spline drawing tool that I (shamelessly) copied from
[sk-Prime/simple_pygames](https://github.com/sk-Prime/simple_pygames) and slightly modified to print the
BSpline's control points.

This tool is used to create splines for enemy trajectories.

Run it.

```sh
python bspline.py
```

Draw a spline (figure it out by yourself :wink:). The tool will print out the control points coordinates
as an array of tuples on the console. For example:

```sh
$ python bspline.py
pygame 2.6.1 (SDL 2.28.4, Python 3.12.5)
Hello from the pygame community. https://www.pygame.org/contribute.html
[(306, 51), (574, 357)]
[(306, 51), (574, 357), (584, 829)]
[(306, 51), (574, 357), (584, 829), (337, 1062)]
```
