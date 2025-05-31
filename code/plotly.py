# import modules
import os, sys, time, random, yaml
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tqdm.rich import tqdm
import seaborn as sns
from matplotlib.ticker import FormatStrFormatter
import matplotlib.ticker as ticker
from collections import Counter
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from typing import List, Dict
from datetime import timedelta

# loading the yaml file
with open('metadata.key_variables.arm.yml', 'r') as file:
    yml = yaml.safe_load(file)


# Trim and save the csv to itself with only the specified columns
def trim_csv(yml):
    for site in yml['NSA'].keys():
        for instrument in yml['NSA'][site].keys():
            filename = yml['NSA'][site][instrument]['filename']
            var_list = yml['NSA'][site][instrument]['var_name']

            try:
                df = pd.read_csv(f"../../data/{filename}", usecols=var_list)
                df.to_csv(f"../data/{filename}", index=False)
                print(f"✅ Trimmed and saved: {filename}")

            except Exception as e:
                print(f"❌ Failed to process {filename}: {e}")

def load_and_prepare_dataframe(site: str, instrument: str, yml: dict, data_folder: str = "../../data") -> tuple[pd.DataFrame, list[str], str]:
    data_info = yml['NSA'][site][instrument]
    vars = data_info['var_name']
    title = data_info['title']
    filename = data_info['filename']

    # Load and resample
    df = pd.read_csv(os.path.join(data_folder, filename), usecols=vars)
    df[vars[0]] = pd.to_datetime(df[vars[0]])
    df = df.set_index(vars[0])
    df = df.resample("10T").mean()
    df = df.dropna(how='all', subset=vars[1:])

    # Define valid time window (last 4 full weeks)
    last_valid_time = df[vars[1:]].dropna(how='all').index.max()
    if last_valid_time is None:
        raise ValueError(f"No valid data found for {site}-{instrument}")
    
    end_of_week_4 = last_valid_time.floor("D") + pd.Timedelta(hours=23, minutes=50)
    start_of_week_1 = end_of_week_4 - timedelta(days=28)
    seconds_in_week = 7 * 24 * 60 * 60

    df = df.loc[start_of_week_1:end_of_week_4 - pd.Timedelta(minutes=9)].reset_index()
    df['week'] = (((df[vars[0]] - start_of_week_1).dt.total_seconds()) // seconds_in_week + 1).astype(int)
    df['is_nan'] = df[vars[1]].isna().astype(int)

    return df, vars, title

def plot_datatime(df: pd.DataFrame, vars: List[str], time_col: str, title: str, group_name: str, fontfamily="Open Sans") -> go.Figure:
    fig = go.Figure()

    for week in range(1, 5):
        df_w = df[(df['week'] == week)]
        if not df_w.empty:
            fig.add_trace(go.Scattergl(
                x=df_w[vars[0]],
                y=df_w['is_nan'] + df_w['week'],
                mode='markers',
                marker=dict(symbol='square', size=6, opacity=0.8),
                name=f"Week {week}",
                showlegend=True
            ))

    fig.update_layout(
        paper_bgcolor='#B5828C',
        plot_bgcolor='#B5828C',
        title=dict(
            text=f"{title} - Missing Data (Weeks 1–4)",
            font=dict(color='#EBFDFB', size=26, family=fontfamily)
        ),
        xaxis=dict(
            title=dict(text=vars[0], font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)
        ),
        yaxis=dict(
            title=dict(text="Week", font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickmode='array',
            tickvals=[1, 2, 3, 4],
            ticktext=["Week 1", "Week 2", "Week 3", "Week 4"],
            tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily),
            range=[0.5, 4.5]
        ),
        legend=dict(
            x=1.02, y=1, yanchor='top',
            font=dict(color='#EBFDFB', size=15, family=fontfamily)
        ),
        margin=dict(r=100),
        height=500
    )

    return fig

def plot_grouped_variables(df: pd.DataFrame, vars: List[str], time_col: str, title: str, group_name: str, fontfamily="Open Sans") -> go.Figure:
    fig = go.Figure()
    trace_meta = []

    for var in vars:
        for week in sorted(df['week'].unique()):
            df_week = df[df['week'] == week]
            trace = go.Scattergl(
                x=df_week[time_col],
                y=df_week[var],
                mode='lines',
                name=f"{var} (Week {week})",
                visible=(week == df['week'].max())
            )
            fig.add_trace(trace)
            trace_meta.append(week)

    fig.update_layout(
        paper_bgcolor='#B5828C',
        title=dict(text=f"{title} - {group_name} (Week {df['week'].max()})",
                   font=dict(color='#EBFDFB', size=26, family=fontfamily)),
        xaxis=dict(title=dict(text=time_col, font=dict(color='#EBFDFB', size=20, family=fontfamily)),
                   tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)),
        yaxis=dict(title=dict(text=group_name, font=dict(color='#EBFDFB', size=20, family=fontfamily)),
                   tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)),
        legend=dict(x=1.02, y=1, yanchor='top',
                    font=dict(color='#EBFDFB', size=15, family=fontfamily)),
        updatemenus=[dict(
            type="dropdown",
            direction="down",
            showactive=True,
            x=1.02,
            y=1.1,
            xanchor="left",
            yanchor="top",
            font=dict(color="lightgrey", size=15, family=fontfamily),
            buttons=[
                dict(
                    label=f"Week {w}",
                    method="update",
                    args=[
                        {"visible": [t == w for t in trace_meta]},
                        {"title": f"{title} - {group_name} (Week {w})"}
                    ],
                )
                for w in sorted(df['week'].unique())
            ]
        )],
        height=800
    )
    return fig

def plot_single_variable(df: pd.DataFrame, var: str, time_col: str, title: str, fontfamily="Open Sans") -> go.Figure:
    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.05)
    trace_meta, hist_meta = [], []

    var = vars[1]
    time_col = vars[0]
    weeks = sorted(df['week'].unique(), reverse=True)  # show Week 4 first in dropdown

    # Add one line plot per week
    for week in weeks:
        df_week = df[df['week'] == week]
        trace = go.Scattergl(
            x=df_week[time_col],
            y=df_week[var],
            mode='lines',
            name=f"{var} (Week {week})",
            visible=(week == weeks[0]),  # only show last week by default
            showlegend=True,
            line=dict(color="#55AD9B")
        )
        fig.add_trace(trace, row=1, col=1)
        trace_meta.append(week)  # <-- fix: track visibility index


    for week in weeks:
        df_week = df[df['week'] == week]
        hist = go.Histogram(
            x=df_week[var],
            nbinsx=100,
            marker=dict(color="#55AD9B"),
            opacity=0.75,
            name=f"{var} Histogram (Week {week})",
            visible=(week == weeks[0]),
            showlegend=False
        )
        fig.add_trace(hist, row=2, col=1)
        hist_meta.append(week)
        
    # Create dropdown menu buttons
    buttons = []
    for i, week in enumerate(weeks):
        n_weeks = len(weeks)
        visibility = [j == i for j in range(n_weeks)] + [j == i for j in range(n_weeks)]
        buttons.append(dict(
            label=f"Week {week}",
            method="update",
            args=[
                {"visible": visibility},
                {"title": f"{title} - {var} (Week {week})"}
            ]
        ))

    # Layout
    fig.update_layout(
        paper_bgcolor='#B5828C',
        title=dict(
            text=f"{title} - {var} (Week {weeks[0]})",
            font=dict(color='#EBFDFB', size=26, family=fontfamily)
        ),
        xaxis2=dict(  # x-axis of histogram (bottom plot)
            title=dict(text=time_col, font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)
        ),
        yaxis=dict(
            title=dict(text=var, font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)
        ),
        legend=dict(
            x=1.02, y=1, yanchor='top',
            font=dict(color='#EBFDFB', size=15, family=fontfamily)
        ),
        updatemenus=[dict(
            type="dropdown",
            direction="down",
            showactive=True,
            x=1.02,
            y=1.1,
            xanchor="left",
            yanchor="top",
            font=dict(color="lightgrey", size=15, family=fontfamily),
            buttons=buttons
        )],
        height=800
    )
    return fig



def generate_html(site: str, instrument: str, yml: dict, output_path: str = "output.html"):
    
    df, vars, title = load_and_prepare_dataframe(site, instrument, yml)
    time_col = vars[0]
    group_vars = [v for v in vars if v != time_col]

    groups: Dict[str, List[str]] = {
        "Air Temperature": [v for v in group_vars if "air_temperature" in v],
        "Distance": [v for v in group_vars if "distance_" in v],
        "Data Quality": [v for v in group_vars if "data_quality_" in v],
        "Other": [v for v in group_vars if all(kw not in v for kw in ["air_temperature", "distance_", "data_quality_"])]
    }

    figs = {gname: plot_grouped_variables(df, gvars, time_col, title, gname) for gname, gvars in groups.items() if gvars}

    html_blocks = []
    for i, (name, fig) in enumerate(figs.items()):
        fig_html = pio.to_html(fig, include_plotlyjs=('cdn' if i == 0 else False), full_html=False)
        block = f"""
        <div class="plot-wrapper" data-container="u_wind_container">
            <div id=\"{name.replace(' ', '_').lower()}_container\"  class="plot-container">
                {fig_html}
            </div>
        </div>
        """
        html_blocks.append(block)

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} Plotly Plots</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        <link rel="stylesheet" href="../../style.css">
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>{title} ({instrument}, {site}) Plotly Plots</h1>

        <nav id="cut-nav"> 
            <ul id="cut-links"></ul>
        </nav>

        <!-- performance or selection plots -->
        <nav id="mode-nav">
            <ul>
                <li>Plot: </li>
                <li data-target="u_wind_container"><a href="#">u wind</a></li>
                <li data-target="v_wind_container"><a href="#">v wind</a></li>
                <li data-target="w_wind_container"><a href="#">w wind</a></li>
            </ul>
        </nav>

        <!-- Section to display images -->
        <section>
            <h2 id="cut-title">{title} ({instrument}, {site}) Description<br>
                Can drag to zoom in & double click to reset below images
            </h2>
            <div class="wrapper" id="image-container">
                <!-- Images will be dynamically added here -->
            </div>
        </section>

        <!-- Modal for Fullscreen Image -->
        <div id="image-modal" class="modal">
            <span class="close">&times;</span>
            <img class="modal-content" id="modal-img">
        </div>

        {''.join(html_blocks)}

        <script src="../../cut_link.js"></script>
        <script src="../../scroll.js"></script>
        <script src="../../navigation.js"></script>
    </body>
    </html>
    """

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Saved: {output_path}")
