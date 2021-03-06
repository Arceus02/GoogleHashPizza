import sys
from src import density
from src import slicer
from src import expander


def solve(data):
    # extract data
    meta = data[0]
    map_pizza = data[1]
    n_lines = meta[0]
    n_columns = meta[1]
    # get prototypes of slices
    slices_prototype = slicer.get_slices_prototype(meta)
    # calculate density map
    print("Calculating density ...")
    map_density = density.get_density_array(data)
    # calculate order of search
    ordered_coordinates_per_level = density.organize_coordinates_by_level(map_density)
    # assign slices that cover a maximum of mean priority
    map_distribution = [[0 for c in l] for l in map_pizza]
    slice_id_counter = 1
    # show progress
    print("Assigning slices ...")
    coordinates_counter = 0
    max_coordinates_counter = n_lines * n_columns
    next_percentage = 0
    for list_coordinates in ordered_coordinates_per_level:
        for coordinates in list_coordinates:
            coordinates_counter += 1
            if int((coordinates_counter / max_coordinates_counter) * 100) == next_percentage:
                sys.stdout.write("\r" + str(int(coordinates_counter / max_coordinates_counter * 100)) + "%")
                next_percentage += 1
            y, x = tuple(coordinates)
            if map_distribution[y][x] == 0:
                slices = slicer.get_all_local_slices(y, x, data, slices_prototype)
                # remove slices that contain at least one used cell
                slices_to_remove = []
                for slice in slices:
                    all_cells_unused = True
                    y0, x0, y1, x1 = tuple(slice)
                    for x in range(x0, x1 + 1):
                        for y in range(y0, y1 + 1):
                            if map_distribution[y][x] != 0:
                                all_cells_unused = False
                    if not all_cells_unused:
                        slices_to_remove.append(slice)
                for slice_to_remove in slices_to_remove:
                    slices.remove(slice_to_remove)
                # remove slices that doesn't contain enough of each components
                slices = slicer.get_all_local_correct_slices(slices, meta, map_pizza)
                if len(slices) > 0:
                    # calculate slices scores
                    slices_score = [0 for k in slices]
                    for i, slice in enumerate(slices):
                        y0, x0, y1, x1 = tuple(slice)
                        for x in range(x0, x1 + 1):
                            for y in range(y0, y1 + 1):
                                slices_score[i] += map_density[y][x]
                        area = (y1 - y0 + 1) * (x1 - x0 + 1)
                        slices_score[i] /= area
                    # get best slice
                    best_slice = slices[slices_score.index(max(slices_score))]
                    # apply slice to distribution
                    y0, x0, y1, x1 = tuple(best_slice)
                    for x in range(x0, x1 + 1):
                        for y in range(y0, y1 + 1):
                            map_distribution[y][x] = slice_id_counter
                    # increment slice id counter for next slice
                    slice_id_counter += 1
    # expand
    print("Expanding (may take a while) ...")
    expander.expand_slices_to_fullest(meta, ordered_coordinates_per_level, map_distribution)
    return map_distribution


def getSlicesData(map_distribution):
    m = [row[:] for row in map_distribution]
    n_lines = len(m)
    n_columns = len(m[0])
    output = ""
    slices_counter = 0
    for i_line in range(n_lines):
        for i_column in range(n_columns):
            # if cell is part of a slice
            slice_id = m[i_line][i_column]
            if slice_id != 0:
                # find slice's points
                x0, y0, x1, y1 = i_column, i_line, i_column, i_line
                while x0 - 1 >= 0 and m[y0][x0 - 1] == slice_id:
                    x0 -= 1
                while x1 + 1 < n_columns and m[y1][x1 + 1] == slice_id:
                    x1 += 1
                while y0 - 1 >= 0 and m[y0 - 1][x0] == slice_id:
                    y0 -= 1
                while y1 + 1 < n_lines and m[y1 + 1][x1] == slice_id:
                    y1 += 1
                # print(y0, x0, y1, x1)
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        m[y][x] = 0
                output += str(y0) + " " + str(x0) + " " + str(y1) + " " + str(x1) + "\n"
                slices_counter += 1
    output = str(slices_counter) + "\n" + output
    return output
