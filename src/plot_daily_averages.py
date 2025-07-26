import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
import yaml
import argparse
from utils.strava_db import DB_PATH
import numpy as np


CONFIG_PATH = Path("config/plot.yaml").resolve().parents[1] / "config" / "plot.yaml"
DB_PATH = Path("data/strava.db").resolve().parents[1] / "data" / "strava.db"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)
    
def select_x_values(x_values: str) -> str:
    if x_values == "day":
        return "day"
    elif x_values == "week":
        return "week"
    elif x_values == "distance":
        return "avg_distance"
    elif x_values == "speed":
        return "speed"
    elif x_values == "heart_rate":
        return "heart_rate"
    elif x_values == "elevation":
        return "elevation"
    else:
        raise ValueError(f"Invalid X value: {x_values}")
    
def select_y_values(y_values: str) -> str:
    if y_values == "day":
        return "day"
    elif y_values == "week":
        return "week"
    elif y_values == "distance":
        return "avg_distance"
    elif y_values == "speed":
        return "speed"
    elif y_values == "heart_rate":
        return "average_hr"
    elif y_values == "elevation":
        return "elevation"
    else:
        raise ValueError(f"Invalid Y value: {y_values}")
    
def map_field(key: str) -> str:
    mapping = {
        "day": "day",
        "week": "week",  # if you want to support future weekly grouping
        "distance": "avg_distance",
        "speed": "avg_speed",
        "heart_rate": "average_hr",
        "elevation": "avg_elevation",
    }
    if key not in mapping:
        raise ValueError(f"Invalid field: {key}")
    return mapping[key]

def load_daily_averages():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT 
            DATE(start_date) as day,
            AVG(distance) / 1000.0 as avg_distance,
            AVG(moving_time) / 60.0 as avg_moving_time,
            AVG(average_speed) * 3.6 as avg_speed,
            AVG(average_hr) as average_hr,
            AVG(max_hr) as max_hr,
            AVG(total_elevation_gain) / 1000.0 as avg_elevation
        FROM activities
        WHERE distance > 1000
        GROUP BY day
        ORDER BY day
    """
    df = pd.read_sql_query(query, conn, parse_dates=["day"])
    conn.close()
    return df

def style_plot(theme):
    plt.rcParams.update({
        "axes.facecolor": theme["background_color"],
        "figure.facecolor": theme["background_color"],
        "grid.color": theme["grid_color"],
        "grid.alpha": 0.3,
        "text.color": theme["text_color"],
        "axes.labelcolor": theme["text_color"],
        "xtick.color": theme["text_color"],
        "ytick.color": theme["text_color"],
        "font.family": theme["font"],
        "lines.linewidth": 2.0,
        "axes.edgecolor": theme["grid_color"],
    })

def distance_by_week(df, x_values, y_values):
    df = df.sort_values(by=x_values)
    df["week"] = df[x_values].dt.isocalendar().week
    df = df.groupby("week")[y_values].mean().reset_index()
    return df.sort_values(by="week")

def distance_by_day(df, x_values, y_values):
    df = df.sort_values(by=x_values)
    df = df.groupby("day")[y_values].mean().reset_index()
    return df.sort_values(by="day")


def plot_metric(df, x_values, y_values, theme):   
    # Plot the data
    plt.plot(
        df[x_values].values,
        df[y_values].values, 
        label="Data",
        linestyle=theme["line_style"],
        marker=theme["marker"],
        color=theme["accent_color"],
        markerfacecolor=theme["marker_color"],
        markeredgewidth=0,
        alpha=theme["alpha"]
    )
    
    # Create appropriate labels with units
    x_label = x_values
    y_label = y_values
    
    if x_values == "avg_distance":
        x_label = "Distance (km)"
    if y_values == "avg_distance":
        y_label = "Distance (km)"

    plt.title(f"{x_label} vs {y_label}", fontsize=16, color=theme["text_color"])
    plt.xlabel(x_label, fontsize=16, color=theme["text_color"])
    plt.ylabel(y_label, fontsize=16, color=theme["text_color"])
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tick_params(axis='x', colors=theme["text_color"])
    plt.tick_params(axis='y', colors=theme["text_color"])
    plt.gca().spines['bottom'].set_color(theme["grid_color"])
    plt.gca().spines['top'].set_color(theme["grid_color"])
    plt.gca().spines['left'].set_color(theme["grid_color"])
    plt.gca().spines['right'].set_color(theme["grid_color"])


def trend_line(df, x_values, y_values, theme, y_offset):
    df = df.sort_values(by=x_values)

    x = df[x_values].values
    y = df[y_values].values

    if np.issubdtype(x.dtype, np.datetime64):
        x_float = x.astype("datetime64[D]").astype(float)
    else:
        x_float = x

    # Fit trend
    x_float = np.asarray(x_float, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    z = np.polyfit(x_float, y, 1)
    p = np.poly1d(z)

    # Plot trend line
    plt.plot(
        df[x_values],
        p(x_float),
        label="Average Trend",
        color=theme["trend_line_color"],
        linestyle=theme["trend_line_style"],
        linewidth=theme["trend_line_width"],
        alpha=theme["trend_line_alpha"],
        marker=theme["trend_line_marker"],
        markerfacecolor=theme["trend_line_marker_color"],
        markeredgewidth=theme["trend_line_marker_edgewidth"],
    )

    # Annotate equation
    if np.issubdtype(df[x_values].dtype, np.datetime64):
        x_pos = df[x_values].iloc[-1] + pd.Timedelta(days=0.1)
        x_pos_float = x_pos.to_datetime64().astype("datetime64[D]").astype(float)
    else:
        x_pos = df[x_values].iloc[-1] + 0.1
        x_pos_float = x_pos

    y_pos = p(x_pos_float)

    plt.annotate(
        f"y = {p.coef[0]:.2f}x + {p.coef[1]:.2f}",
        xy=(0.01, y_offset),
        xycoords="axes fraction",
        fontsize=16,
        color=theme.get("trend_line_equation_color"),
        ha="left",
        va="top",
        bbox=dict(boxstyle="round", fc=theme["background_color"], ec="none", alpha=0.7)
    )

    print("Placing equation at:", y_offset)

    return y_offset - 0.03

def curve_fit_trend(df, x_values, y_values, degree, theme, y_offset):
    df = df.sort_values(by=x_values)

    x = df[x_values].values
    y = df[y_values].values

    if np.issubdtype(x.dtype, np.datetime64):
        x_plot = x  # preserve for plotting
        x = x.astype("datetime64[D]").astype(float)
    else:
        x_plot = x

    x_float = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # Fit a curve of the given degree
    coeffs = np.polyfit(x_float, y, degree)
    poly = np.poly1d(coeffs)

    # Plot the curve
    plt.plot(
        x_plot,
        poly(x),
        label="Data Curve",
        color=theme["curve_fit_color"],
        linestyle=theme["curve_fit_style"],
        linewidth=theme["curve_fit_width"],
        alpha=theme["curve_fit_alpha"],
        marker=theme["curve_fit_marker"],
        markerfacecolor=theme["curve_fit_marker_color"],
        markeredgewidth=theme["curve_fit_marker_edgewidth"],
    )

    # Optional: show equation
    if theme.get("show_equation", True):
        equation = " + ".join([f"{c:.2e}x^{i}" for i, c in enumerate(reversed(coeffs))])
        x_pos = x_plot[-1] + pd.Timedelta(days=0.1) if np.issubdtype(x_plot.dtype, np.datetime64) else x_plot[-1] + 0.1
        y_pos = poly(x[-1])

    plt.annotate(
        f"${equation}$",
        xy=(0.01, y_offset),
        xycoords="axes fraction",
        fontsize=16,
        color=theme.get("curve_fit_equation_color"),
        ha="left",
        va="top",
        bbox=dict(boxstyle="round", fc=theme["background_color"], ec="none", alpha=0.7)
    )

    print("Placing equation at:", y_offset)

    return y_offset - 0.03

def plot_all_segmented_trends(df, x_col, y_col, theme, y_offset, segment_size=4):
    df = df.sort_values(by=x_col)
    num_chunks = len(df) // segment_size

    pastel_palette = [
        "#a6daff", "#c6a0f6", "#f5bde6", "#f0c6c6", "#b5e8e0",
        "#f28fad", "#d2d2ff", "#e8d6ff", "#ffe5b4", "#ffd6e0"
    ]

    for i in range(num_chunks):
        chunk = df.iloc[i * segment_size:(i + 1) * segment_size]
        if len(chunk) < 2:
            continue

        x = chunk[x_col].values
        y = chunk[y_col].values

        if np.issubdtype(x.dtype, np.datetime64):
            x_float = x.astype("datetime64[D]").astype(float)
        else:
            x_float = x

        z = np.polyfit(x_float, y, 1)
        p = np.poly1d(z)

        color = pastel_palette[i % len(pastel_palette)]

        plt.plot(
            chunk[x_col],
            p(x_float),
            color=color,
            linestyle="--",
            linewidth=2,
            alpha=0.9,
            label=f"Segment Trend {i+1}"
        )

        # Staggered annotation
        plt.annotate(
            f"y = {p.coef[0]:.2f}x + {p.coef[1]:.2f}",
            xy=(0.01, y_offset),
            xycoords="axes fraction",
            fontsize=13,
            color=color,
            ha="left",
            va="top",
            bbox=dict(boxstyle="round", fc=theme["background_color"], ec="none", alpha=0.6)
        )

        y_offset -= 0.01  # Stack downward

    return y_offset

def main():
    plt.figure(figsize=(20, 10))

    # Parse the arguments
    parser = argparse.ArgumentParser("Select the X and Y values to plot")
    parser.add_argument("--x", type=str, help="X value(s) to plot", default="day", choices=["day", "week", "distance", "speed", "heart_rate", "elevation"])
    parser.add_argument("--y", type=str, help="Y value(s) to plot", default="day", choices=["day", "week", "distance", "speed", "heart_rate", "elevation"])
    parser.add_argument("--group_by", type=str, help="Group by day or week", default="day", choices=["day", "week"])
    parser.add_argument("--trend_line", action="store_true", help="Plot the trend line")
    parser.add_argument("--curve_fit", action="store_true", help="Plot the curve fit")
    parser.add_argument("--segmented_trends", type=int, help="Plot the segmented trends", default=4, choices=[4, 7, 14, 28])
    parser.add_argument("--save", action="store_true", help="Save the plot")
    args = parser.parse_args()

    # Map the fields
    x_values = map_field(args.x)
    y_values = map_field(args.y)

    if x_values == y_values:
        raise ValueError("X and Y values cannot be the same")

    config = load_config()
    theme = config["theme"] # type: ignore

    # Load the data
    df = load_daily_averages()
    style_plot(theme)

    if args.group_by == "week": # type: ignore
        df = df.sort_values("day")
        start_date = df["day"].min()
        df["week_bin"] = ((df["day"] - start_date).dt.days // 7)
        df = df.groupby("week_bin", as_index=False).mean()
        df["week_start"] = start_date + pd.to_timedelta(df["week_bin"] * 7, unit="D")
        x_values = "week_start"
    else:
        df = df.groupby("day", as_index=False).mean()
        x_values = "day"

    # Plot the data
    plot_metric(df, x_values, y_values, theme)
    equation_y = 0.95 # type: ignore
    
    if args.trend_line:
        equation_y = trend_line(df, x_values, y_values, theme, equation_y)

    if args.curve_fit:
        equation_y = curve_fit_trend(df, x_values, y_values, 2, theme, equation_y)

    if args.save:
        plt.savefig(f"plots/{x_values}_{y_values}_{args.group_by}.png")

    if args.segmented_trends:
        equation_y = plot_all_segmented_trends(df, x_values, y_values, theme, equation_y, int(args.segmented_trends))

    plt.legend(loc="upper right", frameon=True, facecolor=theme["background_color"], edgecolor=theme["grid_color"], fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

if __name__ == "__main__":
    main()
