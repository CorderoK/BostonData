import streamlit as st
import pandas as pd
import altair as alt


# ---------------------------------------------------------------
# Set wide layout
# ---------------------------------------------------------------
st.set_page_config(layout="wide")


# ---------------------------------------------------------------
# Load and clean the dataset
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("listings.csv.gz", compression="gzip", low_memory=False)


    # Clean price and availability
    df["price"] = df["price"].replace('[\$,]', '', regex=True).astype(float)
    df["availability_365"] = df["availability_365"].fillna(0)


    # Clean neighborhood
    df["neighbourhood_cleansed"] = df["neighbourhood_cleansed"].astype(str).str.strip()
    df["neighbourhood_cleansed"] = df["neighbourhood_cleansed"].replace(["", "nan", "NaN", "None"], "Unknown")
    df["neighbourhood_cleansed"] = df["neighbourhood_cleansed"].fillna("Unknown")


    return df


df = load_data()


# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.title("Filter Listings")


room_type_options = sorted(df["room_type"].dropna().unique())
neighborhood_options = sorted(df["neighbourhood_cleansed"].dropna().unique())


room_type = st.sidebar.multiselect(
    "Room Type",
    options=room_type_options,
    default=room_type_options
)


neighborhood = st.sidebar.multiselect(
    "Neighborhood",
    options=neighborhood_options,
    default=neighborhood_options
)


price_range = st.sidebar.slider(
    "Price Range ($)",
    float(df["price"].min()),
    float(df["price"].max()),
    (50.0, 300.0)
)


# ---------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------
filtered_df = df[
    (df["room_type"].isin(room_type)) &
    (df["neighbourhood_cleansed"].isin(neighborhood)) &
    (df["price"] >= price_range[0]) &
    (df["price"] <= price_range[1])
]


# ---------------------------------------------------------------
# Chart 1: Boxplot of Prices by Neighborhood (interactive)
# ---------------------------------------------------------------
boxplot = alt.Chart(filtered_df).mark_boxplot(extent="min-max").encode(
    x=alt.X("neighbourhood_cleansed:N",
            sort=alt.EncodingSortField(field="price", op="median", order="descending"),
            axis=alt.Axis(labelAngle=-45, labelLimit=400, labelOverlap=False),
            title="Neighborhood"),
    y=alt.Y("price:Q", title="Price (USD)"),
    color=alt.Color("neighbourhood_cleansed:N", legend=None),
    tooltip=["neighbourhood_cleansed", "price"]
).properties(
    width=max(1000, 30 * filtered_df["neighbourhood_cleansed"].nunique()),
    height=400,
    title="Distribution of Prices by Neighborhood (Interactive)"
).interactive()


# ---------------------------------------------------------------
# Chart 2: Scatter plot of Price vs Availability (with color legend)
# ---------------------------------------------------------------
scatter = alt.Chart(filtered_df).mark_circle(size=60, opacity=0.5).encode(
    x=alt.X("availability_365:Q", title="Availability (days per year)"),
    y=alt.Y("price:Q", title="Price (USD)"),
    color=alt.Color("room_type:N",
                    scale=alt.Scale(scheme="category10"),
                    legend=alt.Legend(title="Room Type")),
    tooltip=["name", "room_type", "neighbourhood_cleansed", "availability_365", "price"]
).interactive().properties(
    width=1000,
    height=400,
    title="Price vs. Availability (Interactive Zoom & Pan)"
)


# ---------------------------------------------------------------
# Chart 3: Heatmap of Room Types by Neighborhood (log color scale)
# ---------------------------------------------------------------
heatmap_data = (
    filtered_df
    .groupby(["neighbourhood_cleansed", "room_type"])
    .size()
    .reset_index(name="count")
)
heatmap_data = heatmap_data[heatmap_data["count"] > 0]


num_neighborhoods = heatmap_data["neighbourhood_cleansed"].nunique()
row_height = 30
chart_height = max(300, num_neighborhoods * row_height)


heatmap = alt.Chart(heatmap_data).mark_rect().encode(
    x=alt.X("room_type:N", title="Room Type", axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("neighbourhood_cleansed:N", title="Neighborhood"),
    color=alt.Color("count:Q",
                    scale=alt.Scale(type="log", scheme="blues"),
                    legend=alt.Legend(title="Listing Count (log)")),
    tooltip=["neighbourhood_cleansed:N", "room_type:N", "count:Q"]
).properties(
    width=800,
    height=chart_height,
    title="Distribution of Room Types by Neighborhood (Log Scale)"
).configure_axis(
    labelFontSize=14,
    titleFontSize=16
).configure_title(
    fontSize=18
)


# ---------------------------------------------------------------
# Layout
# ---------------------------------------------------------------
st.altair_chart(boxplot, use_container_width=True)
st.altair_chart(scatter, use_container_width=True)


st.subheader("Distribution of Room Types by Neighborhood")
if heatmap_data.empty:
    st.warning("No listings available with the current filters.")
else:
    st.altair_chart(heatmap, use_container_width=True)




