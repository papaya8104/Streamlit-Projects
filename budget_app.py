import streamlit as st
import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from functools import lru_cache

# Set page config
st.set_page_config(
    page_title="Personal Budget Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-top: 1rem;
    }
    .achievement {
        background-color: #E5E7EB;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .achievement-completed {
        background-color: #D1FAE5;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .reward {
        color: #059669;
        font-weight: bold;
    }
    .card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for account balances
if 'account_balances' not in st.session_state:
    st.session_state.account_balances = {
        "Westpac Choice": 536.29,
        "ANZ Access": 1391.45,
        "Westpac Offset": 220144.00
    }

@lru_cache(maxsize=2)
def load_csv_files(folder_path):
    """Load all CSV files from the specified folder matching the naming pattern.
    Results are cached to improve performance."""
    all_data = []
    
    # Get list of CSV files with pattern YYYY-MM
    csv_files = glob.glob(os.path.join(folder_path, "????-??.csv"))
    
    for file in csv_files:
        try:
            # Extract month and year from filename
            filename = os.path.basename(file)
            year_month = filename.split('.')[0]  # Gets "2025-05" part
            
            # Read the CSV file
            df = pd.read_csv(file)
            
            # Check if required columns exist
            required_cols = ['Date', 'Account', 'Category', 'Subcategory', 'Description', 'Amount']
            if not all(col in df.columns for col in required_cols):
                st.warning(f"File {filename} is missing required columns. Skipping.")
                continue
                
            # Convert Date to datetime - handle Australian date format (DD/MM/YYYY)
            df['Date'] = pd.to_datetime(df['Date'], format="%d/%m/%Y", errors='coerce')
            
            # Add month info for filtering
            df['Month'] = year_month
            df['MonthName'] = df['Date'].dt.strftime('%b %Y')
            
            # Append to the list
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Error loading file {file}: {e}")
    
    # Combine all data
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        return combined_data
    else:
        return pd.DataFrame()

def get_account_balance(account, data):
    """Calculate current balance for a given account based on transactions."""
    if account in st.session_state.account_balances:
        starting_balance = st.session_state.account_balances[account]
        
        # Filter data for this account
        account_data = data[data['Account'] == account]
        
        # Sum all transactions
        total_amount = account_data['Amount'].sum()
        
        return starting_balance + total_amount
    return 0

def get_monthly_delta(account, data):
    """Calculate the monthly delta for an account to display correctly colored metrics."""
    if not data.empty and account in data['Account'].unique():
        latest_month = data['Month'].max()
        month_data = data[(data['Month'] == latest_month) & (data['Account'] == account)]
        return month_data['Amount'].sum()
    return 0

def check_achievements(data, month=None):
    """Check which achievements have been met for the given month."""
    completed = []
    
    # Define fixed achievements
    achievements = [
        {"name": "Miscellaneous Master", "category": "Miscellaneous", "target": 200, "icon": "🏆"},
        {"name": "Dining Deal", "category": "Eating Out", "target": 200, "icon": "🍽️"}
    ]
    
    # Filter by month if specified
    if month:
        month_data = data[data['Month'] == month]
    else:
        # Use the most recent month
        if not data.empty:
            latest_month = data['Month'].max()
            month_data = data[data['Month'] == latest_month]
        else:
            month_data = data
    
    # Check each achievement
    for achievement in achievements:
        category = achievement["category"]
        target = achievement["target"]
        
        # For expense categories, we check if spending is below target
        category_data = month_data[month_data['Category'] == category]
        total_spent = abs(category_data[category_data['Amount'] < 0]['Amount'].sum())
        if total_spent < target:
            completed.append(achievement)
    
    return completed

def main():
    st.markdown('<div class="main-header">Personal Budget Dashboard 💰</div>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    st.sidebar.title("Configuration")
    
    # Input for CSV folder path
    folder_path = st.sidebar.text_input("CSV Files Folder Path", "C:\\Users\\jetsn\\OneDrive\\Desktop\\Budget")
    
    # Add refresh button to reload data
    if st.sidebar.button("🔄 Refresh Data"):
        # Clear the cache to force reloading of data
        load_csv_files.cache_clear()
        st.experimental_rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Recent Activity Settings")
    end_date = st.sidebar.date_input(
        "Select End Date", 
        value=datetime.now().date(),
        key="recent_activity_end_date"
    )
    
    # Load data
    data = load_csv_files(folder_path)
    
    if data.empty:
        st.warning(f"No valid CSV files found in {folder_path}. Please check the path and file format.")
        st.info("CSV files should be named like '2025-05.csv' and contain columns: Date, Account, Category, Subcategory, Description, and Amount")
        return
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Transactions", "Achievements", "Accounts", "Recent Activity"])
    
    # Tab 1: Dashboard
    with tab1:
        # Date filters
        st.markdown('<div class="section-header">Filter Data</div>', unsafe_allow_html=True)
        
        # Get unique months
        months = sorted(data['Month'].unique())
        
        # Month selection
        selected_month = st.selectbox("Select Month", options=["All"] + list(months))
        
        # Filter data based on selection
        if selected_month != "All":
            filtered_data = data[data['Month'] == selected_month]
        else:
            filtered_data = data
        
        # Show summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_income = filtered_data[filtered_data['Amount'] > 0]['Amount'].sum()
            st.metric("Total Income", f"${total_income:,.2f}")
        
        with col2:
            total_expenses = filtered_data[filtered_data['Amount'] < 0]['Amount'].sum()
            st.metric("Total Expenses", f"${abs(total_expenses):,.2f}")
        
        with col3:
            net = total_income + total_expenses  # total_expenses is negative
            st.metric("Net", f"${net:,.2f}", delta=f"${net:,.2f}")
        
        # Category visualization
        st.markdown('<div class="section-header">Spending by Category</div>', unsafe_allow_html=True)
        
        # Group by category and calculate total
        category_totals = filtered_data[filtered_data['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        
        # Create bar chart for categories
        fig_categories = px.bar(
            x=category_totals.index,
            y=category_totals.values,
            labels={'x': 'Category', 'y': 'Total Spent ($)'},
            title='Spending by Category',
            color=category_totals.values,
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_categories, use_container_width=True)
        
        with st.expander("Subcategory Breakdown",expanded=False):
            # Add subcategory drill-down
            if not category_totals.empty:
                
                # Select a category to drill down into
                category_options = sorted(filtered_data['Category'].unique())
                selected_drill_category = st.selectbox("Select Category to Drill Down", options=category_options)
                
                # Filter data for the selected category
                category_data = filtered_data[filtered_data['Category'] == selected_drill_category]
                
                # Get subcategory totals
                subcategory_totals = category_data[category_data['Amount'] < 0].groupby('Subcategory')['Amount'].sum().abs()
                
                # Create a figure with both the category total and subcategory breakdown
                fig_subcategories = px.bar(
                    x=subcategory_totals.index,
                    y=subcategory_totals.values,
                    labels={'x': 'Subcategory', 'y': f'Total Spent in {selected_drill_category} ($)'},
                    title=f'Spending by Subcategory within {selected_drill_category}',
                    color=subcategory_totals.values,
                    color_continuous_scale='Viridis'
                )
                
                # Add a line for the category total
                category_total = abs(category_data[category_data['Amount'] < 0]['Amount'].sum())
                
                # Display the charts
                st.plotly_chart(fig_subcategories, use_container_width=True)
                
                # Show the total spent in this category
                st.metric(f"Total Spent in {selected_drill_category}", f"${category_total:,.2f}")
        
        # Time series visualization
        st.markdown('<div class="section-header">Spending Over Time</div>', unsafe_allow_html=True)
        
        # Category selection for time series
        categories = ['All'] + sorted(data['Category'].unique().tolist())
        selected_category = st.selectbox('Select Category for Time Series', categories)
        
        # Prepare time series data
        if selected_category == 'All':
            category_filter = data
        else:
            category_filter = data[data['Category'] == selected_category]
        
        # Group by date and make it cumulative
        daily_totals = category_filter.groupby([pd.Grouper(key='Date', freq='D')])['Amount'].sum()
        daily_totals = daily_totals.cumsum()  # Make it cumulative
        
        if not daily_totals.empty:
            # Create time series chart
            fig_time = px.line(
                x=daily_totals.index,
                y=daily_totals.values,
                labels={'x': 'Date', 'y': 'Amount ($)'},
                title=f'{"All Categories" if selected_category == "All" else selected_category} - Cumulative Totals'
            )
            
            # Format x-axis to show only dates without times
            fig_time.update_xaxes(
                tickformat="%Y-%m-%d",
                dtick="D1"  # Daily ticks
            )
            
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info(f"No data available for {selected_category} in the selected time period.")
    
    # Tab 2: Transactions
    with tab2:
        st.markdown('<div class="section-header">Transaction Details</div>', unsafe_allow_html=True)
        
        # Filters for transactions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            month_filter = st.selectbox("Month", options=["All"] + list(months), key="trans_month")
        
        with col2:
            categories = ["All"] + sorted(data['Category'].unique().tolist())
            category_filter = st.selectbox("Category", options=categories, key="trans_cat")
        
        with col3:
            accounts = ["All"] + sorted(data['Account'].unique().tolist())
            account_filter = st.selectbox("Account", options=accounts, key="trans_acc")
        
        # Apply filters
        filtered_trans = data.copy()
        
        if month_filter != "All":
            filtered_trans = filtered_trans[filtered_trans['Month'] == month_filter]
        
        if category_filter != "All":
            filtered_trans = filtered_trans[filtered_trans['Category'] == category_filter]
        
        if account_filter != "All":
            filtered_trans = filtered_trans[filtered_trans['Account'] == account_filter]
        
        # Sort and display transactions
        filtered_trans = filtered_trans.sort_values('Date', ascending=False)
        
        # Format the amount with colors
        def color_amount(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}'
        
        # Custom formatter for negative amounts
        def format_amount(val):
            if val < 0:
                return f'-${abs(val):,.2f}'
            else:
                return f'${val:,.2f}'
        
        # Apply formatting and show dataframe
        styled_df = filtered_trans[['Date', 'Account', 'Category', 'Subcategory', 'Description', 'Amount']].style.applymap(
            color_amount, subset=['Amount']
        ).format({
            'Amount': format_amount, 
            'Date': '{:%Y-%m-%d}'
        })
        
        st.dataframe(styled_df, use_container_width=True)
    
        def check_achievements(data, month=None):
            """Check which achievements have been met for the given month."""
            all_achievements = []
            
            # Define fixed achievements
            achievements = [
                {"name": "Dining Deal", "category": "Eating Out", "target": 200, "icon": "🍽️"},
                {"name": "Miscellaneous Master", "category": "Miscellaneous", "target": 200, "icon": "🏆"}
            ]
            
            # Filter by month if specified
            if month and month != "All":
                month_data = data[data['Month'] == month]
            else:
                # Use the most recent month
                if not data.empty:
                    latest_month = data['Month'].max()
                    month_data = data[data['Month'] == latest_month]
                else:
                    month_data = data
            
            # Check each achievement
            for achievement in achievements:
                category = achievement["category"]
                target = achievement["target"]
                
                # For expense categories, we check if spending is below target
                category_data = month_data[month_data['Category'] == category]
                total_spent = abs(category_data[category_data['Amount'] < 0]['Amount'].sum())
                
                # Calculate progress percentage (inverted for expense targets - less is better)
                if target > 0:
                    progress = min(100, (total_spent / target) * 100)
                    is_completed = total_spent < target
                else:
                    progress = 0
                    is_completed = False
                
                # Create a copy with progress information
                achievement_with_progress = achievement.copy()
                achievement_with_progress["progress"] = progress
                achievement_with_progress["spent"] = total_spent
                achievement_with_progress["completed"] = is_completed
                
                # Add to appropriate list
                all_achievements.append(achievement_with_progress)
            
            return all_achievements

        # Replace the Achievements tab section with this code:
        # Tab 3: Achievements
        with tab3:
            st.markdown('<div class="section-header">Monthly Achievements</div>', unsafe_allow_html=True)
            
            # Month selection for achievements
            achievement_months = ["Current Month"] + sorted(data['Month'].unique())
            selected_achievement_month = st.selectbox("Select Month", options=achievement_months, key="achievement_month")
            
            # Convert "Current Month" to the latest month in the data
            if selected_achievement_month == "Current Month":
                if not data.empty:
                    selected_achievement_month = data['Month'].max()
            
            # Get achievements with progress
            all_achievements = check_achievements(data, selected_achievement_month)
            
            # Display achievement progress
            st.markdown('<div class="section-header">Spending Goals Progress</div>', unsafe_allow_html=True)
            
            # Display all achievements with progress bars
            for achievement in all_achievements:
                # Create achievement card with conditional styling
                card_class = "achievement-completed" if achievement["completed"] else "achievement"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <h3>{achievement["icon"]} {achievement["name"]}</h3>
                    <p>Target: Keep {achievement["category"]} spending under ${achievement["target"]}</p>
                    <p>Current: ${achievement["spent"]:.2f} ({100 - achievement["progress"]:.1f}% to goal)</p>
                    <div style="background-color: #E5E7EB; border-radius: 5px; height: 20px; width: 100%;">
                        <div style="background-color: {'#10B981' if achievement["completed"] else '#60A5FA'}; 
                                    width: {100 - achievement["progress"]}%; 
                                    height: 20px; 
                                    border-radius: 5px;">
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Tab 4: Accounts
    with tab4:
        st.markdown('<div class="section-header">Account Balances</div>', unsafe_allow_html=True)
        
        # Display account balances in 3 columns
        col1, col2, col3 = st.columns(3)
        
        # Map accounts to columns
        account_cols = {
            "Westpac Choice": col1,
            "ANZ Access": col2,
            "Westpac Offset": col3
        }
        
        # Display account balances with transactions factored in
        for account in st.session_state.account_balances:
            current_balance = get_account_balance(account, data)
            
            # Calculate monthly change
            month_change = get_monthly_delta(account, data)
            
            # Display in the appropriate column
            if account in account_cols:
                col = account_cols[account]
            else:
                # Fallback for any new accounts
                col = col1
            
            with col:
                # Format negative changes properly
                delta_text = f"-${abs(month_change):,.2f} this month" if month_change < 0 else f"${month_change:,.2f} this month"
                
                # For account balances, negative changes should be red (normal) and positive should be green (normal)
                st.metric(
                    label=account,
                    value=f"${current_balance:,.2f}",
                    delta=delta_text,
                    delta_color="normal"  # Normal coloring: negative is red, positive is green
                )
        
        if st.session_state.account_balances and not data.empty:
            st.markdown('<div class="section-header">Balance History</div>', unsafe_allow_html=True)
            
            # Create data for plotting account balances over time
            regular_accounts_df = pd.DataFrame()
            offset_account_df = pd.DataFrame()
            
            # Get all dates from the data
            all_dates = sorted(data['Date'].unique())
            
            if all_dates:
                # Process each account
                for account in st.session_state.account_balances:
                    # Skip empty accounts
                    if not account:
                        continue
                        
                    # Get starting balance
                    initial_balance = st.session_state.account_balances[account]
                    
                    # Create a series for this account
                    account_data = pd.DataFrame({
                        'Date': [all_dates[0] - pd.Timedelta(days=1)],  # Day before first transaction
                        'Balance': [initial_balance],
                        'Account': [account]
                    })
                    
                    # Filter transactions for this account
                    account_transactions = data[data['Account'] == account].copy()
                    
                    if not account_transactions.empty:
                        # Sort by date
                        account_transactions = account_transactions.sort_values('Date')
                        
                        # Calculate running balance
                        running_balance = initial_balance
                        daily_balances = []
                        
                        # Group by date and calculate daily balance
                        daily_sums = account_transactions.groupby('Date')['Amount'].sum()
                        
                        for date, amount in daily_sums.items():
                            running_balance += amount
                            daily_balances.append({
                                'Date': date,
                                'Balance': running_balance,
                                'Account': account
                            })
                        
                        # Add daily balances to the account data
                        if daily_balances:
                            account_data = pd.concat([
                                account_data,
                                pd.DataFrame(daily_balances)
                            ])
                    
                    # Add to appropriate dataframe based on account type
                    if account == "Westpac Offset":
                        offset_account_df = pd.concat([offset_account_df, account_data])
                    else:
                        regular_accounts_df = pd.concat([regular_accounts_df, account_data])
                
                # Create figure
                fig = go.Figure()
                
                # Add traces for regular accounts
                if not regular_accounts_df.empty:
                    for account in regular_accounts_df['Account'].unique():
                        account_data = regular_accounts_df[regular_accounts_df['Account'] == account]
                        fig.add_trace(go.Scatter(
                            x=account_data['Date'],
                            y=account_data['Balance'],
                            mode='lines+markers',
                            name=account,
                            hovertemplate='%{x}<br>Balance: $%{y:,.2f}'
                        ))
                
                # Add trace for Westpac Offset on secondary y-axis
                if not offset_account_df.empty:
                    fig.add_trace(go.Scatter(
                        x=offset_account_df['Date'],
                        y=offset_account_df['Balance'],
                        mode='lines+markers',
                        name="Westpac Offset",
                        yaxis="y2",
                        line=dict(color='green', width=3),
                        hovertemplate='%{x}<br>Balance: $%{y:,.2f}'
                    ))
                
                # Update layout
                fig.update_layout(
                    title='Account Balance History',
                    xaxis_title='Date',
                    yaxis=dict(
                        title=dict(text='Regular Account Balance ($)', font=dict(color='royalblue')),
                        tickfont=dict(color='royalblue'),
                        tickprefix='$',
                        tickformat=',.2f',
                        showgrid=True,
                        zeroline=False
                    ),
                    yaxis2=dict(
                        title=dict(text='Offset Account Balance ($)', font=dict(color='green')),
                        tickfont=dict(color='green'),
                        tickprefix='$',
                        tickformat=',.2f',
                        anchor='x',
                        overlaying='y',
                        side='right',
                        showgrid=False,
                        zeroline=False
                    ),
                    legend_title='Accounts',
                    hovermode='x unified'
                )

                fig.update_xaxes(
                    dtick="D1",  # Daily ticks
                    tickformat="%Y-%m-%d"  # Ensure dates appear without time
                )
                
                # Show the chart
                st.plotly_chart(fig, use_container_width=True)
                
                # Explanation of the chart
                st.info("""
                This chart shows your account balances over time:
                - Regular accounts are shown on the left y-axis
                - The Westpac Offset account is shown on the right y-axis with a different scale
                - Each point represents the running balance after all transactions for that day
                """)
            else:
                st.warning("No transaction data available. Please check your CSV files.")


    with tab5:
        st.markdown('<div class="section-header">Recent Activity (Past 7 Days)</div>', unsafe_allow_html=True)
        
        # Calculate start date (7 days before the selected end date)
        start_date = end_date - timedelta(days=7)
        
        # Convert to datetime for comparison
        start_datetime = pd.Timestamp(start_date)
        end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1)  # Include end date
        
        # Filter data for the date range
        recent_data = data[(data['Date'] >= start_datetime) & (data['Date'] < end_datetime)]
        
        # Display date range
        st.markdown(f"**Showing transactions from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}**")
        
        if recent_data.empty:
            st.info("No transactions found in the selected date range.")
        else:
            # Show summary stats for the period
            col1, col2, col3 = st.columns(3)
            
            with col1:
                period_income = recent_data[recent_data['Amount'] > 0]['Amount'].sum()
                st.metric("Period Income", f"${period_income:,.2f}")
            
            with col2:
                period_expenses = recent_data[recent_data['Amount'] < 0]['Amount'].sum()
                st.metric("Period Expenses", f"${abs(period_expenses):,.2f}")
            
            with col3:
                period_net = period_income + period_expenses
                st.metric("Period Net", f"${period_net:,.2f}", delta=f"${period_net:,.2f}")
            
            # Add filter for accounts in this view
            recent_accounts = ["All"] + sorted(recent_data['Account'].unique().tolist())
            selected_recent_account = st.selectbox(
                "Filter by Account", 
                options=recent_accounts, 
                key="recent_act_acc"
            )
            
            # Apply account filter
            if selected_recent_account != "All":
                filtered_recent = recent_data[recent_data['Account'] == selected_recent_account]
            else:
                filtered_recent = recent_data
            
            # Sort by date (newest first)
            filtered_recent = filtered_recent.sort_values('Date', ascending=False)
            
            # Create a nice visualization of daily spending
            st.markdown('<div class="section-header">Daily Activity</div>', unsafe_allow_html=True)
            
            # Group by date and transaction type (income/expense)
            daily_summary = filtered_recent.copy()
            daily_summary['Type'] = daily_summary['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
            
            # For expenses, convert to positive for better visualization
            daily_summary['Value'] = daily_summary['Amount'].apply(lambda x: x if x > 0 else abs(x))
            
            # Group by date and type
            daily_grouped = daily_summary.groupby([pd.Grouper(key='Date', freq='D'), 'Type'])['Value'].sum().reset_index()
            
            # Create a bar chart showing income and expenses by day
            fig_daily = px.bar(
                daily_grouped,
                x='Date',
                y='Value',
                color='Type',
                barmode='group',
                title='Daily Income and Expenses',
                color_discrete_map={'Income': 'green', 'Expense': 'red'},
                labels={'Value': 'Amount ($)', 'Date': 'Date', 'Type': ''}
            )
            
            # Format x-axis to show only dates
            fig_daily.update_xaxes(
                tickformat="%Y-%m-%d",
                dtick="D1"  # Daily ticks
            )
            
            # Format y-axis to show dollar amounts
            fig_daily.update_yaxes(
                tickprefix='$',
                tickformat=',.2f'
            )
            
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Show transaction details
            st.markdown('<div class="section-header">Transaction Details</div>', unsafe_allow_html=True)
            
            # Custom formatter for negative amounts
            def format_amount(val):
                if val < 0:
                    return f'-${abs(val):,.2f}'
                else:
                    return f'${val:,.2f}'
            
            # Apply formatting and show dataframe
            styled_recent_df = filtered_recent[['Date', 'Account', 'Category', 'Subcategory', 'Description', 'Amount']].style.applymap(
                color_amount, subset=['Amount']  # Reusing your existing color_amount function
            ).format({
                'Amount': format_amount, 
                'Date': '{:%Y-%m-%d}'
            })
            
            st.dataframe(styled_recent_df, use_container_width=True)
            
            # Add a quick category breakdown
            st.markdown('<div class="section-header">Category Breakdown</div>', unsafe_allow_html=True)
            
            # Only include expenses
            expense_data = filtered_recent[filtered_recent['Amount'] < 0]
            
            if not expense_data.empty:
                # Group by category
                category_expense = expense_data.groupby('Category')['Amount'].sum().abs().reset_index()
                category_expense = category_expense.sort_values('Amount', ascending=False)
                
                # Create pie chart
                fig_pie = px.pie(
                    category_expense,
                    values='Amount',
                    names='Category',
                    title='Expense Distribution by Category',
                    hole=0.4
                )
                
                # Format hover information
                fig_pie.update_traces(
                    textinfo='percent+label',
                    hovertemplate='%{label}<br>$%{value:.2f}<br>%{percent}'
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expense transactions to show in the category breakdown.")

if __name__ == "__main__":
    main()
