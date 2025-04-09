import streamlit as st
import pandas as pd
import numpy as np
import datetime
import json
import matplotlib.pyplot as plt
import os
from matplotlib.colors import LinearSegmentedColormap
import random
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="Habit Quest: Track & Level Up",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main {
        background-color: #f5f7ff;
    }
    .css-18e3th9 {
        padding-top: 2rem;
    }
    .streak-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .category-header {
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        color: #1E88E5;
    }
    .achievement-card {
        background-color: #f0f8ff;
        border-left: 4px solid #1E88E5;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0.3rem;
    }
    .level-progress {
        height: 20px;
        background-color: #e0e0e0;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .level-bar {
        height: 100%;
        border-radius: 10px;
        text-align: center;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'habits' not in st.session_state:
    # Default habit categories and examples
    default_categories = {
        "Exercise": ["Walking Pad", "Gym/Training", "Pilates/Yoga"],
        "Reading": ["Fantasy", "Textbooks", "DK Books"],
        "Entertainment": ["Gaming", "Movies/TV", "Sport"],
        "Self Improvement": ["YouTube Learning", "Coding Projects", "Piano"]
    }
    
    st.session_state.habits = {}
    
    # Create default habits with empty completion data
    for category, habits in default_categories.items():
        for habit in habits:
            habit_id = f"{category}_{habit}".replace(" ", "_").lower()
            st.session_state.habits[habit_id] = {
                "name": habit,
                "category": category,
                "streak": 0,
                "longest_streak": 0,
                "completions": {},
                "xp": 0,
                "level": 1,
                "created_date": datetime.now().strftime("%Y-%m-%d")
            }

if 'achievements' not in st.session_state:
    st.session_state.achievements = {
        "streaks": {
            "3_day_streak": {"name": "3-Day Warrior", "description": "Complete a habit for 3 days in a row", "xp": 30, "earned": {}},
            "7_day_streak": {"name": "Week Champion", "description": "Complete a habit for 7 days in a row", "xp": 70, "earned": {}},
            "30_day_streak": {"name": "Monthly Master", "description": "Complete a habit for 30 days in a row", "xp": 300, "earned": {}},
            "100_day_streak": {"name": "Centurion", "description": "Complete a habit for 100 days in a row", "xp": 1000, "earned": {}}
        },
        "milestones": {
            "first_habit": {"name": "First Steps", "description": "Complete any habit for the first time", "xp": 10, "earned": False},
            "five_habits": {"name": "Variety Pack", "description": "Complete 5 different habits", "xp": 50, "earned": False},
            "all_categories": {"name": "Well-Rounded", "description": "Complete at least one habit from each category", "xp": 100, "earned": False}
        }
    }

if 'user' not in st.session_state:
    st.session_state.user = {
        "total_xp": 0,
        "level": 1,
        "next_level_xp": 100
    }

if 'daily_theme' not in st.session_state:
    # Different motivational themes for each day
    themes = [
        "Build momentum today! Every habit counts.",
        "Small steps lead to big changes.",
        "Consistency is your superpower.",
        "Level up your life, one habit at a time.",
        "Today's efforts are tomorrow's results.",
        "Your future self is watching your choices today.",
        "Progress > Perfection"
    ]
    st.session_state.daily_theme = random.choice(themes)

# Functions for saving and loading data
def save_data():
    data = {
        "habits": st.session_state.habits,
        "achievements": st.session_state.achievements,
        "user": st.session_state.user
    }
    
    with open('habit_data.json', 'w') as f:
        # Convert datetime objects to strings before saving
        json.dump(data, f, default=str)

def load_data():
    if os.path.exists('habit_data.json'):
        with open('habit_data.json', 'r') as f:
            data = json.load(f)
            
            # Update session state
            st.session_state.habits = data.get("habits", st.session_state.habits)
            st.session_state.achievements = data.get("achievements", st.session_state.achievements)
            st.session_state.user = data.get("user", st.session_state.user)

# Try to load saved data
try:
    load_data()
except Exception as e:
    st.error(f"Error loading saved data: {e}")

# Function to calculate streak for a habit
def calculate_streak(completions):
    if not completions:
        return 0
        
    dates = sorted([datetime.strptime(date, "%Y-%m-%d") for date in completions.keys() 
                   if completions[date]])
    
    if not dates:
        return 0
    
    # Check if completed today
    today = datetime.now().date()
    latest_date = dates[-1].date()
    
    # If the latest completion is not today or yesterday, streak is broken
    if (today - latest_date).days > 1:
        return 0
    
    # Calculate continuous streak
    streak = 1
    for i in range(len(dates) - 1, 0, -1):
        if (dates[i].date() - dates[i-1].date()).days == 1:
            streak += 1
        else:
            break
            
    return streak

# Function to update streaks for all habits
def update_streaks():
    for habit_id, habit in st.session_state.habits.items():
        current_streak = calculate_streak(habit["completions"])
        
        # Update streak and longest streak
        st.session_state.habits[habit_id]["streak"] = current_streak
        if current_streak > habit["longest_streak"]:
            st.session_state.habits[habit_id]["longest_streak"] = current_streak
        
        # Check for streak achievements
        check_streak_achievements(habit_id, current_streak)

# Function to check and award streak achievements
def check_streak_achievements(habit_id, streak):
    streak_milestones = [3, 7, 30, 100]
    for milestone in streak_milestones:
        achievement_id = f"{milestone}_day_streak"
        if streak >= milestone and habit_id not in st.session_state.achievements["streaks"][achievement_id]["earned"]:
            # Award the achievement and XP
            st.session_state.achievements["streaks"][achievement_id]["earned"][habit_id] = datetime.now().strftime("%Y-%m-%d")
            xp_reward = st.session_state.achievements["streaks"][achievement_id]["xp"]
            award_xp(habit_id, xp_reward)
            
            # Show achievement notification
            achievement_name = st.session_state.achievements["streaks"][achievement_id]["name"]
            habit_name = st.session_state.habits[habit_id]["name"]
            st.success(f"🏆 Achievement Unlocked: {achievement_name} for {habit_name}! +{xp_reward} XP")

# Function to check milestone achievements
def check_milestone_achievements():
    # Check for first habit completion
    completed_habits = []
    completed_categories = set()
    
    for habit_id, habit in st.session_state.habits.items():
        if habit["completions"] and any(habit["completions"].values()):
            completed_habits.append(habit_id)
            completed_categories.add(habit["category"])
    
    # First habit achievement
    if completed_habits and not st.session_state.achievements["milestones"]["first_habit"]["earned"]:
        st.session_state.achievements["milestones"]["first_habit"]["earned"] = True
        xp_reward = st.session_state.achievements["milestones"]["first_habit"]["xp"]
        st.session_state.user["total_xp"] += xp_reward
        st.success(f"🏆 Achievement Unlocked: First Steps! +{xp_reward} XP")
    
    # Five habits achievement
    if len(completed_habits) >= 5 and not st.session_state.achievements["milestones"]["five_habits"]["earned"]:
        st.session_state.achievements["milestones"]["five_habits"]["earned"] = True
        xp_reward = st.session_state.achievements["milestones"]["five_habits"]["xp"]
        st.session_state.user["total_xp"] += xp_reward
        st.success(f"🏆 Achievement Unlocked: Variety Pack! +{xp_reward} XP")
    
    # All categories achievement
    categories = set(habit["category"] for habit in st.session_state.habits.values())
    if completed_categories == categories and not st.session_state.achievements["milestones"]["all_categories"]["earned"]:
        st.session_state.achievements["milestones"]["all_categories"]["earned"] = True
        xp_reward = st.session_state.achievements["milestones"]["all_categories"]["xp"]
        st.session_state.user["total_xp"] += xp_reward
        st.success(f"🏆 Achievement Unlocked: Well-Rounded! +{xp_reward} XP")

# Function to award XP for a habit and update level
def award_xp(habit_id, xp_amount):
    # Award XP to the specific habit
    st.session_state.habits[habit_id]["xp"] += xp_amount
    
    # Calculate level for the habit
    habit_xp = st.session_state.habits[habit_id]["xp"]
    st.session_state.habits[habit_id]["level"] = max(1, int(1 + (habit_xp / 100) ** 0.5))
    
    # Award XP to the user
    st.session_state.user["total_xp"] += xp_amount
    
    # Update user level
    total_xp = st.session_state.user["total_xp"]
    new_level = max(1, int(1 + (total_xp / 100) ** 0.5))
    
    # Level up notification
    if new_level > st.session_state.user["level"]:
        st.balloons()
        st.success(f"🎉 Level Up! You've reached level {new_level}!")
    
    st.session_state.user["level"] = new_level
    st.session_state.user["next_level_xp"] = 100 * (new_level + 1) ** 2

# App Header
st.title("🏆 My Habit Quest: Track & Level Up")
st.markdown(f"### *{st.session_state.daily_theme}*")

# Create tabs for different sections of the app
tabs = st.tabs(["📋 Track Habits", "📊 Analytics", "🏆 Achievements", "⚙️ Settings"])

# Tab 1: Track Habits
with tabs[0]:
    # User profile card
    user_col1, user_col2 = st.columns([1, 2])
    
    with user_col1:
        st.markdown("### Your Quest Progress")
        st.markdown(f"**Level {st.session_state.user['level']}**")
        
        # Calculate XP progress to next level
        current_xp = st.session_state.user["total_xp"]
        next_level_xp = st.session_state.user["next_level_xp"]
        previous_level_xp = 100 * (st.session_state.user["level"]) ** 2
        level_progress = 0 if next_level_xp == previous_level_xp else (current_xp - previous_level_xp) / (next_level_xp - previous_level_xp) * 100
        
        st.markdown(f"XP: {current_xp} / {next_level_xp}")
        
        # Progress bar for level
        st.markdown(
            f"""
            <div class="level-progress">
                <div class="level-bar" style="width: {level_progress}%; background-color: #1E88E5;">
                    {int(level_progress)}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with user_col2:
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate completion rate for today
        total_habits = len(st.session_state.habits)
        completed_today = sum(1 for habit in st.session_state.habits.values() 
                             if today in habit["completions"] and habit["completions"][today])
        
        if total_habits > 0:
            completion_rate = (completed_today / total_habits) * 100
        else:
            completion_rate = 0
        
        st.markdown("### Today's Progress")
        st.progress(completion_rate / 100)
        st.markdown(f"{completed_today} out of {total_habits} habits completed ({int(completion_rate)}%)")
    
    st.markdown("---")
    
    # Group habits by category
    habits_by_category = {}
    for habit_id, habit in st.session_state.habits.items():
        category = habit["category"]
        if category not in habits_by_category:
            habits_by_category[category] = []
        habits_by_category[category].append((habit_id, habit))
    
    # Current date for tracking
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Display habits by category with completion checkboxes
    for category, habits in habits_by_category.items():
        st.markdown(f"### {category}")
        
        # Use columns to display habits in a grid
        cols = st.columns(3)
        
        for i, (habit_id, habit) in enumerate(habits):
            with cols[i % 3]:
                # Check if habit has been completed today
                completed_today = today in habit["completions"] and habit["completions"][today]
                
                # Create a container for each habit
                with st.container():
                    st.markdown(f"""
                    <div class="streak-card">
                        <div class="category-header">{habit["name"]}</div>
                    """, unsafe_allow_html=True)
                    
                    # Display streak and level information
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Current streak:** {habit['streak']} days")
                        st.markdown(f"**Longest streak:** {habit['longest_streak']} days")
                    
                    with col2:
                        st.markdown(f"**Level:** {habit['level']}")
                        st.markdown(f"**XP:** {habit['xp']}")
                    
                    # Checkbox for completing the habit today
                    if st.checkbox("Complete for today", value=completed_today, key=f"check_{habit_id}"):
                        if not completed_today:
                            # Mark habit as completed for today
                            if habit["completions"].get(today, False) != True:
                                st.session_state.habits[habit_id]["completions"][today] = True
                                
                                # Award XP based on streak
                                streak_xp = min(20, 5 + (habit["streak"] * 2))
                                award_xp(habit_id, streak_xp)
                                
                                # Show notification
                                st.success(f"🎯 {habit['name']} completed for today! +{streak_xp} XP")
                                
                                # Update streaks
                                update_streaks()
                                
                                # Check for achievements
                                check_milestone_achievements()
                    else:
                        if completed_today:
                            # Unmark habit as completed
                            st.session_state.habits[habit_id]["completions"][today] = False
                            update_streaks()  # Recalculate streaks
                    
                    st.markdown("</div>", unsafe_allow_html=True)
    
    # Button to save progress
    if st.button("💾 Save Progress"):
        save_data()
        st.success("Progress saved successfully!")

# Tab 2: Analytics
with tabs[1]:
    st.markdown("## Habit Analytics")
    
    # Sidebar for selecting analytics options
    analytics_type = st.selectbox(
        "Choose Analytics View:",
        ["Habit Heatmap", "Streak Progress", "Category Performance", "Habit Completion Rates"]
    )
    
    if analytics_type == "Habit Heatmap":
        st.markdown("### Habit Completion Heatmap")
        st.markdown("This heatmap shows your habit completion patterns over time.")
        
        # Get all unique dates from all habits
        all_dates = set()
        for habit in st.session_state.habits.values():
            all_dates.update(habit["completions"].keys())
        
        # Sort dates
        date_list = sorted(list(all_dates))
        
        # If there's no data yet, show a message
        if not date_list:
            st.info("Complete some habits to see your heatmap!")
        else:
            # Create a dataframe for the heatmap
            habits_list = list(st.session_state.habits.keys())
            habit_names = [st.session_state.habits[h]["name"] for h in habits_list]
            
            # Create empty dataframe
            heatmap_data = []
            
            for date in date_list:
                row = {'Date': date}
                for habit_id in habits_list:
                    habit_name = st.session_state.habits[habit_id]["name"]
                    completed = st.session_state.habits[habit_id]["completions"].get(date, False)
                    row[habit_name] = 1 if completed else 0
                heatmap_data.append(row)
            
            heatmap_df = pd.DataFrame(heatmap_data)
            
            # Set Date as index
            heatmap_df.set_index('Date', inplace=True)
            
            # Plot the heatmap
            fig, ax = plt.subplots(figsize=(12, len(habit_names) * 0.4 + 2))
            
            # Custom colormap (white to blue)
            cmap = LinearSegmentedColormap.from_list('custom_cmap', ['#f5f5f5', '#1E88E5'])
            
            ax = plt.pcolormesh(heatmap_df.T, cmap=cmap, edgecolors='w', linewidth=0.5)
            plt.yticks(np.arange(0.5, len(habit_names)), habit_names)
            plt.xticks(np.arange(0.5, len(date_list)), date_list, rotation=90)
            
            plt.colorbar(ax, label='Completed')
            plt.tight_layout()
            
            st.pyplot(fig)
    
    elif analytics_type == "Streak Progress":
        st.markdown("### Streak Progress")
        st.markdown("Track how your habit streaks have grown over time.")
        
        # Create a bar chart of current streaks
        habit_names = [habit["name"] for habit in st.session_state.habits.values()]
        current_streaks = [habit["streak"] for habit in st.session_state.habits.values()]
        longest_streaks = [habit["longest_streak"] for habit in st.session_state.habits.values()]
        
        # Create a DataFrame for the chart
        streak_df = pd.DataFrame({
            'Habit': habit_names,
            'Current Streak': current_streaks,
            'Longest Streak': longest_streaks
        })
        
        # Sort by longest streak
        streak_df = streak_df.sort_values('Longest Streak', ascending=False)
        
        # Plot with Plotly for interactivity
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=streak_df['Habit'],
            x=streak_df['Current Streak'],
            name='Current Streak',
            orientation='h',
            marker=dict(color='rgba(30, 136, 229, 0.8)')
        ))
        
        fig.add_trace(go.Bar(
            y=streak_df['Habit'],
            x=streak_df['Longest Streak'],
            name='Longest Streak',
            orientation='h',
            marker=dict(color='rgba(255, 193, 7, 0.8)')
        ))
        
        fig.update_layout(
            title='Current vs. Longest Streaks',
            barmode='group',
            height=max(400, len(habit_names) * 40),
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title='Days',
            hovermode='closest'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif analytics_type == "Category Performance":
        st.markdown("### Category Performance")
        st.markdown("See how you're doing across different habit categories.")
        
        # Create a pie chart of completion rates by category
        categories = {}
        for habit in st.session_state.habits.values():
            category = habit["category"]
            if category not in categories:
                categories[category] = {"completed": 0, "total": 0}
            
            for completed in habit["completions"].values():
                categories[category]["total"] += 1
                if completed:
                    categories[category]["completed"] += 1
        
        # Calculate completion percentages
        category_names = []
        completion_rates = []
        
        for category, data in categories.items():
            category_names.append(category)
            if data["total"] > 0:
                completion_rates.append((data["completed"] / data["total"]) * 100)
            else:
                completion_rates.append(0)
        
        # Create the pie chart
        if completion_rates:
            fig = px.pie(
                names=category_names,
                values=completion_rates,
                title="Habit Completion Rates by Category",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                uniformtext_minsize=12,
                uniformtext_mode='hide',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete some habits to see category performance!")
    
    elif analytics_type == "Habit Completion Rates":
        st.markdown("### Habit Completion Rates")
        st.markdown("See your most and least completed habits.")
        
        # Calculate completion rates for each habit
        completion_data = []
        
        for habit_id, habit in st.session_state.habits.items():
            total_days = len(habit["completions"])
            if total_days > 0:
                completed_days = sum(1 for completed in habit["completions"].values() if completed)
                completion_rate = (completed_days / total_days) * 100
            else:
                completed_days = 0
                completion_rate = 0
            
            completion_data.append({
                "Habit": habit["name"],
                "Category": habit["category"],
                "Completion Rate": completion_rate,
                "Days Completed": completed_days,
                "Total Days": total_days
            })
        
        # Convert to DataFrame and sort
        completion_df = pd.DataFrame(completion_data)
        completion_df = completion_df.sort_values("Completion Rate", ascending=False)
        
        # Create the bar chart
        if not completion_df.empty and completion_df["Total Days"].sum() > 0:
            fig = px.bar(
                completion_df,
                x="Habit",
                y="Completion Rate",
                color="Category",
                text="Completion Rate",
                hover_data=["Days Completed", "Total Days"],
                title="Habit Completion Rates",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                uniformtext_minsize=8,
                uniformtext_mode='hide',
                xaxis_tickangle=-45,
                yaxis_title="Completion Rate (%)",
                margin=dict(l=20, r=20, t=40, b=60)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete some habits to see completion rates!")

# Tab 3: Achievements
with tabs[2]:
    st.markdown("## Achievements & Rewards")
    
    # Display streak achievements
    st.markdown("### Streak Achievements")
    
    streak_achievements = st.session_state.achievements["streaks"]
    
    for achievement_id, achievement in streak_achievements.items():
        # Check if any habits have earned this achievement
        earned_habits = achievement["earned"]
        
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Show achievement icon (locked or unlocked)
            if earned_habits:
                st.markdown("🏆")
            else:
                st.markdown("🔒")
        
        with col2:
            # Show achievement details
            st.markdown(f"**{achievement['name']}**")
            st.markdown(f"{achievement['description']}")
            
            # Show which habits have earned this achievement
            if earned_habits:
                habit_names = []
                for habit_id in earned_habits:
                    if habit_id in st.session_state.habits:
                        habit_names.append(st.session_state.habits[habit_id]["name"])
                
                if habit_names:
                    st.markdown(f"*Earned for:* {', '.join(habit_names)}")
        
        with col3:
            # Show XP reward
            st.markdown(f"+{achievement['xp']} XP")
    
    # Display milestone achievements
    st.markdown("### Milestone Achievements")
    
    milestone_achievements = st.session_state.achievements["milestones"]
    
    for achievement_id, achievement in milestone_achievements.items():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Show achievement icon (locked or unlocked)
            if achievement["earned"]:
                st.markdown("🏆")
            else:
                st.markdown("🔒")
        
        with col2:
            # Show achievement details
            st.markdown(f"**{achievement['name']}**")
            st.markdown(f"{achievement['description']}")
        
        with col3:
            # Show XP reward
            st.markdown(f"+{achievement['xp']} XP")

# Tab 4: Settings
with tabs[3]:
    st.markdown("## Settings")
    
    # Add new habit
    st.markdown("### Add New Habit")
    
    # Create columns for form layout
    col1, col2 = st.columns(2)
    
    with col1:
        new_habit_name = st.text_input("Habit Name")
    
    with col2:
        # Get unique categories from existing habits
        existing_categories = sorted(set(habit["category"] for habit in st.session_state.habits.values()))
        
        # Allow selecting existing category or creating a new one
        category_option = st.radio("Category", ["Choose Existing", "Create New"])
        
        if category_option == "Choose Existing" and existing_categories:
            new_habit_category = st.selectbox("Select Category", existing_categories)
        else:
            new_habit_category = st.text_input("New Category Name")
    
    # Button to add the habit
    if st.button("Add Habit"):
        if new_habit_name and new_habit_category:
            # Create a unique ID for the habit
            habit_id = f"{new_habit_category}_{new_habit_name}".replace(" ", "_").lower()
            
            # Check if habit already exists
            if habit_id in st.session_state.habits:
                st.error("This habit already exists!")
            else:
                # Add the new habit
                st.session_state.habits[habit_id] = {
                    "name": new_habit_name,
                    "category": new_habit_category,
                    "streak": 0,
                    "longest_streak": 0,
                    "completions": {},
                    "xp": 0,
                    "level": 1,
                    "created_date": datetime.now().strftime("%Y-%m-%d")
                }
                
                st.success(f"Habit '{new_habit_name}' added successfully!")
                save_data()
        else:
            st.warning("Please enter both a habit name and category.")
    
    st.markdown("---")
    
    # Delete habit
    st.markdown("### Delete Habit")
    
    # Create a selectbox with all habits
    habit_options = [(habit_id, f"{habit['name']} ({habit['category']})") 
                     for habit_id, habit in st.session_state.habits.items()]
    habit_display = [option[1] for option in habit_options]
    
    if habit_options:
        selected_index = st.selectbox("Select Habit to Delete", range(len(habit_options)), format_func=lambda x: habit_display[x])
        selected_habit_id = habit_options[selected_index][0]
        
        # Button to delete the habit
        if st.button("Delete Habit"):
            habit_name = st.session_state.habits[selected_habit_id]["name"]
            if st.session_state.habits.pop(selected_habit_id, None):
                st.success(f"Habit '{habit_name}' deleted successfully!")
                save_data()
    else:
        st.info("No habits to delete.")
    
    st.markdown("---")
    
    # Reset all data
    st.markdown("### Reset Data")
    st.warning("This will delete all habits, achievements, and progress. This cannot be undone.")
    
    # Two-step confirmation to prevent accidental reset
    if st.button("Reset All Data"):
        st.session_state.confirm_reset = True
    
    if st.session_state.get("confirm_reset", False):
        if st.button("Yes, I'm sure. Reset everything"):
            # Reset all session state data
            if 'habits' in st.session_state:
                del st.session_state.habits
            if 'achievements' in st.session_state:
                del st.session_state.achievements
            if 'user' in st.session_state:
                del st.session_state.user
            if 'confirm_reset' in st.session_state:
                del st.session_state.confirm_reset
            
            # Delete save file if it exists
            if os.path.exists('habit_data.json'):
                os.remove('habit_data.json')
            
            st.success("All data has been reset. Refresh the page to start fresh.")
    
    st.markdown("---")
    
    # Export data
    st.markdown("### Export Data")
    
    if st.button("Export Data (JSON)"):
        # Create JSON data
        data = {
            "habits": st.session_state.habits,
            "achievements": st.session_state.achievements,
            "user": st.session_state.user
        }
        
        # Convert to JSON string
        json_data = json.dumps(data, indent=4, default=str)
        
        # Create download link
        st.download_button(
            label="Download JSON",
            data=json_data,
            file_name="habit_tracker_data.json",
            mime="application/json"
        )

# Main app loop
if __name__ == "__main__":
    # This will execute when the script is run directly
    pass