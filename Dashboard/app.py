import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import pickle


#################################################################### PAGE CONFIGURATION ####################################################################
st.set_page_config(page_title="Getaround Project Dashboard", page_icon="🚦", layout="wide")


#################################################################### SIDEBAR MENU ####################################################################

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["🏠 Home/Introduction", "📊 Delays Analysis", "💸 Price Prediction", "🎉 The End & Thank You"])

e = st.sidebar.empty()
e.write("")
st.sidebar.write("Made with 💖💗❤️‍🔥 by Youenn PATAT")
e = st.sidebar.empty()
e.write("")
st.sidebar.image("Aventurine_3.png", use_container_width=True)
st.sidebar.markdown("« 🥂 Cheers, dear reader! 🍷»")


#################################################################### Loading data ####################################################################
####################################################################       &      ####################################################################
#################################################################### Cleaning data ####################################################################
@st.cache_data 
def load_data():
    data = pd.read_excel("https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_delay_analysis.xlsx")
    return data
    
@st.cache_data 
def load_data_price():
    data_price = pd.read_csv("https://full-stack-assets.s3.eu-west-3.amazonaws.com/Deployment/get_around_pricing_project.csv", index_col=0)
    return data_price

data_load_state = st.text('Loading data...')
data = load_data()
data_price = load_data_price()
data_load_state.text("")

mean_rental_per_day = data_price["rental_price_per_day"].mean()

# Count the number of entries with delay_at_checkout_in_minutes > mean + 3*std and < mean - 3*std
mean_delay_checkout = data["delay_at_checkout_in_minutes"].mean()
std_delay_checkout = data["delay_at_checkout_in_minutes"].std()
outliers = data[(data['delay_at_checkout_in_minutes'] > (mean_delay_checkout + 3* std_delay_checkout)) |
                 (data['delay_at_checkout_in_minutes'] < (mean_delay_checkout - 3* std_delay_checkout))]
# Get the count of such entries
num_outliers = len(outliers)
# Filter out and remove the outliers
data = data[(data['delay_at_checkout_in_minutes'] <= (mean_delay_checkout + 3* std_delay_checkout)) & (data['delay_at_checkout_in_minutes'] >= (mean_delay_checkout - 3* std_delay_checkout)) | (data['delay_at_checkout_in_minutes'].isna())]
# We keep the Nan values to keep information of the cancel state of the rental, if not all the cancel state would be removed
# Define a function to categorize delays
def categorize_delay(delay):
    if pd.isna(delay):
        return "Unknown"
    elif delay <= 0:
        return "Early or in time"
    elif delay < 60:
        return "< 1 hour"
    elif delay < 120:
        return "1 to 2 hours"
    elif delay < 180:
        return "2 to 3 hours"
    elif delay < 360:
        return "3 to 6 hours"
    elif delay < 720:
        return "6 to 12 hours"
    elif delay < 1440:
        return "12 to 24 hours"
    else:
        return "1 day or more"
# Apply function to create the new column
data["checkout_delay_category"] = data["delay_at_checkout_in_minutes"].apply(categorize_delay)

#################################################################### HOME PAGE ####################################################################

if page == "🏠 Home/Introduction":
    st.title("Welcome to the Getaround Project Dashboard ⌚🚗⌚")
    st.image("https://lever-client-logos.s3.amazonaws.com/2bd4cdf9-37f2-497f-9096-c2793296a75f-1568844229943.png", use_container_width=True)
    st.image("https://imgcdn.stablediffusionweb.com/2024/4/2/85a87b99-264f-4692-b507-7d84b2e4c351.jpg", use_container_width=True)
    st.markdown("""
    ## Introduction
    This project aims to analyze the impact of a new feature of threshold to deal with problematic cases when there are delays at the check-out for a rental.
    
    🟠 **What you'll find in this app**:
    * 📊 Data insights on rental delays & affected revenue.
    * 📉 Strategies to mitigate issues.
    * 🎯 Conclusion & recommendations.
    
    **Use the sidebar** to navigate between pages. 🚀
                
    In this first page, you will find out the presentation of data and first views of it. In the **Delays Analysis** page, you will find the analysis of the problem and answers. 
    And in the last page, some thanking and link for my other works.
    """)

    st.subheader("📌 - Basic analysis and view of data",  divider="orange")

    # diplay raw data for delays
    st.write("Raw Data")
    if st.checkbox('Show raw data'):
        st.subheader('Raw data')
        st.write(data) 

    
    # Calculate the value counts of each delay category
    delay_counts = data['checkout_delay_category'].value_counts()
    # Calculate the percentage of each category
    delay_percentages = (delay_counts / delay_counts.sum()) * 100

    st.markdown("""
    Firstly, we want to check the proportion of check-in type (`mobile` or `connect`) and the proportion of the rentals' states (`ended` or `canceled`).
    """)

    col1, col2 = st.columns([1, 2])
    with col1:
        #visualisation of the percentage of the mobile vs connect check rental
        checkin_counts = data["checkin_type"].value_counts().reset_index()
        checkin_counts.columns = ["checkin_type", "count"]
        fig1 = px.pie(checkin_counts, 
                    names="checkin_type", 
                    values="count", 
                    title="Check-in Type Distribution",
                    color_discrete_sequence=["#3CB371", "#FFA500"])
        fig1.update_traces(textfont_color="black")
        st.plotly_chart(fig1, use_container_width=True, key="1")


    # Add text in the second column
    with col2:
        #visualisation of the percentage of the mobile vs connect check rental
        cancel_counts = data["state"].value_counts().reset_index()
        cancel_counts.columns = ["state", "count"]
        fig2 = px.pie(cancel_counts, 
                    names="state", 
                    values="count", 
                    title="Proportion of rentals' states",
                    color_discrete_sequence=["#3CB371", "#FFA500"])
        fig2.update_traces(textfont_color="black")
        st.plotly_chart(fig2, use_container_width=True, key="2")

    st.markdown("""
    So, we see that the majority of check-in are made by mobile, only 20% are made by the connected car. 
    Moreover, in our case, with that dataset, we see that rentals are cancels for 15% of rentals.
    """)

    st.markdown("""
                Now let's check the distribution of checkout delays in function of category of time.
                """)
    # Count occurrences of each category
    delay_counts = data["checkout_delay_category"].value_counts().reset_index()
    delay_counts.columns = ["Category", "Count"]
    delay_counts["Percentage"] = (delay_counts["Count"] / delay_counts["Count"].sum()) * 100
    # Define custom colors
    custom_colors = {
        "Early or in time": "#FFA500",  # Orange
    }
    # Assign green as the default color
    for category in delay_counts["Category"]:
        if category not in custom_colors:
            custom_colors[category] = "#3CB371"  # Green
    # Create a bar chart
    fig3 = px.bar(
        delay_counts, 
        x="Category", 
        y="Count", 
        title="Distribution of Checkout Delays", 
        labels={"Category": "Checkout Delay Category", "Count": "Number of Rentals"},
        color="Category",
        text=delay_counts["Percentage"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_map=custom_colors,
    )
    fig3.update_traces(textfont_color="black")
    fig3.update_xaxes(showgrid=False, tickfont=dict(color='black'))
    fig3.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig3.update_layout(xaxis_title="", yaxis_title="", title_font=dict(weight="bold"), showlegend=False, xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
    st.plotly_chart(fig3, use_container_width=True, theme=None)
    st.markdown("""
                There is only 32.6% of rental checkout that are early or in time, without delay. 
                For 23.4% we don't have informations. And the majoruty of delays are less than 2 hours.
                """)

    # Count occurrences of each category grouped by checkin_type
    delay_counts = data.groupby(["checkout_delay_category", "checkin_type"]).size().reset_index(name="Count")
    delay_counts["Percentage"] = (delay_counts["Count"] / delay_counts["Count"].sum()) * 100
    # Create a grouped bar chart
    fig4 = px.bar(
        delay_counts, 
        x="checkout_delay_category", 
        y="Count", 
        color="checkin_type",
        title="Distribution of Checkout Delays by Check-in Type", 
        labels={"checkout_delay_category": "Checkout Delay Category", "Count": "Number of Rentals", "checkin_type": "Check-in Type"},
        barmode="group",  # Groups bars side by side
        #text="Count",
        text=delay_counts["Percentage"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_sequence=["#FFA500", "#3CB371"]
    )
    # Improve layout by setting custom order for x-axis
    fig4.update_traces(textfont_color="black")
    fig4.update_xaxes(showgrid=False, tickfont=dict(color='black'))
    fig4.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig4.update_layout(xaxis_title="", yaxis_title="", title_font=dict(weight="bold"), xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
    fig4.update_layout(xaxis={'categoryorder':'array', 'categoryarray': [
        "Early or in time", "< 1 hour", "1 to 2 hours", "2 to 3 hours",
        "3 to 6 hours", "6 to 12 hours", "12 to 24 hours", "1 day or more", "Unknown"
    ]})
    st.plotly_chart(fig4, use_container_width=True,  theme=None)
    st.markdown("""
                There is much more delay problem with mobile checkin type than connect.
                """)
    
    st.markdown("""
                Great ! Now for the following analysis, go to the next page "**📊 Delays Analysis**" !
                """)    

#################################################################### DELAYS ANALYSIS ####################################################################

elif page == "📊 Delays Analysis":
    st.title("Analysis & Insights 📊")
    st.markdown("""
    Here, we analyze the delay problematic and how to solve it with threshold and a certain scope.
    
    **Key Findings**:
    - 🚗 A minimum delay of **X minutes** reduces scheduling conflicts.
    - 💰 Potential revenue impact: **Y% of total revenue**.
    - ✅ Solving **Z% of problematic cases** with the policy.

    *Visuals and explanations go here.*
                
    In the following, we will focus on the next steps and questions:
                * How often are drivers late for the next check-in? How does it impact the next driver?
                * Which share of our owner’s revenue would potentially be affected by the feature?
                * How many rentals would be affected by the feature depending on the threshold and scope we choose?
                * How many problematic cases will it solve depending on the chosen threshold and scope?
    """)

    st.subheader("📌 - How often are drivers late for the next check-in? How does it impact the next driver?",  divider="orange")

    st.markdown("""
                So, for the first question, here's the visualization of the check-out that are `late`, `early or in time` and the `unknown` data.
                """)
    
    # Count occurrences of category & group category as simple "late", "in time" or "unknown"
    delay_drivers = data["checkout_delay_category"].apply(lambda x: "Early or in time" if x == "Early or in time"
                                                                    else "Unkonwn" if x == "Unknown"
                                                                    else "Late").value_counts().reset_index()
    delay_drivers.columns = ["Category", "Count"]
    delay_drivers["Percentage"] = (delay_drivers["Count"] / delay_drivers["Count"].sum()) * 100
    # Create a bar chart
    fig5 = px.bar(
        delay_drivers, 
        x="Category", 
        y="Count", 
        labels={"Category": "Checkout Delay Category", "Count": "Number of Rentals"},
        title="Distribution of Checkout Delays", 
        text=delay_drivers["Percentage"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_sequence=["#FFA500"],
    )
    fig5.update_traces(textfont_color="black")
    fig5.update_xaxes(showgrid=False, tickfont=dict(color='black'))
    fig5.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig5.update_layout(xaxis_title="", yaxis_title="", title_font=dict(weight="bold"), showlegend=False, xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
    st.plotly_chart(fig5, use_container_width=True, theme=None)

    # Count occurrences of each category
    delay_counts = data["checkout_delay_category"].value_counts().reset_index()
    delay_counts.columns = ["Category", "Count"]
    delay_counts["Percentage"] = (delay_counts["Count"] / delay_counts["Count"].sum()) * 100
    # Define custom colors
    custom_colors = {
        "Early or in time": "#FFA500",  # Orange
    }
    # Assign green as the default color
    for category in delay_counts["Category"]:
        if category not in custom_colors:
            custom_colors[category] = "#3CB371"  # Green
    # Create a bar chart
    fig6 = px.bar(
        delay_counts, 
        x="Category", 
        y="Count", 
        title="Distribution of Checkout Delays", 
        labels={"Category": "Checkout Delay Category", "Count": "Number of Rentals"},
        color="Category",
        text=delay_counts["Percentage"].apply(lambda x: f"{x:.1f}%"),
        color_discrete_map=custom_colors,
    )
    fig6.update_traces(textfont_color="black")
    fig6.update_xaxes(showgrid=False, tickfont=dict(color='black'))
    fig6.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig6.update_layout(xaxis_title="", yaxis_title="", title_font=dict(weight="bold"), showlegend=False, xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
    st.plotly_chart(fig6, use_container_width=True, theme=None)

    st.markdown("""
                Only 32.6% of the check-out are early or in time, whereas almost half of the check-out (44%) are late.
                """)
    
    st.markdown("""
                Now, for the 2nd question, let's see how delays impact the next driver.
                """)
    
    mean_delay_impact = data["time_delta_with_previous_rental_in_minutes"].mean()
    min_delay_impact = data["time_delta_with_previous_rental_in_minutes"].min()
    max_delay_impact = data["time_delta_with_previous_rental_in_minutes"].max()

    st.markdown("#### Delay impacting informations on the next driver 🚘:")

    st.write(f"▪️*Average delay impacting next driver:* {mean_delay_impact:.2f} minutes")
    st.write(f"▪️*Minimum delay impacting next driver:* {min_delay_impact:.2f} minutes")
    st.write(f"▪️*Maximum delay impacting next driver:* {max_delay_impact:.2f} minutes")

    delay_impact = data

    delay_impact["delta-late_checkout"] = delay_impact["time_delta_with_previous_rental_in_minutes"] - delay_impact["delay_at_checkout_in_minutes"]
    #if negative delta - late checkout, it means that the new rental cannot do its check-in
    negative_delay_impact = delay_impact[delay_impact["delta-late_checkout"] < 0]
    late_checkout = delay_drivers[delay_drivers["Category"] == "Late"]["Count"][0]
    nb_problematic_checkin_late = len(negative_delay_impact)
    # percentage calculation
    problematic_delays_rate = nb_problematic_checkin_late*100/late_checkout
    st.write(f"▪️Among all the delays ({late_checkout}), {problematic_delays_rate:.3f}% \n of delays caused problems to the next rental because the checkout\n was made later than the new rental checkin.")

    # Calculate the average duration of problematic delays
    average_problematic_delay = negative_delay_impact['delay_at_checkout_in_minutes'].mean()
    # Calculate the average duration of non-problematic delays
    average_non_problematic_delay = data[data['delay_at_checkout_in_minutes'] > 0]['delay_at_checkout_in_minutes'].mean()
    # Compare the averages
    st.write(f"▪️Average Duration of Problematic Delays: {average_problematic_delay:.0f} minutes")
    st.write(f"▪️Average Duration of Non-Problematic Delays: {average_non_problematic_delay:.0f} minutes")
    
    delay_impact["problematic_delay"] = delay_impact["delta-late_checkout"] < 0
    delay_impact["problematic_delay"].value_counts()

    fig7 = px.histogram(delay_impact, x="problematic_delay", color_discrete_sequence=["#FFA500"], title="Proportion of problematic delays"
                )
    fig7.update_xaxes(
        categoryorder='array',
        categoryarray=["Problematic", "Non-Problematic"],
        showgrid=False, tickfont=dict(color='black')
    )
    fig7.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig7.add_annotation(x=3, y=10000,text=f"Avg Delay: {average_problematic_delay:.2f} min",showarrow=False)
    fig7.add_annotation(x=2, y=10000,text=f"Avg Delay: {average_non_problematic_delay:.2f} min",showarrow=False)
    fig7.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=[True, False],
            ticktext=["Problematic Delay", "Non Problematic Delay"],
            zeroline=True,zerolinecolor="black",zerolinewidth=2
        ),
        xaxis_title="",
        yaxis_title="",
        title_font=dict(weight="bold"),
        showlegend=False,
        plot_bgcolor="#BDDFD6"
    )
    fig7.update_traces(textfont_color="black")
    st.plotly_chart(fig7, use_container_width=True, theme=None)

    st.markdown("""
                For the majority of cases, it poses no problem to have delay, but for 2.857% of the case it is problematic for the following rental.
                """)
    
    st.subheader("📌 - Which share of our owner’s revenue would potentially be affected by the feature?",  divider="orange")

    # Define the treshold of minimum time between 2 locations (minutes)
    thresholds = [30, 60, 90, 120, 180, 360, 720, 1440]  # Example : 1 hour

    data["mean_price_per_rental"] = mean_rental_per_day

    treshold_data = data
    percentage_revenue_impacted = []
    percentage_revenue_impacted_displaying = {}

    for threshold in thresholds:
        treshold_data[f"affected_rentals_{threshold}"] = data["time_delta_with_previous_rental_in_minutes"] <= threshold
        affected_rentals = data[data["time_delta_with_previous_rental_in_minutes"] <= threshold]
        affected_revenue = affected_rentals["mean_price_per_rental"].sum()
        total_revenue = data["mean_price_per_rental"].sum()
        revenue_impact = (affected_revenue / total_revenue) * 100
        percentage_revenue_impacted.append(revenue_impact)
        percentage_revenue_impacted_displaying[threshold] = round(revenue_impact, 3)

    col1, col2 = st.columns([1, 2])
    with col1:
        # Select a threshold
        selected_threshold = st.selectbox("Select a threshold ⏳ (in minutes):", thresholds, key="selectbox_1")
        # Display impacted revenue percentage
        st.metric(label="💰 Impacted Revenue", value=f"{percentage_revenue_impacted_displaying[selected_threshold]}%")
    
    with col2:
        affected_counts = [treshold_data[f"affected_rentals_{threshold}"].value_counts().get(True, 0) for threshold in thresholds]
        affected_rentals_plot = pd.DataFrame({"Threshold (min)": thresholds, "Affected rentals": affected_counts})

        fig8 = px.line(affected_rentals_plot, x="Threshold (min)", y="Affected rentals", text="Affected rentals",
                    title="Number of rentals affected by the treshold",
                    color_discrete_sequence=["#3CB371"],)
        fig8.update_traces(textposition='top center', textfont_color="black")
        fig8.update_xaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'), showline=True, linewidth=2, linecolor='black')
        fig8.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
        fig8.update_layout(xaxis_title="", yaxis_title="", title_font=dict(weight="bold"), showlegend=False, xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
        st.plotly_chart(fig8, use_container_width=True, theme=None)

    
    st.subheader("📌 - How many rentals would be affected by the feature depending on the threshold and scope we choose?",  divider="orange")

    all_affected_list = []
    all_affected_display = {}
    connect_affected_list = []
    connect_affected_display = {}
    all_affected_percentage = {}
    connect_affected_percentage = {}

    for threshold in thresholds:
        all_rentals = len(data)
        all_affected = data[data["time_delta_with_previous_rental_in_minutes"] <= threshold].shape[0]
        all_affected_list.append(all_affected)
        connect_affected = data[(data["time_delta_with_previous_rental_in_minutes"] <= threshold) & 
                                (data["checkin_type"] == "connect")].shape[0]
        connect_affected_list.append(connect_affected)
        all_affected_display[threshold] = all_affected
        connect_affected_display[threshold] = connect_affected
        all_affected_percentage[threshold] = (all_affected / all_rentals) * 100
        connect_affected_percentage[threshold] = (connect_affected / all_rentals) * 100

    # Select a threshold
    selected_threshold = st.selectbox("Select a threshold ⏳ (in minutes):", thresholds, key="selectbox_2")
    # Add a title before metrics
    st.markdown(f"#### 🚗 Rentals Affected by the {selected_threshold}-Minutes Threshold")

    col1, col2 = st.columns(2)
    # Display metrics side by side
    with col1:
        st.metric(label="📲 All check-ins affected in number ⇩", value=f"{all_affected_display[selected_threshold]}")
        st.metric(label="📲 All check-ins affected in % ⇩", value=f"{all_affected_percentage[selected_threshold]:.3f}")

    with col2:
        st.metric(label="🛜 Connect check-ins affected in number ⇩", value=f"{connect_affected_display[selected_threshold]}")
        st.metric(label="🛜 Connect check-ins affected in % ⇩", value=f"{connect_affected_percentage[selected_threshold]:.3f}")

    data_affected = pd.DataFrame({ "thresholds" : thresholds,
                 "all_affected" : all_affected_list,
                 "connect_affected" : connect_affected_list})
    
    fig9 = px.scatter(data_affected, x='thresholds', y='all_affected',
                    color_discrete_sequence=["#FFA500"],
                    labels={'all_affected': 'All Affected'},
                    title="Rentals affected by Thresholds in function of the type of check-in")
    # Add a line for 'all_affected'
    fig9.add_trace(go.Scatter(x=data_affected['thresholds'], y=data_affected['all_affected'],
        mode='lines+markers+text', line=dict(color='#FFA500'), name='All Affected', text=data_affected['all_affected']))

    fig9.add_trace(go.Scatter(x=data_affected['thresholds'], y=data_affected['connect_affected'], 
                        mode='lines+markers+text', marker_color='#3CB371', name='Connect Affected',
                        text=data_affected['connect_affected'],))  # Texte à afficher sur les marqueurs
    fig9.update_traces(textposition='top center', textfont_color="black")
    fig9.update_xaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'), showline=True, linewidth=2, linecolor='black')
    fig9.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig9.update_layout(xaxis_title="", yaxis_title="", title_font=dict(weight="bold"), showlegend=True, xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
    st.plotly_chart(fig9, use_container_width=True, theme=None)

    st.markdown("""
                There are less rentals affected with the scope only on connected check-in than all 
                (mobile + connect) check-in. Moreover, as it could be expected, more rentals are 
                impacted with an increasing of the threshold choice.""")
    
    st.subheader("📌 - How many problematic cases will it solve depending on the chosen threshold and scope?",  divider="orange")

    solved_cases_all_list = []
    solved_cases_connect_list = []

    for threshold, i in zip(thresholds, range(len(thresholds))):

        problematic_cases = negative_delay_impact[(negative_delay_impact["delay_at_checkout_in_minutes"] <= threshold)]
        problematic_connectec_case = negative_delay_impact[(negative_delay_impact["delay_at_checkout_in_minutes"] <= threshold) & 
                                                        (negative_delay_impact["checkin_type"] == "connect")]
        total_problems_cases = len(negative_delay_impact)
        total_connect_pb_cases = len(negative_delay_impact[negative_delay_impact["checkin_type"] == "connect"])

        solved_cases = problematic_cases.shape[0]
        solved_cases_all_list.append(solved_cases)
        solved_cases_connect = problematic_connectec_case.shape[0]
        solved_cases_connect_list.append(solved_cases_connect)

        percentage_solved_all = (solved_cases / total_problems_cases) * 100
        percentage_connect_solved = (solved_cases_connect / total_connect_pb_cases) * 100

    # Convert to DataFrame
    df_solved_cases = pd.DataFrame({
        "Threshold (minutes)": thresholds,
        "Solved Cases (All Check-ins)": solved_cases_all_list,
        "Solved Cases (Connect Check-ins)": solved_cases_connect_list,
        "Revenue Impacted (%)": percentage_revenue_impacted
    })

    # Select a threshold with a slider
    selected_threshold = st.selectbox("Select a threshold ⏳ (in minutes):", thresholds, key="selectbox_3")

    # Get values for selected threshold
    selected_data = df_solved_cases[df_solved_cases["Threshold (minutes)"] == selected_threshold].iloc[0]

    # Display Metrics in Two Columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📲 All Check-ins Solved", value=f"{selected_data['Solved Cases (All Check-ins)']}")
    with col2:
        st.metric(label="🛜 Connect Check-ins Solved", value=f"{selected_data['Solved Cases (Connect Check-ins)']}")
    with col3:
        st.metric(label="💰 Revenue Impacted", value=f"{selected_data['Revenue Impacted (%)']:.2f} %")

    # Create the figure
    fig10 = go.Figure()
    # Add line for "All Check-ins"
    fig10.add_trace(go.Scatter(
        x=thresholds, 
        y=solved_cases_all_list, 
        mode="lines+markers", 
        name="Solved Cases (All Check-ins)", 
        marker=dict(color="#FFA500")
    ))
    # Add line for "Connect Check-ins"
    fig10.add_trace(go.Scatter(
        x=thresholds, 
        y=solved_cases_connect_list, 
        mode="lines+markers", 
        name="Solved Cases (Connect Check-ins)", 
        marker=dict(color="#3CB371")
    ))
    # Add vertical dashed lines with text annotations
    for i, threshold in enumerate(thresholds):
        max_y_value = solved_cases_all_list[i]  # Ensure line stops at "Solved Cases (All Check-ins)"
        
        # Add dashed line from y=0 to y=max_y_value
        fig10.add_trace(go.Scatter(
            x=[threshold, threshold],  # Vertical line at threshold
            y=[0, max_y_value],  # Stop at max_y_value
            mode="lines",
            line=dict(color="red", width=1.5, dash="dash"),
            name="Revenue Impact Annotation" if i == 0 else None,  # Show legend only once
            showlegend=(i == 0)
        ))
        # Add text annotation slightly above the dashed line
        fig10.add_annotation(
            x=threshold, 
            y=max_y_value + 20,  # Position slightly above the dashed line
            text=f"{percentage_revenue_impacted[i]:.2f}%",  # Format percentage
            showarrow=False,
            font=dict(size=10, color="red"),
            align="center",
        )
    fig10.update_traces(textposition='top center', textfont_color="black")
    fig10.update_xaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'), showline=True, linewidth=2, linecolor='black')
    fig10.update_yaxes(showgrid=True, gridcolor='#A9A9A9', tickfont=dict(color='black'))
    fig10.update_layout(title="Number of Problematic Cases Solved by Threshold",xaxis_title="",yaxis_title="", title_font=dict(weight="bold"),showlegend=True, xaxis=dict(zeroline=True,zerolinecolor="black",zerolinewidth=2), plot_bgcolor="#BDDFD6")
    st.plotly_chart(fig10, use_container_width=True, theme=None)

    st.markdown("""
                #### 📊 Data Table""")
    st.dataframe(df_solved_cases)

    st.markdown("""
                Now, we can see the problematic cases solved in function of the check-in type (connect or all {mobile📲 + connect🛜}) 
                with the impacted revenue percentage of each threshold. For me the best choice to solve problem without too much 
                economical impact is to choose the threshold of **180** or **360** minutes, for the scope of all check-in type.""")

    st.markdown("""
                ✨ Thanks for reading all the way through! I hope you enjoyed it and found it interesting.
                Go to the last page, `The End & Thank You`, for a little surprise and links to my other works‼️
                """)
#################################################################### Price prediction ####################################################################

elif page == "💸 Price Prediction":
    st.title("Price Prediction for a Rental 💸💶")
    st.markdown("""
    Here, you can choose the parameters of a car and with a connection to my API, you can have a day price prediction of the car.
    
    🟠 **What you'll find in this page**:
    * 🏎️ Object to select your car's characteristics?
    * 💸 A price prediction for one rental day.
                """)
    
    st.write("Select the car parameters below and get an estimated rental price!")

    # Define API URL
    api_url = "https://hyraxuna-api-getaround.hf.space/predict"

    # Define input fields for car parameters
    car_model = st.selectbox("Car Brand:", ['Citroën','Peugeot','PGO','Renault','Audi','BMW','Mercedes','Opel','Volkswagen','Ferrari','Mitsubishi','Nissan','SEAT','Subaru','Toyota','other'])
    mileage = st.slider("Mileage (km):", 0, 600000, 50000, step=1000)
    engine_power = st.slider("Engine Power (HP):", 0, 1000, 100, step=5)
    fuel = st.selectbox("Fuel Type:", ['diesel','petrol','other'])
    paint_color = st.selectbox("Paint Color:", ['black','grey','white','red','silver','blue','beige','brown','other'])
    car_type = st.selectbox("Car Type:", ['convertible','coupe','estate','hatchback','sedan','subcompact','suv','van'])

    # Boolean Features
    private_parking_available = st.checkbox("Private Parking Available")
    has_gps = st.checkbox("GPS Included")
    has_air_conditioning = st.checkbox("Air Conditioning")
    automatic_car = st.checkbox("Automatic Transmission")
    has_getaround_connect = st.checkbox("Getaround Connect Available")
    has_speed_regulator = st.checkbox("Speed Regulator Installed")
    winter_tires = st.checkbox("Winter Tires Installed")

    # Button to Predict
    if st.button("🔍 Predict Rental Price"):
        st.subheader("💶 Prediction Results")

        # Prepare input data as JSON
        input_data = {
                    "model_key": car_model, 
                    "mileage": mileage,
                    "engine_power": engine_power,
                    "fuel": fuel,
                    "paint_color": paint_color,
                    "car_type": car_type,
                    "private_parking_available": private_parking_available,
                    "has_gps": has_gps,
                    "has_air_conditioning": has_air_conditioning,
                    "automatic_car": automatic_car,
                    "has_getaround_connect": has_getaround_connect,
                    "has_speed_regulator": has_speed_regulator,
                    "winter_tires": winter_tires
                }

        headers = {"Content-Type": "application/json"}

        try:
            # API Request
            response = requests.post(api_url, data=json.dumps(input_data), headers=headers)
            result = response.json()

            if response.status_code == 200:
                predicted_price = result.get("prediction")
                st.success(f"💰 Estimated Rental Price: **{predicted_price} € per day**")
            else:
                st.error("⚠️ Error fetching prediction. Please check API or try again.")
        
        except Exception as e:
            st.error(f"⚠️ API Request Failed: {e}")

#################################################################### END & THANK YOU PAGE ####################################################################

elif page == "🎉 The End & Thank You":
    st.title("Thank You for Exploring! 🎉")

     # Create two columns
    col1, col2 = st.columns([1, 2])  # Adjust column ratio (1:2 for image & text)

    # Add an image in the first column
    with col1:
        st.image("ChibiElf1.png", use_container_width=True) 

    # Add text in the second column
    with col2:
        st.markdown("""
        **Final Thoughts**
        - 🚀 This analysis helps optimize the rental platform.
        - 🔎 Finding the right balance between user experience and revenue impact is key.
        
        **🙏 Thank you for your time!**
        
        📩 Feel free to reach out for more insights.
                    
        Here are the links for my other works on **Github** & **Linkedin**:
        """)

        # Define the GitHub and LinkedIn URLs
        github_url = "https://github.com/HyraXuna?tab=repositories"
        linkedin_url = "https://www.linkedin.com/in/youenn-patat-46b59b246/"

        # Display clickable images for GitHub and LinkedIn
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; gap: 20px;">
                <a href="{github_url}" target="_blank">
                    <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" width="40">
                </a>
                <a href="{linkedin_url}" target="_blank">
                    <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="40">
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.balloons()  # 🎈 Fun effect for celebration!

### Footer 
st.markdown("---")

st.markdown(
    """
    <div style="text-align: center;">
        <p>If you want to see more, check out my <strong>Github</strong> 📖</p>
        <a href="https://github.com/HyraXuna?tab=repositories" target="_blank">
            <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" width="40">
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")
