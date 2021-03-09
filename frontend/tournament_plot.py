import pandas as pd
import plotly.express as px
from plotly import io

def get_tournament_fig(data_dict):

    df = pd.DataFrame.from_dict(data_dict)


    fig = px.bar(
        df,
        x="score",
        y="agent_type",
        color="agent_type",
        facet_col="panther",
        facet_row="pelican",
        orientation="h"
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[-1]))
    fig.for_each_annotation(lambda a: a.update(textangle=0) \
                            if "pelican" in a.text else a)
    fig.for_each_annotation(lambda a: a.update(textangle=-15) \
                            if "panther" in a.text else a)

    # modify the layout, labels etc.
    fig.update_yaxes(visible=False)
    fig.update_xaxes(visible=False)
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.04,
            xanchor="auto",
            x=0.5
        ),
        margin=dict(l=20, r=240, t=90, b=20)
    )
    div = io.to_html(fig, full_html=False, include_plotlyjs=False)
    return div
