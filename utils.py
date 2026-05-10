def build_filters(location, cuisine, rating_outof_5):

    filters = "WHERE 1=1"

    if location != "All":
        filters += f" AND location = '{location}'"

    if cuisine != "All":
        filters += f" AND cuisines = '{cuisine}'"

    filters += f" AND rating_outof_5 >= {rating_outof_5}"

    return filters