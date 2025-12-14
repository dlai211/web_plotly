# import modules
import os, yaml, re
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from typing import List
from datetime import timedelta
from datetime import datetime


# Trim and save the csv to itself with only the specified columns
def trim_csv(yml, site, instrument):
    datastream, filename = filename_from_yml(yml, site, instrument)
    data_info = yml['NSA'][site][instrument]
    vars = data_info['var_name']

    datastream, filename = filename_from_yml(yml, site, instrument)
    # Flatten the variables + datastream
    var_list = [item + "_" + datastream for group in vars for item in (group if isinstance(group, list) else [group])]

    try:
        # df = pd.read_csv(f"../../data/{filename}", usecols=var_list) # need to change the path to the data folder
        df = pd.read_csv(f"/Users/whbarndt/Documents/ARM-Data/NSA/{site}/{instrument.upper()}-Processed/{filename}", usecols=var_list) # need to change the path to the data folder
        df.to_csv(f"../data/{filename}", index=False) # save to ANOTHER data folder
        print(f"✅ Trimmed and saved: {filename}")

    except Exception as e:
        print(f"❌ Failed to process {filename}: {e}")

def filename_from_yml(yml: dict, site: str, instrument: str) -> str:
    """
    Extracts the filename from the YAML configuration for a given site and instrument.
    """
    data_level = "a1"
    location = "NSA"
    current_time = datetime.now()
    if current_time.month < 8:
        snow_year = current_time.year
    else:
        snow_year = current_time.year + 1
    
    datastream = f"{location.lower()}{instrument.lower()}{site}.{data_level}"
    filename = f"{datastream}_snowyear_{snow_year}.csv" # real data does not have "_trimmed" 
    datastream = datastream + f"_{snow_year}"

    return datastream, filename

def shorten_var_name(var: str) -> str:
    """
    Shortens the variable name by removing the '_nsa' suffix.
    """
    match = re.match(r"^(.*?)_nsa", var)
    prefix = match.group(1) # get rid of the _nsa part
    return prefix

def load_and_prepare_dataframe(yml: dict, site: str, instrument: str, data_folder: str = "../data") -> tuple[pd.DataFrame, list[str], str]:
    data_info = yml['NSA'][site][instrument]
    vars = data_info['var_name']
    title = data_info['title']

    datastream, filename = filename_from_yml(yml, site, instrument)
    # Flatten the variables + datastream
    vars = [item + "_" + datastream for group in vars for item in (group if isinstance(group, list) else [group])]

    # Load and resample
    df = pd.read_csv(os.path.join(data_folder, filename), usecols=vars)
    df[vars[0]] = pd.to_datetime(df[vars[0]])
    df = df.set_index(vars[0])
    df = df.resample("10min").mean() # 10-minute intervals
    df = df.dropna(how='all', subset=vars[1:])

    # Define last 4 weeks
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

def plot_datatime(df: pd.DataFrame, time_col: str, title: str, fontfamily="Open Sans") -> go.Figure:
    fig = go.Figure()

    for week in range(1, 5):
        df_w = df[(df['week'] == week)]
        if not df_w.empty:
            fig.add_trace(go.Scattergl(
                x=df_w[time_col],
                y=df_w['is_nan'] + df_w['week'],
                mode='markers',
                marker=dict(symbol='square', size=6, opacity=0.8),
                name=f"week {week}",
                showlegend=True
            ))

    fig.update_layout(
        paper_bgcolor='#B5828C',
        title=dict(
            text=f"{title} (weeks 1–4)",
            font=dict(color='#EBFDFB', size=26, family=fontfamily)
        ),
        xaxis=dict(
            title=dict(text="datetime", font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)
        ),
        yaxis=dict(
            title=dict(text="week", font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickmode='array',
            tickvals=[1, 2, 3, 4],
            ticktext=["week 1", "week 2", "week 3", "week 4"],
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
    weeks = sorted(df['week'].unique(), reverse=True)  # show Week 4 first in dropdown

    for var in vars:
        for week in weeks: # show Week 4 first in dropdown
            df_week = df[df['week'] == week]
            trace = go.Scattergl(
                x=df_week[time_col],
                y=df_week[var],
                mode='lines',
                name=f"{shorten_var_name(var)} (Week {week})",
                visible=(week == df['week'].max())
            )
            fig.add_trace(trace)
            trace_meta.append(week)

        buttons = []

    for i, week in enumerate(weeks):
        n_weeks = len(weeks)
        visibility = [j == i for j in range(n_weeks)] + [j == i for j in range(n_weeks)]
        buttons.append(dict(
            label=f"Week {week}",
            method="update",
            args=[
                {"visible": visibility},
                {"title": f"{title} - {group_name} (Week {week})"}
            ]
        ))

    fig.update_layout(
        paper_bgcolor='#B5828C',
        title=dict(text=f"{title} - {group_name} (Week {weeks[0]})",
                   font=dict(color='#EBFDFB', size=26, family=fontfamily)),
        xaxis=dict(title=dict(text="datetime", font=dict(color='#EBFDFB', size=20, family=fontfamily)),
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
            buttons=buttons
        )],
        height=800
    )
    return fig

def plot_single_variable(df: pd.DataFrame, var: str, time_col: str, title: str, fontfamily="Open Sans") -> go.Figure: 

    fig = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True, vertical_spacing=0.05)
    trace_meta, hist_meta = [], []
    weeks = sorted(df['week'].unique(), reverse=True)  # show Week 4 first in dropdown

    # Add one line plot per week
    for week in weeks:
        df_week = df[df['week'] == week]
        trace = go.Scattergl(
            x=df_week[time_col],
            y=df_week[var],
            mode='lines',
            name=f"{shorten_var_name(var)} (Week {week})",
            visible=(week == weeks[0]),
            showlegend=True,
            line=dict(color="#55AD9B")
        )
        fig.add_trace(trace, row=1, col=1)
        trace_meta.append(week)


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
                {"title": f"{title} - {shorten_var_name(var)} (Week {week})"}
            ]
        ))

    # Layout
    fig.update_layout(
        paper_bgcolor='#B5828C',
        title=dict(
            text=f"{title} - {shorten_var_name(var)} (Week {weeks[0]})",
            font=dict(color='#EBFDFB', size=26, family=fontfamily)
        ),
        xaxis=dict(  # x-axis of top plot
            title=dict(text="datetime", font=dict(color='#EBFDFB', size=20, family=fontfamily)),
            tickfont=dict(color='#EBFDFB', size=13.5, family=fontfamily)
        ),
        xaxis2=dict(
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
    fig.update_xaxes(showticklabels=True, row=1, col=1)

    return fig



def generate_html(site, instrument, title, figs, output_path):
    html_blocks, mode_blocks = [], []
    for i, (name, fig) in enumerate(figs.items()):

        mode_block = f"""
                <li data-target="{name}_container"><a href="#">{name}</a></li>
        """
        mode_blocks.append(mode_block)


        fig_html = pio.to_html(fig, include_plotlyjs="cdn", full_html=False)
        html_block = f"""
        <div class="plot-wrapper" data-container="{name}_container">
            <div id="{name}_container"  class="plot-container">
                {fig_html}
            </div>
        </div>
        """
        html_blocks.append(html_block)

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} Plotly Plots</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
        <link rel="stylesheet" href="../../style.css">
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
                {''.join(mode_blocks)}
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

        <script src="../../cut_link.js"></script>
        <script src="../../navigation.js"></script>

        <!-- Modal for Fullscreen Image -->
        <div id="image-modal" class="modal">
            <span class="close">&times;</span>
            <img class="modal-content" id="modal-img">
        </div>

        {''.join(html_blocks)}

        <script src="../../scroll.js"></script>
    </body>
    </html>
    """
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Saved: {output_path}")


def main():
    # loading the yaml file
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, 'metadata.key_variables.arm.yml')
    with open(file_path, 'r') as file:
        yml = yaml.safe_load(file)

    for site in yml['NSA'].keys():
        for instrument in yml['NSA'][site].keys():
            figs = {}

            all_vars = yml['NSA'][site][instrument]['var_name']
            df, vars, title = load_and_prepare_dataframe(yml, site, instrument, data_folder=os.path.join(base_dir, '..', 'data'))
            datastream, filename = filename_from_yml(yml, site, instrument)
            time_col = vars[0]

            fig_datetime = plot_datatime(df, time_col, title, fontfamily="Open Sans")
            figs['datetime'] = fig_datetime

            for i in range(1, len(all_vars)):
                if isinstance(all_vars[i], list): # list?
                    group = all_vars[i]
                    group_name = re.sub(r'_\d+$', '', group[0])
                    full_group = [item + "_" + datastream for item in group]
                    fig_group = plot_grouped_variables(df, full_group, time_col, title, group_name, fontfamily="Open Sans")
                    figs[group_name] = fig_group
                else:
                    single_name = all_vars[i]
                    full_single = single_name + "_" + datastream
                    fig_single = plot_single_variable(df, full_single, time_col, title, fontfamily="Open Sans")
                    figs[single_name] = fig_single

            # Generate HTML
            output_path = os.path.join(base_dir, '..', 'plots', site, f'{instrument}.html')
            generate_html(site, instrument, title, figs, output_path)

if __name__ == "__main__":
    main()