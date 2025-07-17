import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk  # For Treeview for better table display
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime, timedelta
import numpy as np  # For statistical calculations like mode

# --- Custom Color Theme ---
COLOR_PRIMARY = "#2C3E50"  # Dark blue
COLOR_SECONDARY = "#3498DB"  # Blue
COLOR_DARK_BACKGROUND = "#000000"  # Black background
COLOR_LIGHT_TEXT = "#FFFFFF"
COLOR_WHITE = "#FFFFFF"
COLOR_SUCCESS = "#2ECC71"  # Green
COLOR_WARNING = "#F1C40F"  # Yellow
COLOR_DANGER = "#E74C3C"  # Red
COLOR_INFO = "#3498DB"  # Blue

# --- Font Settings ---
FONT_HEADER = ("Arial", 16, "bold")
FONT_NORMAL = ("Arial", 11)
FONT_BUTTON = ("Arial", 11, "bold")


class DataManager:
    """Manages all sales data operations, including loading, saving, and querying."""
    def __init__(self, data_file="sales_data.csv"):
        self.data_file = data_file
        self.sales_data = self._load_data()

    def _load_data(self):
        """Loads sales data from the specified CSV file. Returns empty DataFrame if file not found or error."""
        if os.path.exists(self.data_file):
            try:
                df = pd.read_csv(self.data_file, parse_dates=['Date'])
                df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                df['Total'] = pd.to_numeric(df['Total'], errors='coerce')
                df.dropna(subset=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'], inplace=True)
                return df
            except Exception as e:
                messagebox.showerror("Data Load Error", f"Failed to load data from {self.data_file}: {e}")
                return pd.DataFrame(columns=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'])
        else:
            return pd.DataFrame(columns=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'])

    def add_data(self, new_df):
        """Adds new DataFrame records to the existing sales data and saves."""
        required_cols = ['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total']
        if not all(col in new_df.columns for col in required_cols):
            messagebox.showerror("Import Error", "Imported file missing one or more required columns.")
            return False
        try:
            new_df['Date'] = pd.to_datetime(new_df['Date'])
            new_df['Quantity'] = pd.to_numeric(new_df['Quantity'], errors='coerce')
            new_df['UnitPrice'] = pd.to_numeric(new_df['UnitPrice'], errors='coerce')
            new_df['Total'] = pd.to_numeric(new_df['Total'], errors='coerce')
            new_df.dropna(subset=['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total'], inplace=True)
        except Exception as e:
            messagebox.showerror("Data Conversion Error", f"Error converting data types during import: {e}")
            return False
        if new_df.empty:
            messagebox.showwarning("No Valid Data", "No valid records to add after processing.")
            return False
        self.sales_data = pd.concat([self.sales_data, new_df], ignore_index=True)
        self._save_data()
        return True

    def _save_data(self):
        """Saves the current sales data DataFrame to the CSV file."""
        try:
            self.sales_data.to_csv(self.data_file, index=False)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data to {self.data_file}: {e}")

    def get_branches(self):
        """Returns a sorted list of unique branch names."""
        return sorted(self.sales_data['Branch'].unique().tolist()) if not self.sales_data.empty else []

    def get_products(self):
        """Returns a sorted list of unique product names."""
        return sorted(self.sales_data['Product'].unique().tolist()) if not self.sales_data.empty else []

    def get_years(self):
        """Returns a sorted list of unique years present in the data."""
        if not self.sales_data.empty and 'Date' in self.sales_data.columns:
            return sorted(self.sales_data['Date'].dt.year.unique().tolist())
        return [datetime.now().year]

    def get_monthly_sales(self, branch=None, year=None, month=None):
        """Filters sales data by branch, year, and month, then aggregates total sales per product."""
        df = self.sales_data.copy()
        if df.empty:
            return pd.DataFrame(columns=['Product', 'Quantity', 'UnitPrice', 'Total'])
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        if year:
            df = df[df['Date'].dt.year == year]
        if month:
            df = df[df['Date'].dt.month == month]
        if df.empty:
            return pd.DataFrame(columns=['Product', 'Quantity', 'UnitPrice', 'Total'])
        return df.groupby('Product').agg(
            Quantity=('Quantity', 'sum'),
            UnitPrice=('UnitPrice', 'mean'),
            Total=('Total', 'sum')
        ).reset_index()

    def get_product_price_history(self, product_name):
        """Retrieves historical unit prices for a specific product."""
        if self.sales_data.empty:
            return pd.DataFrame(columns=['Date', 'UnitPrice'])
        return self.sales_data[self.sales_data['Product'] == product_name][['Date', 'UnitPrice']].drop_duplicates().sort_values(by='Date')

    def get_weekly_sales(self, start_date, end_date, branch=None):
        """Calculates daily sales totals for a specified week and branch."""
        if self.sales_data.empty:
            return pd.DataFrame({'DayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 'Total': [0] * 7})
        df = self.sales_data[(self.sales_data['Date'] >= start_date) & (self.sales_data['Date'] <= end_date)].copy()
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        if df.empty:
            return pd.DataFrame({'DayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 'Total': [0] * 7})
        df['DayOfWeek'] = df['Date'].dt.day_name()
        return df.groupby('DayOfWeek')['Total'].sum().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], fill_value=0).reset_index()

    def get_product_preferences(self, date_range=None, category=None, branch=None):
        """Analyzes product popularity based on units sold and revenue within filters."""
        df = self.sales_data.copy()
        if df.empty:
            return pd.DataFrame(columns=['Product', 'UnitsSold', 'Revenue'])
        if date_range:
            start, end = date_range
            df = df[(df['Date'] >= start) & (df['Date'] <= end)]
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        if df.empty:
            return pd.DataFrame(columns=['Product', 'UnitsSold', 'Revenue'])
        return df.groupby('Product').agg(
            UnitsSold=('Quantity', 'sum'),
            Revenue=('Total', 'sum')
        ).sort_values(by='UnitsSold', ascending=False).reset_index()

    def get_sales_distribution(self, date_range=None, branch=None, category=None):
        """Returns a Series of total sales amounts per transaction for distribution analysis."""
        df = self.sales_data.copy()
        if df.empty:
            return pd.Series(dtype='float64')
        if date_range:
            start, end = date_range
            df = df[(df['Date'] >= start) & (df['Date'] <= end)]
        if branch and branch != "All Branches":
            df = df[df['Branch'] == branch]
        return df['Total']


class BasePage(tk.Toplevel):
    """Base class for all analysis and utility pages."""
    def __init__(self, master, data_manager, title="Application Page"):
        super().__init__(master)
        self.master = master
        self.data_manager = data_manager
        self.title(title)
        self.geometry("1200x800")
        self.configure(bg=COLOR_DARK_BACKGROUND)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.transient(master)
        self.grab_set()

    def on_close(self):
        """Handles closing the page, returning focus to the dashboard."""
        self.destroy()
        self.master.deiconify()
        self.master.lift()


class LoginPage(tk.Toplevel):
    """Handles user authentication."""
    def __init__(self, master, data_manager):
        super().__init__(master)
        self.master = master
        self.data_manager = data_manager
        self.title("Login")
        self.geometry("400x300")
        self.configure(bg=COLOR_DARK_BACKGROUND)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(False, False)

        # Center the window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) / 2
        y = (self.winfo_screenheight() - self.winfo_reqheight()) / 2
        self.geometry("+%d+%d" % (x, y))

        login_frame = tk.Frame(self, bg=COLOR_DARK_BACKGROUND, padx=30, pady=20)
        login_frame.pack(expand=True)

        tk.Label(login_frame, text="Sampath Food City", font=("Arial", 16, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=(0, 20))

        tk.Label(login_frame, text="Username:", font=("Arial", 11),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(anchor="w")

        self.username_entry = tk.Entry(login_frame, width=30, font=("Arial", 10))
        self.username_entry.pack(pady=(0, 10))
        self.username_entry.focus_set()

        tk.Label(login_frame, text="Password:", font=("Arial", 11),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(anchor="w")

        self.password_entry = tk.Entry(login_frame, show="*", width=30, font=("Arial", 10))
        self.password_entry.pack(pady=(0, 15))

        self.login_button = tk.Button(login_frame, text="Login", command=self.attempt_login,
                                   font=("Arial", 11, "bold"), bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat")
        self.login_button.pack(pady=(10, 5))

        self.error_label = tk.Label(login_frame, text="", fg=COLOR_DANGER,
                                 font=("Arial", 10), bg=COLOR_DARK_BACKGROUND)
        self.error_label.pack(pady=5)

        self.valid_users = {"admin": "admin123", "analyst": "analyst123"}

        self.username_entry.bind("<Return>", lambda event: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda event: self.attempt_login())

    def attempt_login(self):
        """Checks entered credentials against hardcoded valid users."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username in self.valid_users and self.valid_users[username] == password:
            messagebox.showinfo("Login Success", f"Welcome, {username}!", parent=self)
            self.master.show_dashboard(username)
            self.destroy()
        else:
            self.error_label.config(text="Invalid credentials")
            self.password_entry.delete(0, tk.END)

    def on_close(self):
        """If user closes login window, exit the entire application."""
        self.master.destroy()


class MainApp(tk.Tk):
    """
    The main application window, managing the overall flow and pages.
    Composition: MainApp creates and holds instances of DataManager and DashboardPage.
    """
    def __init__(self):
        super().__init__()
        self.title("Sales Analysis System")
        self.geometry("1200x800")
        self.configure(bg=COLOR_DARK_BACKGROUND)
        self.withdraw()  # Hide main window initially until login is complete
        self.data_manager = DataManager()  # Composition: MainApp 'has-a' DataManager
        self.dashboard_page = None  # Will hold the dashboard instance
        self.open_analysis_windows = []
        self.show_login()

    def show_login(self):
        """Displays the login page."""
        LoginPage(self, self.data_manager)

    def show_dashboard(self, user_role):
        """
        Displays the dashboard page after successful login.
        Destroys any existing dashboard and creates a new one to refresh content.
        """
        if self.dashboard_page:
            self.dashboard_page.destroy()
        self.deiconify()  # Show the main window
        self.dashboard_page = DashboardPage(self, self.data_manager, user_role)
        self.dashboard_page.lift()  # Bring to front

    def update_all_page_dropdowns(self):
        """
        Triggers the refresh of dropdowns in all currently open analysis pages.
        Also updates the dashboard summary and button states.
        """
        self.dashboard_page.update_summary()
        self.dashboard_page.update_button_states()
        self.open_analysis_windows = [win for win in self.open_analysis_windows if win.winfo_exists()]
        for page in self.open_analysis_windows:
            if hasattr(page, 'refresh_dropdowns'):
                page.refresh_dropdowns()


class DashboardPage(tk.Frame):
    """Central navigation hub for the application with a left sidebar."""
    def __init__(self, master, data_manager, user_role="Analyst"):
        super().__init__(master, bg=COLOR_DARK_BACKGROUND)
        self.master = master
        self.data_manager = data_manager
        self.user_role = user_role
        self.pack(fill="both", expand=True)

        # Create left navigation panel
        self.create_navigation_panel()

        # Create right content area
        self.content_frame = tk.Frame(self, bg=COLOR_DARK_BACKGROUND)
        self.content_frame.pack(side=tk.RIGHT, fill="both", expand=True)

        self.create_welcome_content()

    def create_navigation_panel(self):
        """Creates the left navigation panel with buttons."""
        nav_width = 250
        nav_frame = tk.Frame(self, width=nav_width, bg=COLOR_PRIMARY)
        nav_frame.pack(side=tk.LEFT, fill="y")
        nav_frame.pack_propagate(False)

        # Logo/Header
        tk.Label(nav_frame, text="Sales\nAnalysis\nSystem", font=("Arial", 16, "bold"),
                 bg=COLOR_PRIMARY, fg=COLOR_WHITE, justify="center").pack(pady=30)

        # Navigation buttons
        self.buttons_config = [
            ("Monthly Sales", self.open_monthly_sales),
            ("Price Analysis", self.open_price_analysis),
            ("Weekly Sales", self.open_weekly_sales),
            ("Product Preference", self.open_product_preference),
            ("Sales Distribution", self.open_sales_distribution),
            ("Data Import", self.open_data_import),
            ("Data Export", self.open_data_export),
            ("Logout / Exit", self.logout_exit)
        ]
        self.action_buttons = []
        for text, command in self.buttons_config:
            btn = tk.Button(nav_frame, text=text, command=command, width=20,
                          font=("Arial", 11, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE,
                          bd=0, anchor="w", padx=20, pady=10, relief="flat")
            btn.pack(fill="x", pady=2)
            self.action_buttons.append(btn)

    def create_welcome_content(self):
        """Creates the initial welcome content in the right side."""
        self.clear_content_frame()

        # Welcome section
        welcome_frame = tk.Frame(self.content_frame, bg=COLOR_DARK_BACKGROUND, relief="solid", bd=1)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(welcome_frame, text="Sales Analysis Dashboard", font=("Arial", 20, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=30)

        tk.Label(welcome_frame, text=f"Welcome, {self.user_role.capitalize()}!",
                 font=("Arial", 16), bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack()

        # Summary section
        summary_frame = tk.Frame(self.content_frame, bg=COLOR_DARK_BACKGROUND, relief="solid", bd=1)
        summary_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.summary_label = tk.Label(summary_frame, text="", font=("Arial", 12),
                                   fg=COLOR_LIGHT_TEXT, bg=COLOR_DARK_BACKGROUND)
        self.summary_label.pack(pady=30)

        self.update_summary()
        self.update_button_states()

    def clear_content_frame(self):
        """Clears the content frame to prepare for new content."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def update_summary(self):
        """Updates the dashboard summary with current data insights."""
        if not self.data_manager.sales_data.empty:
            total_sales = self.data_manager.sales_data['Total'].sum()
            top_product_df = self.data_manager.sales_data.groupby('Product')['Total'].sum().nlargest(1)
            if not top_product_df.empty:
                top_product_name = top_product_df.index[0]
                summary_text = f"Total Sales (All Time): Rs. {total_sales:,.2f}\nTop Product: {top_product_name}"
            else:
                summary_text = "No sales data available for summary."
        else:
            summary_text = "No sales data available. Please import data using 'Data Import'."
        self.summary_label.config(text=summary_text)

    def update_button_states(self):
        """Disables/enables analysis buttons based on data availability."""
        has_data = not self.data_manager.sales_data.empty
        for text, _ in self.buttons_config:
            if text in ["Data Import", "Logout / Exit"]:
                continue
            for btn in self.action_buttons:
                if btn.cget("text") == text:
                    btn.config(state=tk.NORMAL if has_data else tk.DISABLED)
                    break

    def open_monthly_sales(self):
        self.clear_content_frame()
        MonthlySalesPage(self.content_frame, self.master.data_manager)

    def open_price_analysis(self):
        self.clear_content_frame()
        PriceAnalysisPage(self.content_frame, self.master.data_manager)

    def open_weekly_sales(self):
        self.clear_content_frame()
        WeeklySalesPage(self.content_frame, self.master.data_manager)

    def open_product_preference(self):
        self.clear_content_frame()
        ProductPreferencePage(self.content_frame, self.master.data_manager)

    def open_sales_distribution(self):
        self.clear_content_frame()
        SalesDistributionPage(self.content_frame, self.master.data_manager)

    def open_data_import(self):
        self.clear_content_frame()
        DataImportPage(self.content_frame, self.master.data_manager)

    def open_data_export(self):
        self.clear_content_frame()
        DataExportPage(self.content_frame, self.master.data_manager)

    def logout_exit(self):
        """Initiates the exit confirmation process."""
        self.master.withdraw()
        ExitConfirmationPage(self.master)


class MonthlySalesPage:
    """Displays monthly sales performance per branch, with table and bar chart."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.create_header()
        self.create_controls()
        self.create_chart_area()
        self.create_table_area()
        self.last_report_df = pd.DataFrame()
        self.refresh_dropdowns()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Monthly Sales Analysis", font=("Arial", 18, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_controls(self):
        """Creates control elements for filtering data."""
        control_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        control_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(control_frame, text="Branch:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=0, padx=5)

        self.branch_var = tk.StringVar(self.parent)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=1, padx=5)

        tk.Label(control_frame, text="Year:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=2, padx=5)

        self.year_var = tk.StringVar(self.parent)
        self.year_dropdown = tk.OptionMenu(control_frame, self.year_var, "Loading...")
        self.year_dropdown.grid(row=0, column=3, padx=5)

        tk.Label(control_frame, text="Month:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=4, padx=5)

        self.month_var = tk.StringVar(self.parent)
        self.months = [
            "All Months", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        self.month_dropdown = tk.OptionMenu(control_frame, self.month_var, *self.months)
        self.month_var.set("All Months")
        self.month_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Generate Report", command=self.generate_report,
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").grid(
                 row=0, column=6, padx=10)

        tk.Button(control_frame, text="Export PDF", command=self.export_report_pdf,
                 font=FONT_BUTTON, bg=COLOR_INFO, fg=COLOR_WHITE, relief="flat").grid(
                 row=0, column=7, padx=5)

    def create_chart_area(self):
        """Creates the area for displaying charts."""
        self.fig, self.ax = plt.subplots(figsize=(12, 5))  # Increased chart size
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=20, pady=10)

    def create_table_area(self):
        """Creates the area for displaying tabular data."""
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("Product", "Quantity", "UnitPrice", "Total"), show="headings")
        self.tree.heading("Product", text="Product")
        self.tree.heading("Quantity", text="Quantity")
        self.tree.heading("UnitPrice", text="Unit Price")
        self.tree.heading("Total", text="Total Sales")
        self.tree.column("Product", width=250, anchor="w")
        self.tree.column("Quantity", width=100, anchor="center")
        self.tree.column("UnitPrice", width=120, anchor="e")
        self.tree.column("Total", width=120, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")

    def refresh_dropdowns(self):
        """Populates or updates the branch and year dropdowns."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        years = sorted(self.data_manager.get_years(), reverse=True)

        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch,
                                                 command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        self.year_dropdown['menu'].delete(0, 'end')
        for year in years:
            self.year_dropdown['menu'].add_command(label=str(year),
                                             command=tk._setit(self.year_var, str(year)))
        if years:
            self.year_var.set(str(years[0]))
        else:
            self.year_var.set(str(datetime.now().year))
            self.year_dropdown.config(state=tk.DISABLED)

        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)
        self.year_dropdown.config(state=state)
        self.month_dropdown.config(state=state)

    def generate_report(self):
        """Generates and displays the monthly sales report based on selected filters."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to generate reports.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self._clear_treeview()
            return

        selected_branch = self.branch_var.get()
        selected_year_str = self.year_var.get()
        selected_month_name = self.month_var.get()
        selected_year = int(selected_year_str) if selected_year_str and selected_year_str != "All Years" else None
        selected_month = None
        if selected_month_name != "All Months":
            selected_month = datetime.strptime(selected_month_name, "%B").month

        report_data = self.data_manager.get_monthly_sales(selected_branch, selected_year, selected_month)
        self.last_report_df = report_data

        if report_data.empty:
            messagebox.showinfo("No Data", "No sales data found for the selected criteria.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self._clear_treeview()
            return

        self._clear_treeview()
        for index, row in report_data.iterrows():
            self.tree.insert("", "end", values=(
                row['Product'],
                f"{row['Quantity']:.0f}",
                f"Rs. {row['UnitPrice']:.2f}",
                f"Rs. {row['Total']:.2f}"
            ))

        self.ax.clear()
        self.ax.bar(report_data['Product'], report_data['Total'], color=COLOR_SECONDARY)
        self.ax.set_title(f'Total Sales per Product ({selected_month_name} {selected_year_str})')
        self.ax.set_xlabel('Product')
        self.ax.set_ylabel('Total Sales (Rs.)')
        self.ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels
        self.fig.tight_layout()
        self.canvas.draw()

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def export_report_pdf(self):
        """Exports the current report as a PDF."""
        if self.last_report_df.empty:
            messagebox.showwarning("No Data", "Generate a report first before exporting.", parent=self.parent)
            return
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save Monthly Sales Report"
            )
            if file_path:
                self.fig.savefig(file_path, bbox_inches='tight')
                messagebox.showinfo("Export Success", f"Report saved to {file_path}", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF: {e}", parent=self.parent)


class PriceAnalysisPage:
    """Analyzes price fluctuations of individual products with a line graph and historical table."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.create_header()
        self.create_controls()
        self.create_chart_area()
        self.create_stats_area()
        self.create_table_area()
        self.refresh_dropdowns()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Price Analysis", font=("Arial", 18, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_controls(self):
        """Creates control elements for filtering data."""
        control_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        control_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(control_frame, text="Select Product:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=0, padx=5)

        self.product_var = tk.StringVar(self.parent)
        self.product_dropdown = tk.OptionMenu(control_frame, self.product_var, "Loading...")
        self.product_dropdown.grid(row=0, column=1, padx=5)

        tk.Button(control_frame, text="Analyze Price", command=self.analyze_price,
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").grid(
                 row=0, column=2, padx=10)

    def create_chart_area(self):
        """Creates the area for displaying charts."""
        self.fig, self.ax = plt.subplots(figsize=(12, 5))  # Increased chart size
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=20, pady=10)

    def create_stats_area(self):
        """Creates labels for price statistics."""
        stats_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        stats_frame.pack(pady=10, fill="x", padx=20)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.avg_price_label = tk.Label(stats_frame, text="Average Price: N/A",
                                     bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.avg_price_label.grid(row=0, column=0, padx=10)

        self.max_price_label = tk.Label(stats_frame, text="Max Price: N/A",
                                     bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.max_price_label.grid(row=0, column=1, padx=10)

        self.min_price_label = tk.Label(stats_frame, text="Min Price: N/A",
                                     bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.min_price_label.grid(row=0, column=2, padx=10)

        self.current_price_label = tk.Label(stats_frame, text="Current Price: N/A",
                                       bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.current_price_label.grid(row=0, column=3, padx=10)

    def create_table_area(self):
        """Creates the area for displaying tabular data."""
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("Date", "Price"), show="headings")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Price", text="Price (Rs.)")
        self.tree.column("Date", width=150, anchor="center")
        self.tree.column("Price", width=150, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")

    def refresh_dropdowns(self):
        """Populates or updates the product dropdown."""
        products = self.data_manager.get_products()
        self.product_dropdown['menu'].delete(0, 'end')
        if products:
            for product in products:
                self.product_dropdown['menu'].add_command(label=product,
                                                    command=tk._setit(self.product_var, product))
            self.product_var.set(products[0])
            self.product_dropdown.config(state=tk.NORMAL)
        else:
            self.product_var.set("No Products Available")
            self.product_dropdown.config(state=tk.DISABLED)
        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.product_dropdown.config(state=state)

    def analyze_price(self):
        """Fetches and displays price history for the selected product."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to analyze prices.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self.update_stats(None, None, None, None)
            self._clear_treeview()
            return

        selected_product = self.product_var.get()
        if not selected_product or selected_product == "No Products Available":
            messagebox.showwarning("Selection Error", "Please select a product.", parent=self.parent)
            return

        price_history_df = self.data_manager.get_product_price_history(selected_product)
        if price_history_df.empty:
            messagebox.showinfo("No Data", f"No price history found for {selected_product}.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self.update_stats(None, None, None, None)
            self._clear_treeview()
            return

        self.ax.clear()
        self.ax.plot(price_history_df['Date'], price_history_df['UnitPrice'], marker='o', linestyle='-', color=COLOR_SECONDARY)
        self.ax.set_title(f'Price Fluctuation for {selected_product}')
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel('Unit Price (Rs.)')
        self.fig.autofmt_xdate()
        self.fig.tight_layout()
        self.canvas.draw()

        avg_price = price_history_df['UnitPrice'].mean()
        max_price = price_history_df['UnitPrice'].max()
        min_price = price_history_df['UnitPrice'].min()
        current_price = price_history_df.iloc[-1]['UnitPrice'] if not price_history_df.empty else None

        self.update_stats(avg_price, max_price, min_price, current_price)

        self._clear_treeview()
        for index, row in price_history_df.iterrows():
            self.tree.insert("", "end", values=(row['Date'].strftime('%Y-%m-%d'), f"Rs. {row['UnitPrice']:.2f}"))

    def update_stats(self, avg, max_val, min_val, current):
        """Updates the statistical labels for price analysis."""
        self.avg_price_label.config(text=f"Average Price: Rs. {avg:.2f}" if avg is not None else "Average Price: N/A")
        self.max_price_label.config(text=f"Max Price: Rs. {max_val:.2f}" if max_val is not None else "Max Price: N/A")
        self.min_price_label.config(text=f"Min Price: Rs. {min_val:.2f}" if min_val is not None else "Min Price: N/A")
        self.current_price_label.config(text=f"Current Price: Rs. {current:.2f}" if current is not None else "Current Price: N/A")

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)


class WeeklySalesPage:
    """Provides an overview of sales trends during a specific week."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.create_header()
        self.create_controls()
        self.create_chart_area()
        self.create_summary_labels()
        self.create_table_area()
        self.refresh_dropdowns()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Weekly Sales Summary", font=("Arial", 18, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_controls(self):
        """Creates control elements for filtering data."""
        control_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        control_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(control_frame, text="Start Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=0, padx=5)

        self.start_date_entry = tk.Entry(control_frame, width=15, font=FONT_NORMAL)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="End Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=2, padx=5)

        self.end_date_entry = tk.Entry(control_frame, width=15, font=FONT_NORMAL)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="Branch:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=4, padx=5)

        self.branch_var = tk.StringVar(self.parent)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Generate Summary", command=self.generate_summary,
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").grid(
                 row=0, column=6, padx=10)

    def create_chart_area(self):
        """Creates the area for displaying charts."""
        self.fig, self.ax = plt.subplots(figsize=(12, 5))  # Increased chart size
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=20, pady=10)

    def create_summary_labels(self):
        """Creates labels for weekly sales statistics."""
        self.summary_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        self.summary_frame.pack(pady=10, fill="x", padx=20)
        self.summary_frame.grid_columnconfigure((0, 1), weight=1)

        self.total_revenue_label = tk.Label(self.summary_frame, text="Total Revenue: N/A",
                                         bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.total_revenue_label.grid(row=0, column=0, padx=10)

        self.avg_daily_sales_label = tk.Label(self.summary_frame, text="Average Daily Sales: N/A",
                                          bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.avg_daily_sales_label.grid(row=0, column=1, padx=10)

    def create_table_area(self):
        """Creates the area for displaying tabular data."""
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("DayOfWeek", "TotalSales"), show="headings")
        self.tree.heading("DayOfWeek", text="Day of Week")
        self.tree.heading("TotalSales", text="Total Sales (Rs.)")
        self.tree.column("DayOfWeek", width=150, anchor="center")
        self.tree.column("TotalSales", width=150, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")

    def refresh_dropdowns(self):
        """Populates or updates the branch dropdown."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch,
                                              command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)
        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)

    def generate_summary(self):
        """Generates and displays the weekly sales summary."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to generate weekly summaries.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self.update_summary_labels(None, None)
            self._clear_treeview()
            return
        try:
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self.parent)
                return

            selected_branch = self.branch_var.get()
            weekly_sales_df = self.data_manager.get_weekly_sales(start_date, end_date, selected_branch)

            if weekly_sales_df.empty or weekly_sales_df['Total'].sum() == 0:
                messagebox.showinfo("No Data", "No sales data found for the selected week and branch.", parent=self.parent)
                self.ax.clear()
                self.canvas.draw()
                self.update_summary_labels(None, None)
                self._clear_treeview()
                return

            self.ax.clear()
            self.ax.bar(weekly_sales_df['DayOfWeek'], weekly_sales_df['Total'], color=COLOR_SECONDARY)
            self.ax.set_title(f'Weekly Sales Summary ({start_date_str} to {end_date_str})')
            self.ax.set_xlabel('Day of Week')
            self.ax.set_ylabel('Total Sales (Rs.)')
            self.fig.tight_layout()
            self.canvas.draw()

            total_revenue = weekly_sales_df['Total'].sum()
            num_days_with_sales = (weekly_sales_df['Total'] > 0).sum()
            avg_daily_sales = total_revenue / num_days_with_sales if num_days_with_sales > 0 else 0

            self.update_summary_labels(total_revenue, avg_daily_sales)

            self._clear_treeview()
            for index, row in weekly_sales_df.iterrows():
                self.tree.insert("", "end", values=(row['DayOfWeek'], f"Rs. {row['Total']:.2f}"))
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD.", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self.parent)

    def update_summary_labels(self, total_revenue, avg_daily_sales):
        """Updates the summary statistics labels."""
        self.total_revenue_label.config(
            text=f"Total Revenue: Rs. {total_revenue:.2f}" if total_revenue is not None else "Total Revenue: N/A"
        )
        self.avg_daily_sales_label.config(
            text=f"Average Daily Sales: Rs. {avg_daily_sales:.2f}" if avg_daily_sales is not None else "Average Daily Sales: N/A"
        )

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)


class ProductPreferencePage:
    """Highlights most popular products based on units sold and revenue."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.create_header()
        self.create_controls()
        self.create_chart_area()
        self.create_table_area()
        self.last_report_data = None  # To hold data for export
        self.refresh_dropdowns()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Product Preference Analysis", font=("Arial", 18, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_controls(self):
        """Creates control elements for applying filters."""
        control_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        control_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(control_frame, text="Start Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=0, padx=5)

        self.start_date_entry = tk.Entry(control_frame, width=15, font=FONT_NORMAL)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="End Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=2, padx=5)

        self.end_date_entry = tk.Entry(control_frame, width=15, font=FONT_NORMAL)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="Branch:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=4, padx=5)

        self.branch_var = tk.StringVar(self.parent)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Analyze Preferences", command=self.analyze_preferences,
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").grid(
                 row=1, column=0, columnspan=3, pady=10)

        tk.Button(control_frame, text="Export Report", command=self.export_report,
                 font=FONT_BUTTON, bg=COLOR_INFO, fg=COLOR_WHITE, relief="flat").grid(
                 row=1, column=3, columnspan=3, pady=10)

    def create_chart_area(self):
        """Creates the area for displaying charts."""
        self.fig, self.ax = plt.subplots(figsize=(12, 5))  # Increased chart size
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=20, pady=10)

    def create_table_area(self):
        """Creates the area for displaying tabular data."""
        tree_frame = tk.Frame(self.parent)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("Product", "UnitsSold", "Revenue"), show="headings")
        self.tree.heading("Product", text="Product")
        self.tree.heading("UnitsSold", text="Units Sold")
        self.tree.heading("Revenue", text="Revenue (Rs.)")
        self.tree.column("Product", width=250, anchor="w")
        self.tree.column("UnitsSold", width=120, anchor="center")
        self.tree.column("Revenue", width=150, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_scroll.pack(side="right", fill="y")

    def refresh_dropdowns(self):
        """Populates or updates the branch dropdown."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch,
                                              command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)
        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)

    def analyze_preferences(self):
        """Analyzes and displays product preferences."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to analyze product preferences.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self._clear_treeview()
            self.last_report_data = None
            return
        try:
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self.parent)
                return

            selected_branch = self.branch_var.get()
            date_range = (start_date, end_date)
            preference_df = self.data_manager.get_product_preferences(date_range, branch=selected_branch)

            if preference_df.empty:
                messagebox.showinfo("No Data", "No product preference data found for the selected criteria.", parent=self.parent)
                self.ax.clear()
                self.canvas.draw()
                self._clear_treeview()
                self.last_report_data = None
                return

            self.last_report_data = preference_df.copy()
            self._clear_treeview()
            for index, row in preference_df.iterrows():
                self.tree.insert("", "end", values=(
                    row['Product'],
                    f"{row['UnitsSold']:.0f}",
                    f"Rs. {row['Revenue']:.2f}"
                ))

            self.ax.clear()
            top_10 = preference_df.head(10)
            if not top_10.empty:
                bars = self.ax.barh(top_10['Product'][::-1], top_10['UnitsSold'][::-1], color=COLOR_SECONDARY)
                self.ax.set_title('Top 10 Product Preferences by Units Sold')
                self.ax.set_xlabel('Units Sold')
                self.ax.set_ylabel('Product')
                # Add value labels to the right of each bar
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    self.ax.text(width * 1.02, bar.get_y() + bar.get_height()/2, f'{width:.0f}', va='center', ha='left', fontsize=10)
                self.fig.tight_layout()
            else:
                self.ax.text(0.5, 0.5, "No data for chart", horizontalalignment='center',
                         verticalalignment='center', transform=self.ax.transAxes)
            self.canvas.draw()
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD.", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self.parent)

    def _clear_treeview(self):
        """Clears all existing items from the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def export_report(self):
        """Exports the product preference report to CSV/Excel."""
        if self.last_report_data is None or self.last_report_data.empty:
            messagebox.showwarning("No Data", "Generate a report first before exporting.", parent=self.parent)
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")],
            title="Save Product Preference Report"
        )
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    self.last_report_data.to_csv(file_path, index=False)
                elif file_path.endswith(".xlsx"):
                    self.last_report_data.to_excel(file_path, index=False)
                messagebox.showinfo("Export Success", f"Report saved to {file_path}", parent=self.parent)
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export report: {e}", parent=self.parent)


class SalesDistributionPage:
    """Visualizes how total sales amounts are distributed across transactions."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.create_header()
        self.create_controls()
        self.create_chart_area()
        self.create_stats_labels()
        self.refresh_dropdowns()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Sales Distribution Analysis", font=("Arial", 18, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_controls(self):
        """Creates control elements for filtering data."""
        control_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        control_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(control_frame, text="Start Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=0, padx=5)

        self.start_date_entry = tk.Entry(control_frame, width=15, font=FONT_NORMAL)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="End Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=2, padx=5)

        self.end_date_entry = tk.Entry(control_frame, width=15, font=FONT_NORMAL)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        tk.Label(control_frame, text="Branch:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=4, padx=5)

        self.branch_var = tk.StringVar(self.parent)
        self.branch_dropdown = tk.OptionMenu(control_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=5, padx=5)

        tk.Button(control_frame, text="Analyze Distribution", command=self.analyze_distribution,
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").grid(
                 row=1, column=0, columnspan=6, pady=10)

    def create_chart_area(self):
        """Creates the area for displaying charts."""
        self.fig, self.ax = plt.subplots(figsize=(12, 5))  # Increased chart size
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(padx=20, pady=10)

    def create_stats_labels(self):
        """Creates labels for distribution statistics."""
        self.stats_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        self.stats_frame.pack(pady=10, fill="x", padx=20)
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.mean_label = tk.Label(self.stats_frame, text="Mean: N/A",
                                bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.mean_label.grid(row=0, column=0, padx=10)

        self.median_label = tk.Label(self.stats_frame, text="Median: N/A",
                                  bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.median_label.grid(row=0, column=1, padx=10)

        self.mode_label = tk.Label(self.stats_frame, text="Mode: N/A",
                               bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.mode_label.grid(row=0, column=2, padx=10)

        self.min_label = tk.Label(self.stats_frame, text="Min: N/A",
                              bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.min_label.grid(row=0, column=3, padx=10)

        self.max_label = tk.Label(self.stats_frame, text="Max: N/A",
                              bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.max_label.grid(row=0, column=4, padx=10)

        self.std_dev_label = tk.Label(self.stats_frame, text="Std Dev: N/A",
                                    bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.std_dev_label.grid(row=0, column=5, padx=10)

    def refresh_dropdowns(self):
        """Populates or updates the branch dropdown."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch,
                                              command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)
        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)

    def analyze_distribution(self):
        """Analyzes and displays sales amount distribution."""
        if self.data_manager.sales_data.empty:
            messagebox.showinfo("No Data", "Please import sales data first to analyze sales distribution.", parent=self.parent)
            self.ax.clear()
            self.canvas.draw()
            self.update_stats(None, None, None, None, None, None)
            return
        try:
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self.parent)
                return

            selected_branch = self.branch_var.get()
            date_range = (start_date, end_date)
            sales_amounts = self.data_manager.get_sales_distribution(date_range, branch=selected_branch)

            if sales_amounts.empty:
                messagebox.showinfo("No Data", "No sales distribution data found for the selected criteria.", parent=self.parent)
                self.ax.clear()
                self.canvas.draw()
                self.update_stats(None, None, None, None, None, None)
                return

            self.ax.clear()
            self.ax.hist(sales_amounts, bins=30, edgecolor='black', alpha=0.7, color=COLOR_SECONDARY)
            self.ax.set_title('Sales Amount Distribution')
            self.ax.set_xlabel('Sales Amount (Rs.)')
            self.ax.set_ylabel('Frequency')
            self.fig.tight_layout()
            self.canvas.draw()

            mean_val = sales_amounts.mean()
            median_val = sales_amounts.median()
            mode_val = sales_amounts.mode()[0] if not sales_amounts.mode().empty else np.nan
            min_val = sales_amounts.min()
            max_val = sales_amounts.max()
            std_dev_val = sales_amounts.std()

            self.update_stats(mean_val, median_val, mode_val, min_val, max_val, std_dev_val)
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD.", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self.parent)

    def update_stats(self, mean, median, mode, min_val, max_val, std_dev):
        """Updates the statistical labels for sales distribution."""
        self.mean_label.config(text=f"Mean: Rs. {mean:,.2f}" if mean is not None else "Mean: N/A")
        self.median_label.config(text=f"Median: Rs. {median:,.2f}" if median is not None else "Median: N/A")
        self.mode_label.config(text=f"Mode: Rs. {mode:,.2f}" if not np.isnan(mode) else "Mode: N/A")
        self.min_label.config(text=f"Min: Rs. {min_val:,.2f}" if min_val is not None else "Min: N/A")
        self.max_label.config(text=f"Max: Rs. {max_val:,.2f}" if max_val is not None else "Max: N/A")
        self.std_dev_label.config(text=f"Std Dev: Rs. {std_dev:,.2f}" if std_dev is not None else "Std Dev: N/A")


class DataImportPage:
    """Allows users to import new sales data from CSV/Excel files."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.file_path = ""
        self.preview_df = None
        self.create_header()
        self.create_upload_controls()
        self.create_preview_area()
        self.create_status_labels()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Upload New Sales Data", font=("Arial", 16, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_upload_controls(self):
        """Creates controls for uploading files."""
        control_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        control_frame.pack(pady=10, fill="x", padx=20)

        button_frame = tk.Frame(control_frame, bg=COLOR_DARK_BACKGROUND)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Choose File", command=self.choose_file,
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").pack(side="left", padx=10)

        self.file_label = tk.Label(button_frame, text="No file selected",
                               bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT, font=FONT_NORMAL)
        self.file_label.pack(side="left", padx=10)

        tk.Button(control_frame, text="Preview Data", command=self.preview_data,
                 font=FONT_BUTTON, bg=COLOR_INFO, fg=COLOR_WHITE, relief="flat").pack(pady=10)

        self.save_button = tk.Button(control_frame, text="Save to System", command=self.save_data,
                                 font=("Arial", 12, "bold"), bg=COLOR_SUCCESS, fg=COLOR_WHITE, relief="flat", state=tk.DISABLED)
        self.save_button.pack(pady=10)

        self.status_label = tk.Label(control_frame, text="", fg=COLOR_SUCCESS,
                                 bg=COLOR_DARK_BACKGROUND, font=FONT_NORMAL)
        self.status_label.pack(pady=10)

    def create_preview_area(self):
        """Creates the area for displaying file previews."""
        self.preview_text = tk.Text(self.parent, wrap="word", height=15, width=80, font=("Courier New", 9))
        self.preview_text.pack(pady=10, fill="both", expand=True, padx=20)

    def create_status_labels(self):
        """Creates labels for status information."""
        pass  # Already created in create_upload_controls

    def choose_file(self):
        """Opens a file dialog for selecting CSV/Excel files."""
        self.file_path = filedialog.asksaveasfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if self.file_path:
            self.file_label.config(text=os.path.basename(self.file_path))
            self.save_button.config(state=tk.DISABLED)  # Disable until preview is successful
            self.status_label.config(text="")
            self.preview_text.delete(1.0, tk.END)  # Clear previous preview
        else:
            self.file_label.config(text="No file selected")

    def preview_data(self):
        """Reads and displays a preview of the selected data file."""
        if not self.file_path:
            messagebox.showwarning("No File", "Please choose a file first.", parent=self.parent)
            return
        try:
            if self.file_path.endswith(".csv"):
                df = pd.read_csv(self.file_path)
            elif self.file_path.endswith(".xlsx"):
                df = pd.read_excel(self.file_path)
            else:
                raise ValueError("Unsupported file type. Please select CSV or Excel.")
            self.preview_df = df  # Store for saving
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "Preview of the first 5 rows:\n")
            self.preview_text.insert(tk.END, df.head().to_string())
            self.preview_text.insert(tk.END, f"\nTotal records in preview: {len(df)}")

            required_cols = ['Date', 'Branch', 'Product', 'Quantity', 'UnitPrice', 'Total']
            if all(col in df.columns for col in required_cols):
                self.save_button.config(state=tk.NORMAL)  # Enable save button
                self.status_label.config(text="File ready for import. Review data before saving.", fg=COLOR_LIGHT_TEXT)
            else:
                missing_cols = [col for col in required_cols if col not in df.columns]
                self.save_button.config(state=tk.DISABLED)
                self.status_label.config(text=f"Missing required columns: {', '.join(missing_cols)}", fg=COLOR_DANGER)
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error reading file: {e}", parent=self.parent)
            self.preview_df = None
            self.save_button.config(state=tk.DISABLED)
            self.status_label.config(text="Error during preview.", fg=COLOR_DANGER)

    def save_data(self):
        """Saves the previewed data to the system via DataManager."""
        if self.preview_df is None or self.preview_df.empty:
            messagebox.showwarning("No Data", "No data to save. Please preview a file first.", parent=self.parent)
            return
        if self.data_manager.add_data(self.preview_df):
            self.status_label.config(text=f"{len(self.preview_df)} records successfully uploaded and saved!", fg=COLOR_SUCCESS)
            self.save_button.config(state=tk.DISABLED)
            self.file_label.config(text="No file selected")
            self.preview_text.delete(1.0, tk.END)
            messagebox.showinfo("Import Success", "Data imported and saved successfully!", parent=self.parent)
            self.master.update_all_page_dropdowns()  # Update UI if needed
        else:
            self.status_label.config(text="Data upload failed. Check console for errors.", fg=COLOR_DANGER)


class DataExportPage:
    """Allows users to export processed/filtered data to various formats."""
    def __init__(self, parent, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.create_header()
        self.create_filter_controls()
        self.create_export_buttons()
        self.create_status_label()
        self.refresh_dropdowns()

    def create_header(self):
        """Creates the header for this page."""
        tk.Label(self.parent, text="Export Sales Data", font=("Arial", 16, "bold"),
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).pack(pady=20)

    def create_filter_controls(self):
        """Creates controls for applying filters."""
        filter_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        filter_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(filter_frame, text="Branch:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=0, padx=5)

        self.branch_var = tk.StringVar(self.parent)
        self.branch_dropdown = tk.OptionMenu(filter_frame, self.branch_var, "Loading...")
        self.branch_dropdown.grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="Product:", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=0, column=2, padx=5)

        self.product_var = tk.StringVar(self.parent)
        self.product_dropdown = tk.OptionMenu(filter_frame, self.product_var, "Loading...")
        self.product_dropdown.grid(row=0, column=3, padx=5)

        tk.Label(filter_frame, text="Start Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=1, column=0, padx=5, pady=5)

        self.start_date_entry = tk.Entry(filter_frame, width=15, font=FONT_NORMAL)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.start_date_entry.insert(0, "2020-01-01")

        tk.Label(filter_frame, text="End Date (YYYY-MM-DD):", font=FONT_NORMAL,
                 bg=COLOR_DARK_BACKGROUND, fg=COLOR_LIGHT_TEXT).grid(row=1, column=2, padx=5, pady=5)

        self.end_date_entry = tk.Entry(filter_frame, width=15, font=FONT_NORMAL)
        self.end_date_entry.grid(row=1, column=3, padx=5, pady=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

    def create_export_buttons(self):
        """Creates buttons for exporting data."""
        export_button_frame = tk.Frame(self.parent, bg=COLOR_DARK_BACKGROUND)
        export_button_frame.pack(pady=20)

        tk.Button(export_button_frame, text="Export as CSV", command=lambda: self.export_data("csv"),
                 font=FONT_BUTTON, bg=COLOR_SECONDARY, fg=COLOR_WHITE, relief="flat").pack(side="left", padx=10)

        tk.Button(export_button_frame, text="Export as Excel", command=lambda: self.export_data("xlsx"),
                 font=FONT_BUTTON, bg=COLOR_SUCCESS, fg=COLOR_WHITE, relief="flat").pack(side="left", padx=10)

        tk.Button(export_button_frame, text="Export as PDF (Summary)", command=lambda: self.export_data("pdf"),
                 font=FONT_BUTTON, bg=COLOR_DANGER, fg=COLOR_WHITE, relief="flat").pack(side="left", padx=10)

    def create_status_label(self):
        """Creates a label for displaying status messages."""
        self.status_label = tk.Label(self.parent, text="", fg=COLOR_SUCCESS,
                                 bg=COLOR_DARK_BACKGROUND, font=FONT_NORMAL)
        self.status_label.pack(pady=10)

    def refresh_dropdowns(self):
        """Populates or updates the branch and product dropdowns."""
        branches = ["All Branches"] + self.data_manager.get_branches()
        products = ["All Products"] + self.data_manager.get_products()

        self.branch_dropdown['menu'].delete(0, 'end')
        for branch in branches:
            self.branch_dropdown['menu'].add_command(label=branch,
                                              command=tk._setit(self.branch_var, branch))
        if branches:
            self.branch_var.set(branches[0])
        else:
            self.branch_var.set("No Branches Available")
            self.branch_dropdown.config(state=tk.DISABLED)

        self.product_dropdown['menu'].delete(0, 'end')
        for product in products:
            self.product_dropdown['menu'].add_command(label=product,
                                                command=tk._setit(self.product_var, product))
        if products:
            self.product_var.set(products[0])
        else:
            self.product_var.set("No Products Available")
            self.product_dropdown.config(state=tk.DISABLED)

        state = tk.NORMAL if not self.data_manager.sales_data.empty else tk.DISABLED
        self.branch_dropdown.config(state=state)
        self.product_dropdown.config(state=state)

    def export_data(self, file_format):
        """Exports filtered data based on criteria to the chosen format."""
        if self.data_manager.sales_data.empty:
            messagebox.showwarning("No Data", "No data available to export. Please import data first.", parent=self.parent)
            return
        try:
            selected_branch = self.branch_var.get()
            selected_product = self.product_var.get()
            start_date_str = self.start_date_entry.get()
            end_date_str = self.end_date_entry.get()
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showerror("Input Error", "Start date cannot be after end date.", parent=self.parent)
                return

            filtered_df = self.data_manager.sales_data.copy()
            if selected_branch != "All Branches":
                filtered_df = filtered_df[filtered_df['Branch'] == selected_branch]
            if selected_product != "All Products":
                filtered_df = filtered_df[filtered_df['Product'] == selected_product]
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]

            if filtered_df.empty:
                messagebox.showinfo("No Data", "No data found for the selected filters to export.", parent=self.parent)
                return

            file_types = {
                "csv": [("CSV files", "*.csv")],
                "xlsx": [("Excel files", "*.xlsx")],
                "pdf": [("PDF files", "*.pdf")]
            }
            default_ext = "." + file_format
            file_path = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=file_types.get(file_format, [("All files", "*.*")]),
                title=f"Save Data as {file_format.upper()}"
            )
            if file_path:
                if file_format == "csv":
                    filtered_df.to_csv(file_path, index=False)
                elif file_format == "xlsx":
                    filtered_df.to_excel(file_path, index=False)
                elif file_format == "pdf":
                    fig, ax = plt.subplots(figsize=(11, 8.5))  # Standard paper size
                    ax.axis('off')
                    ax.set_title(f"Sales Data Export ({start_date_str} to {end_date_str})", fontsize=14, pad=20)
                    display_df = filtered_df.head(20).copy()
                    if 'Date' in display_df.columns:
                        display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
                    table = ax.table(cellText=display_df.values, colLabels=display_df.columns, loc='center', cellLoc='left')
                    table.auto_set_font_size(False)
                    table.set_fontsize(8)
                    table.scale(1.2, 1.2)
                    fig.savefig(file_path, bbox_inches='tight', pad_inches=0.5)
                    plt.close(fig)  # Close the figure to free memory
                self.status_label.config(text=f"Report downloaded successfully to {file_path}!", fg=COLOR_SUCCESS)
            else:
                self.status_label.config(text="Export cancelled.", fg=COLOR_WARNING)
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use YYYY-MM-DD.", parent=self.parent)
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export: {e}", parent=self.parent)


class ExitConfirmationPage(tk.Toplevel):
    """Confirms user's intention to exit the application."""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Exit Confirmation")
        self.geometry("350x180")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_no)
        self.resizable(False, False)
        self.transient(master)

        tk.Label(self, text="Are you sure you want to exit the application?", font=("Arial", 12, "bold")).pack(pady=30)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Yes, Exit", command=self.on_yes,
                 font=("Arial", 11, "bold"), bg=COLOR_DANGER, fg=COLOR_WHITE, relief="flat").pack(side="left", padx=15)

        tk.Button(button_frame, text="No, Stay", command=self.on_no,
                 font=("Arial", 11, "bold"), bg="#808080", fg=COLOR_WHITE, relief="flat").pack(side="left", padx=15)

    def on_yes(self):
        """Destroys the main application window, exiting the program."""
        self.master.destroy()
        self.destroy()

    def on_no(self):
        """Closes the confirmation window and returns to the main application."""
        self.destroy()
        self.master.deiconify()
        self.master.lift()


# Run the application
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()