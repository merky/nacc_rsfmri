#!/usr/bin/python

import matplotlib.pyplot as plt
import numpy as np

# creates square matrix (row/col labels are same)
# * current setup shows highlights relationships
def heatmap(matrix, labels=None, limits=[0,1], cm=plt.cm.YlGn_r):
    # limits
    mn,mx = limits

    # Plot it out
    fig, ax = plt.subplots()
    heatmap = ax.pcolor(matrix, cmap=cm, alpha=0.95, vmin=mn, vmax=mx)

    # Format
    fig = plt.gcf()
    fig.set_size_inches(9.5, 8)

    # turn off the frame
    ax.set_frame_on(False)

    # put the major ticks at the middle of each cell
    ax.set_yticks(np.arange(matrix.shape[0]) + 0.5, minor=False)
    ax.set_xticks(np.arange(matrix.shape[1]) + 0.5, minor=False)

    # want a more natural, table-like display
    ax.invert_yaxis()
    ax.xaxis.tick_top()

    # Set the labels
    if labels is None: labels = matrix.index

    # note I could have used nba_sort.columns but made "labels" instead
    ax.set_xticklabels(labels, minor=False)
    ax.set_yticklabels(labels, minor=False)

    # rotate the
    plt.xticks(rotation=90)

    ax.grid(False)

    # Turn off all the ticks
    ax = plt.gca()

    # insert color bar
    plt.colorbar(heatmap)

    for t in ax.xaxis.get_major_ticks():
        t.tick1On = False
        t.tick2On = False
    for t in ax.yaxis.get_major_ticks():
        t.tick1On = False
        t.tick2On = False

    return fig
