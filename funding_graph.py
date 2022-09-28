"""

Makes a pretty polar graph of a Gitcoin user's
funding preferences for a given round.

"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys

from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from textwrap import wrap


# Global plot styling updates
plt.rcParams.update({"font.family": "Tahoma"})
plt.rcParams["text.color"] = "#1f1f1f"
plt.rc("axes", unicode_minus=False)


# Pathnames
CONTRIBS_PATH = 'data/contributions.csv'
TAGS_PATH = 'data/tags.csv'
GRANTS_PATH = 'data/grants.json'

# Gitcoin colors
COLORS = [
    "#6F3FF5",  # violet
    "#F3587D", # pink
    "#FFCC00", # yellow          
    "#02E2AC", # green
] 
CMAP = LinearSegmentedColormap.from_list("", COLORS, N=256)


# Max number of tags to display
NUM_TAGS = 10 # can't be more than 12


# Filter on the MECE-est tags
FILTER_TAGS = [
    '*Climate Solutions', 'DAOs', 'Education', '*DeSci', 
    'Infrastructure', '*Crypto Advocacy', '*ETH Infra',
    '*Diversity (DEI)', '*Web3 Social', 'DeFi', 'dGov', 
    '*a16z', '*zkTech', 'Radicle', '*Greater China', 'ETH2.0'
]


# Special cases
GRANTS_TO_IGNORE = [
    12  # Gitcoin grants matching fund
] 


def make_plot(
    handle,                  # a string representing the user's gitcoin username
    max_tags=NUM_TAGS,       # an int representing the max tags to display
    filter_tags=FILTER_TAGS, # a list of grant tags to filter for
    outdir='img/',           # a directory for exporting images to
    var='count'              # a column in the data set to use for valuing preferences
    ):

    """
    Function to render a preference plot. 
    This version only uses contribution counts (not total contribution values or 
    another metric) to determine the order and magnitude of the user's preferences.
    
    """

    handle = handle.lower()

    # load data about the user's donations
    df = (pd
          .read_csv(CONTRIBS_PATH, index_col=0)
          .query("grant_id not in @GRANTS_TO_IGNORE")
          .query("handle == @handle"))
    
    if not len(df):
        print("Unable to locate user:", handle)
        return
                 
    # load grant tags data
    tags_data = pd.read_csv(TAGS_PATH, index_col=0)
    tags_dict = dict(zip(tags_data['tag_id'], tags_data['tag_name']))

    # load the grants data
    grant_mapper = json.load(open(GRANTS_PATH))

    # determine the number of contributions to each grant
    donations = df['grant_id'].value_counts()
    num_grants = len(donations)

    # iterate through each donation to assign grant tags
    data = []
    for grant_id, count in donations.items():
        grant_tags = grant_mapper.get(str(grant_id), [-1])
        for tag in grant_tags:
            data.append({
                'handle': handle,
                'grant_id': grant_id,
                'grant_tag_id': tag,
                'grant_tag': tags_dict[tag],
                var: count
            })
    tidy_data = pd.DataFrame(data)    
    
    # group the data by tags
    df_grouped = (tidy_data    
                  .groupby("grant_tag")
                  [var].sum()
                  .reset_index())

    # sort and filter the tags
    df_sorted = (df_grouped
                 .query("grant_tag in @filter_tags")
                 .sort_values(var, ascending=False)
                 .head(max_tags))
    
    
    # math to determine the positions and spacing of our bars
    angles = np.linspace(0.05, 2 * np.pi - 0.05, len(df_sorted), endpoint=False)
    lengths = df_sorted[var].values
    max_len = df_sorted[var].max() * 1.1

    # make the tag labels
    tags = df_sorted["grant_tag"].values
    tags = ["\n".join(wrap(t.replace("*",""), 5, break_long_words=False)) for t in tags]

    # assign colors based on our distribution
    norm = Normalize(vmin=lengths.min(), vmax=max_len)
    colors = CMAP(norm(lengths))

    # make the plot itself
    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw={"projection": "polar"}, dpi=144)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.bar(angles, lengths, color=colors, alpha=0.9, width=0.52, zorder=10)
    ax.set_xticklabels(tags, size=12);
    ax.set_theta_offset(1.2 * np.pi / 2)
    ax.set_yticks([])
    ax.set_ylim(0, max_len)
    ax.set_xticks(angles)
    plt.box(False)
    
    # title text
    ax.set_title(
        f"{handle} contributed to {num_grants} public goods in GR15\n\n", 
        fontweight='bold'
    )

    outpath = f"{outdir}{handle}_gr15.png"
    plt.savefig(outpath)
    print("Successfully added:", outpath)

    

if __name__ == "__main__":
    
    if len(sys.argv) == 2:
        handle = sys.argv[1]

        make_plot(handle)
    elif len(sys.argv) == 3:
        handle = sys.argv[1]
        maxtags = int(sys.argv[2])
        make_plot(handle, max_tags=maxtags)
    else:
        print("Enter a Gitcoin handle followed by an optional number of tags to display (max 12")
        print("Example: python funding_graph.py ccerv1 11")