import sys
import progressbar
import re
from pylab import figure, axes, pie, title, show
import pylab

from mayavi import mlab
import random
import numpy as np

import matplotlib.pyplot as plt

import networkx as nx

# -*- coding: utf-8 -*-
""" Parser docstring

This script takes a LaTeX list of equations, then:
    1. Generates a dictionary of detected quantities
       and their associated symbols
    2. Generates a list of equations mapping one quantity to another
    3. Generates a graph, with
        - quantities as vertices, and
        - one-way mappings as directed edges
    4. Uses a symbol-complexity dictionary to weight each edge by
       estimated computational complexity
    5. Uses a shortest-path algorithm to solve a given problem
    6. Generates a graph with edges complexity-colormapped
"""

# name file w/ subject area
subject = sys.argv[1]
filepath = "equations/" + subject + ".tex"

# dictionary of complexities
complexity_weights = {"\\times": 0.5, "\\rcurs": 1.0, "\\brcurs": 1.0,
                      "\\int": 0.5, "\\oint": 0.5, "\\nabla": 0.2}

# For looping through
def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)

# Grab file contents
with open(filepath, "r") as fin:
    contents = fin.read()

# drop everything before the equation columns (LaTeX configurations)
contents = contents.split("{multicols}{3}")[1]
# drop everything after the equation columns
contents = contents.split("\\end{multicols}")[0]
# Split into header (quantity) groups (discarding empty first element)
header_groups = contents.split("\\textbf")[1:]

# Create the symbol dictionary
print("Creating symbols...")
bar = progressbar.ProgressBar(max_value=len(header_groups))
symbol = {}
num_symbols = 0
for i, header_group in enumerate(header_groups):
    # Break up lines (tossing original \n from previous group)
    header_group = header_group.split("\n")
    # The header (principal quantity) is the first line
    header = header_group[0]
    # get the quantity name
    # TODO this loop may be useless, as num_sybols never increments
    if num_symbols == 0:
        name = header.split("{")[1].split("}")[0]
    else:
        name = header.split("\\textbf{")[1].split("}")[0][1:]

    # Consider the symbols associated with the principal quantity
    symbol_line  = header.split("(")[1].split(")")[0]

    # DEBUG why is magnetic dipole moment not bold?
    # print("SYMBOL LINE: {}\n".format(symbol_line))

    # Locations of LaTeX inline math indicators ($) in the string
    symbol_tags = [i for i, x in enumerate(symbol_line) if x == "$"]

    # Populate the symbol dictionary
    symbols = [] # List of symbols found for this quantity
    # Some LaTeX shenanigans are in order
    for start, end in pairwise(symbol_tags):
        # Grab the first symbol substring
        symb_string = symbol_line[start + 1:end]
        if "_{" in symb_string:
            # ignore subscripts
            symb_string = symb_string.split("_{")[0]
        # Add the (unformatted) symbol to list of symbols found
        symbols.append(symb_string)

    # Some quantities have multiple symbols
    for symb in symbols:
        try:
            symbol[name].append(symb)
        except KeyError:
            symbol[name] = [symb]
    i += 1
    bar.update(i)

# DEBUG check the symbol dictionary
#print("Quantities Found:\n{}\n\n".format(symbol.keys()))
#print("Symbols Found:\n{}\n\n".format(symbol.values()))

# BUG: symbol.values() has an extra list wrapper :/

# name_of maps symbol to the quantity (name)
name_of = {}
for name_of_quantity,quantity_symbols in symbol.items():
    for quantity_symbol in quantity_symbols[0].split(", "):
        name_of[quantity_symbol] = name_of_quantity

# Now find all equations mapping to the principal quantity
print("Gathering equations...")
bar = progressbar.ProgressBar(max_value=len(header_groups))
edges = []
for i, header_group in enumerate(header_groups):
    # Re-establish the principal quantity
    header = header_group.split("\n")[0]

    # TODO this is useless (see above)
    # Get name for this quantity
    if num_symbols == 0:
        name = header.split("{")[1].split("}")[0]
    else:
        name = header.split("\\textbf{")[1].split("}")[0][1:]

    # destination vertex is always the principal quantity
    destinations = name #symbol[name]

    # Non-header quantities
    other_quantities = symbol.copy()
    other_quantities.pop(name)

    # Loop through equations, checking for any of symb_string(s)
    for equation_line in header_group.split("\n")[1:-1]:

        # Create LHS and RHS of each equation
        LHS = ""
        RHS = ""
        if "\\equiv" in equation_line:
            LHS = equation_line.split("\\equiv")[0]
            RHS = equation_line.split("\\equiv")[1]
        elif "\\neq" in equation_line:
            LHS = equation_line.split("\\neq")[0]
            RHS = equation_line.split("\\neq")[1]
        elif "\\pm" in equation_line:
            continue
        else:
            LHS = equation_line.split("=")[0]
            RHS = equation_line.split("=")[1]

        #print("\n\nDEBUG: RHS: {}\n".format(equation_line))

        # RHS will always have the end of the eqution and the condition
        condition = equation_line.split("\\textit{")[1].split("}")[0]

        # Remove condition from RHS
        RHS = RHS.split("$")[0]
        LHS = LHS.split("$")[1]
        equation = "$" + equation_line.split("$")[1] + "$"

        mapped_from_side = RHS
        # establish mapped-from side
        for symb in symbol[name]:
            if symb in RHS:
                mapped_from_side = LHS

        # For every possible symbol,
        for symb in name_of.keys():
            # print(symb)
            # If the symbol is in the (non-quantity) side,
            if symb in mapped_from_side:
                # Add a new edge to the graph
                # (start symbol, end symbol, equtaion, condition)
                # BUG: i throw out the secondary symbol (symbol[name] yields a list)
                # Names
                start = "$" + symb.split(",")[0] + "$"
                end = "$" + symbol[name][0].split(",")[0] + "$"
                #edges.append((symb, symbol[name][0], equation, condition))
                edges.append((start, end, equation, condition))

    bar.update(i)

print("{} edges collected\n".format(len(edges)))

# TODO compute edge weights here instead of after, so they can go into the dict
# condition edges properly for networkx
nedges = []
for edge in edges:
    edge_dict = {"eqn": edge[2], "condition": edge[3]}
    nedges.append((edge[0], edge[1], edge_dict))

symbol_verts = ["$" + wrapper[0].split(",")[0] + "$" for wrapper in symbol.values()]

print("Constructing graph!")
G = nx.DiGraph()

# Add graph nodes
labels = {}
for i, node in enumerate(symbol_verts):
    G.add_node(node)#, label=r"$\sigma$")
    labels[i] = node

# Add graph edges
G.add_edges_from(nedges)

# Compute edge weights
e_weights = []
for edge in G.edges:
    eqn = G.get_edge_data(edge[0], edge[1])["eqn"]
    edge_weight = 0.0
    for flag in complexity_weights.keys():
        edge_weight += complexity_weights[flag] * float(len([m.start() for m in re.finditer(flag, eqn)]))
    e_weights.append(edge_weight)

# Color nodes by popularity
n_weights = []
for node in G.nodes():
    n_weights.append(G.in_degree(node))

# Visualization
figure(1, figsize=(8, 8))
pos = nx.circular_layout(G)
nx.draw(G, pos=pos, node_color=n_weights, edge_color=e_weights,
        with_labels=True, font_weight='bold', cmap=plt.cm.spring)

#edge_labels = nx.get_edge_attributes(G,'eqn')
#nx.draw_networkx_edge_labels(G, pos, edge_labels = e_weights)

pylab.savefig('tmp.png')
