import sys
import progressbar

subject = sys.argv[1]

filepath = "equations/" + subject + ".tex"


def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


with open(filepath, "r") as fin:
    contents = fin.read()

# drop everything before the equation columns
contents = contents.split("{multicols}{3}")[1]
# drop everything after the equation columns
contents = contents.split("\\end{multicols}")[0]
# Split into header groups (discarding empty first element)
header_groups = contents.split("\\textbf")[1:]

print("Creating symbols...")
bar = progressbar.ProgressBar(max_value=len(header_groups))
symbol = {}
num_symbols = 0
for i, header_group in enumerate(header_groups):
    # Break up lines (tossing original \n from previous group)
    header_group = header_group.split("\n")
    header = header_group[0]
    # get the quantity name
    if num_symbols == 0:
        name = header.split("{")[1].split("}")[0]
    else:
        name = header.split("\\textbf{")[1].split("}")[0][1:]

    symbol_line  = header.split("(")[1].split(")")[0]

    symbol_tags = [i for i, x in enumerate(symbol_line) if x == "$"]

    # Populate the symbol dictionary
    symbols = []
    for start, end in pairwise(symbol_tags):
        # Some LaTeX shenanigans are in order
        symb_string = symbol_line[start + 1:end]
        if "_{" in symb_string:
            # ignore subscripts
            symb_string = symb_string.split("_{")[0]
        if "\\mathbf{" in symb_string:
            # Remove boldface wrapper
            symb_string = symb_string.split("\\mathbf{")[1].split("}")[0]
        symbols.append(symb_string)

    # Some quantities have multiple symbols
    for symb in symbols:
        try:
            symbol[name].append(symb)
        except KeyError:
            symbol[name] = [symb]
    i += 1
    bar.update(i)

print("Symbol Dictionary:\n{}".format(symbol.keys()))

# Now find all equations
print("Gathering equations...")
bar = progressbar.ProgressBar(max_value=len(header_groups))
edges = []
for i, header_group in enumerate(header_groups):
    # Establish the principal quantity

    header = header_group.split("\n")[0]

    symbol_line  = header.split("(")[1].split(")")[0]

    symbol_tags = [i for i, x in enumerate(symbol_line) if x == "$"]

    # Populate the symbol dictionary
    symbols = []
    for start, end in pairwise(symbol_tags):
        # Some LaTeX shenanigans are in order
        symb_string = symbol_line[start + 1:end]
        if "_{" in symb_string:
            # ignore subscripts
            symb_string = symb_string.split("_{")[0]
        if "\\mathbf{" in symb_string:
            # Remove boldface wrapper
            symb_string = symb_string.split("\\mathbf{")[1].split("}")[0]
        symbols.append(symb_string)

    # End vertex is always the principal quantity
    dest = symbols[0]
    # Loop through equations, checking for any of symb_string(s)
    for equation_line in header_group.split("\n")[1:-1]:
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
            
        RHS = RHS.split("$")[0]
        for symb_set in symbol.values():
            for symb in symb_set:
                if symb in LHS or symb in RHS:
                    start = symb
                    edges.append((start, dest, equation_line.split("$")[0] + equation_line.split("$")[1]))
    
bar.update(i)
   
print("Edges collected:")
for edge in edges:
   print("Quantities: {}, {}".format(edge[0], edge[1]))
   print("Equation: {}".format(edge[2]))
