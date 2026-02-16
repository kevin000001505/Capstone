import pandas as pd


lat = [
    89,
    87,
    85,
    83,
    81,
    79,
    77,
    75,
    73,
    71,
    69,
    67,
    65,
    63,
    61,
    59,
    57,
    55,
    53,
    51,
    49,
    47,
    45,
    43,
    41,
    39,
    37,
    35,
    33,
    31,
    29,
    27,
    25,
    23,
    21,
    19,
    17,
    15,
    13,
    11,
    9,
    7,
    5,
    3,
    1,
    -1,
    -3,
    -5,
    -7,
    -9,
    -11,
    -13,
    -15,
    -17,
    -19,
    -21,
    -23,
    -25,
    -27,
    -29,
    -31,
    -33,
    -35,
    -37,
    -39,
    -41,
    -43,
    -45,
    -47,
    -49,
    -51,
    -53,
    -55,
    -57,
    -59,
    -61,
    -63,
    -65,
    -67,
    -69,
    -71,
    -73,
    -75,
    -77,
    -79,
    -81,
    -83,
    -85,
    -87,
    -89,
]
long = [
    -178,
    -174,
    -170,
    -166,
    -162,
    -158,
    -154,
    -150,
    -146,
    -142,
    -138,
    -134,
    -130,
    -126,
    -122,
    -118,
    -114,
    -110,
    -106,
    -102,
    -98,
    -94,
    -90,
    -86,
    -82,
    -78,
    -74,
    -70,
    -66,
    -62,
    -58,
    -54,
    -50,
    -46,
    -42,
    -38,
    -34,
    -30,
    -26,
    -22,
    -18,
    -14,
    -10,
    -6,
    -2,
    2,
    6,
    10,
    14,
    18,
    22,
    26,
    30,
    34,
    38,
    42,
    46,
    50,
    54,
    58,
    62,
    66,
    70,
    74,
    78,
    82,
    86,
    90,
    94,
    98,
    102,
    106,
    110,
    114,
    118,
    122,
    126,
    130,
    134,
    138,
    142,
    146,
    150,
    154,
    158,
    162,
    166,
    170,
    174,
    178,
]


def parse_drap_data(data_string):
    """
    Parse NOAA DRAP (D-Region Absorption Prediction) data

    Parameters:
    -----------
    data_string : str
        The complete DRAP data file content as a string

    Returns:
    --------
    tuple: (metadata_dict, dataframe_wide, dataframe_long)
    """

    lines = data_string.strip().split("\n")
    longitudes = long
    latitudes = lat
    data_rows = []

    metadata = {}
    for line in lines:
        if line.startswith("#"):
            if "Product:" in line:
                metadata["product"] = line.split("Product:")[1].split("/")[0].strip()
            elif "Product Valid At" in line:
                metadata["valid_at"] = line.split("Product Valid At :")[1].strip()
            elif "Estimated Recovery Time" in line:
                metadata["recovery_time"] = line.split("Estimated Recovery Time :")[
                    1
                ].strip()
            elif "X-RAY Message" in line:
                metadata["xray_message"] = line.split("X-RAY Message :")[1].strip()
            elif "X-RAY Warning" in line:
                metadata["xray_warning"] = line.split("X-RAY Warning :")[1].strip()
            elif "Proton Message" in line:
                metadata["proton_message"] = line.split("Proton Message :")[1].strip()

        line = line.strip()
        if "--------" in line or not line or line.startswith("#"):
            continue

        parts = line.split("|")

        # Pass the longitude
        if len(parts) == 2:
            # faster due to carry float instead of str in memnory
            values = [float(v) for v in parts[1].strip().split()]
            data_rows.append(values)

    df_wide = pd.DataFrame(data_rows, columns=longitudes, index=latitudes)
    df_wide.index.name = "Latitude"
    df_wide.columns.name = "Longitude"

    df_long = df_wide.reset_index().melt(
        id_vars="Latitude", var_name="Longitude", value_name="Absorption"
    )

    return metadata, df_wide, df_long
