from re import U
import streamlit as st
import pandas as pd
import altair as alt

@st.cache
def load_data():
    """
    Write 1-2 lines of code here to load the data from CSV to a pandas dataframe
    and return it.
    """
    return pd.read_csv('pulse39.csv')

@st.cache
def get_slice_membership(df, genders, races, educations, age_range):
    """
    Implement a function that computes which rows of the given dataframe should
    be part of the slice, and returns a boolean pandas Series that indicates 0
    if the row is not part of the slice, and 1 if it is part of the slice.
    
    
    In the example provided, we assume genders is a list of selected strings
    (e.g. ['Male', 'Transgender']). We then filter the labels based on which
    rows have a value for gender that is contained in this list. You can extend
    this approach to the other variables based on how they are returned from
    their respective Streamlit components.
    """
    labels = pd.Series([1] * len(df), index=df.index)
    if genders:
        labels &= df['gender'].isin(genders)
    # ... complete this function for the other demographic variables
    if races:
        labels &= df['race'].isin(races)
    if educations:
        labels &= df['education'].isin(educations)
    if age_range:
        labels &= df['age'] >= age_range[0]
        labels &= df['age'] <= age_range[1]
    return labels

def make_long_reason_dataframe(df, reason_prefix):
    """
    ======== You don't need to edit this =========
    
    Utility function that converts a dataframe containing multiple columns to
    a long-style dataframe that can be plotted using Altair. For example, say
    the input is something like:
    
         | why_no_vaccine_Reason 1 | why_no_vaccine_Reason 2 | ...
    -----+-------------------------+-------------------------+------
    1    | 0                       | 1                       | 
    2    | 1                       | 1                       |
    
    This function, if called with the reason_prefix 'why_no_vaccine_', will
    return a long dataframe:
    
         | id | reason      | agree
    -----+----+-------------+---------
    1    | 1  | Reason 2    | 1
    2    | 2  | Reason 1    | 1
    3    | 2  | Reason 2    | 1
    
    For every person (in the returned id column), there may be one or more
    rows for each reason listed. The agree column will always contain 1s, so you
    can easily sum that column for visualization.
    """
    reasons = df[[c for c in df.columns if c.startswith(reason_prefix)]].copy()
    reasons['id'] = reasons.index
    reasons = pd.wide_to_long(reasons, reason_prefix, i='id', j='reason', suffix='.+')
    reasons = reasons[~pd.isna(reasons[reason_prefix])].reset_index().rename({reason_prefix: 'agree'}, axis=1)
    return reasons


# MAIN CODE

st.title("Household Pulse Explorable")
with st.spinner(text="Loading data..."):
    df = load_data()
st.text("Visualize the overall dataset and some distributions here...")

st.write(df)

# 1.1 race & education distribution
race_brush = alt.selection_multi(fields=['race'])
edu_brush = alt.selection_multi(fields=['education'])

race_bar = alt.Chart(df).mark_bar().encode(
    x = 'count()',
    y = alt.Y('race', sort='-x'),
    # tooltip = ['race'],
    color = alt.condition(race_brush, alt.value('steelblue'), alt.value('lightgray'))
).add_selection(race_brush).transform_filter(edu_brush)

edu_bar = alt.Chart(df).mark_bar().encode(
    x = 'count()',
    y = 'education',
    # tooltip = ['education'],
    color = alt.condition(edu_brush, alt.value('salmon'), alt.value('lightgray'))
).add_selection(edu_brush).transform_filter(race_brush)

st.altair_chart(race_bar & edu_bar, use_container_width=True)



st.header("Custom slicing")
# st.text("Implement your interactive slicing tool here...")

## button
genders = st.multiselect("Gender", df.gender.unique())
races = st.multiselect("Race", df.race.unique())
educations = st.multiselect("Education", df.education.unique())
age_range = st.slider("Age", min_value = df.age.min(), max_value = df.age.max(), value = (df.age.min(), df.age.max()))

# slicing data
labels = get_slice_membership(df, genders, races, educations, age_range)
not_labels = pd.Series(1-labels).astype('boolean')
df_slice = df[labels]
df_out_slice = df[not_labels]

# metrics
col1, col2 = st.columns(2)
p1 = round((df_slice[df_slice.received_vaccine].shape[0] / df_slice.shape[0]) * 100, 2)
m1 = round(df_slice.vaccine_intention.mean(), 2)

if df_out_slice.shape[0]:
    p2 = round((df_out_slice[df_out_slice.received_vaccine].shape[0] / df_out_slice.shape[0]) * 100, 2)
    m2 = round(df_out_slice.vaccine_intention.mean(), 2)

# Creates a dataframe with columns 'reason' (string) and 'agree' (boolean)
vaccine_reasons_inslice = make_long_reason_dataframe(df_slice, 'why_no_vaccine_')
reasons1 = alt.Chart(vaccine_reasons_inslice, title='In Slice').mark_bar().encode(
    x='sum(agree)',
    y='reason:O',
).interactive()
if df_out_slice.shape[0]:
    vaccine_reasons_outslice = make_long_reason_dataframe(df_out_slice, 'why_no_vaccine_')
    reasons2 = alt.Chart(vaccine_reasons_outslice, title='Out of Slice').mark_bar().encode(
        x='sum(agree)',
        y='reason:O',
    ).interactive()


with col1:
    st.metric("Percentage received vaccine", p1)
    st.metric("Mean intention in slice (5 is certain not to get vaccine)", m1)
    st.altair_chart(reasons1)
if df_out_slice.shape[0]:
    with col2:
        st.metric("Percentage received vaccine", p2)
        st.metric("Mean intention in slice (5 is certain not to get vaccine)", m2)
        st.altair_chart(reasons2)


st.header("Person sampling")
st.text("Implement a button to sample and describe a random person here...")
