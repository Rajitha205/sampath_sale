import unittest
import pandas as pd
import os
import tempfile
from datetime import datetime, timedelta
import numpy as np # For statistical calculations like mode, used in SalesDistributionPage logic
import tkinter as tk # Import tkinter for integration tests

# Import DataManager and MonthlySalesPage from main.py
# Assuming main.py is in the same directory or discoverable in the sales_analysis_system module
from main import DataManager, MonthlySalesPage, PriceAnalysisPage, WeeklySalesPage, ProductPreferencePage, SalesDistributionPage

# Sample data for testing
# This data is designed to cover various scenarios, including multiple branches, products, and dates.
TEST_DATA = pd.DataFrame({
    'Date': [
        '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
        '2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
        '2024-02-10', '2024-02-11', '2024-03-15', '2023-12-25', '2024-01-01' # Added more diverse dates
    ],
    'Branch': [
        'Colombo', 'Kandy', 'Colombo', 'Kandy', 'Colombo',
        'Kandy', 'Colombo', 'Kandy', 'Colombo', 'Kandy',
        'Colombo', 'Kandy', 'Colombo', 'Kandy', 'Colombo'
    ],
    'Product': [
        'Milk', 'Bread', 'Milk', 'Eggs', 'Butter',
        'Bread', 'Milk', 'Eggs', 'Butter', 'Bread',
        'Milk', 'Eggs', 'Butter', 'Milk', 'Bread' # Added more diverse products
    ],
    'Quantity': [2, 3, 1, 4, 2, 2, 3, 1, 3, 4, 5, 2, 1, 3, 2],
    'UnitPrice': [50.0, 60.0, 52.0, 30.0, 100.0, 62.0, 51.0, 31.0, 105.0, 61.0, 55.0, 32.0, 110.0, 50.0, 60.0],
    'Total': [100.0, 180.0, 52.0, 120.0, 200.0, 124.0, 153.0, 31.0, 315.0, 244.0, 275.0, 64.0, 110.0, 150.0, 120.0]
})


class TestDataManager(unittest.TestCase):
    """
    Unit tests for the DataManager class, covering data loading,
    manipulation, and various reporting functionalities.
    """
    def setUp(self):
        """
        Set up a temporary directory and CSV file for each test to ensure
        a clean state and avoid side effects between tests.
        """
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.test_dir.name, "sales_data.csv")
        # Save the TEST_DATA to the temporary CSV file
        TEST_DATA.to_csv(self.data_file, index=False)

        # Initialize DataManager with the temporary data file
        self.manager = DataManager(data_file=self.data_file)

    def tearDown(self):
        """
        Clean up the temporary directory after each test.
        """
        self.test_dir.cleanup()

    def test_load_data(self):
        """Unit Test 1: Data loading - checks if data is loaded and not empty."""
        self.assertFalse(self.manager.sales_data.empty)
        # Check if the number of rows loaded matches the test data
        self.assertEqual(len(self.manager.sales_data), len(TEST_DATA))
        # Check if 'Date' column is correctly parsed as datetime objects
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.manager.sales_data['Date']))

    def test_get_branches(self):
        """Unit Test 2: Get unique branches - verifies correct unique branches are returned."""
        branches = self.manager.get_branches()
        self.assertIsInstance(branches, list)
        self.assertIn('Colombo', branches)
        self.assertIn('Kandy', branches)
        self.assertEqual(len(branches), 2) # Ensure only expected branches are found

    def test_get_products(self):
        """Unit Test 3: Get unique products - verifies correct unique products are returned."""
        products = self.manager.get_products()
        self.assertIsInstance(products, list)
        self.assertIn('Milk', products)
        self.assertIn('Bread', products)
        self.assertIn('Eggs', products)
        self.assertIn('Butter', products)
        self.assertEqual(len(products), 4) # Ensure only expected products are found

    def test_get_years(self):
        """Unit Test 4: Get years from dates - verifies correct unique years are returned."""
        years = self.manager.get_years()
        self.assertIsInstance(years, list)
        self.assertIn(2023, years)
        self.assertIn(2024, years)
        self.assertEqual(len(years), 2) # Ensure only expected years are found

    def test_add_data(self):
        """Unit Test 5: Add new data to existing dataset - checks if data is added and saved."""
        new_data = pd.DataFrame({
            'Date': ['2024-01-06'],
            'Branch': ['Colombo'],
            'Product': ['Cheese'],
            'Quantity': [1],
            'UnitPrice': [150.0],
            'Total': [150.0]
        })
        success = self.manager.add_data(new_data)
        self.assertTrue(success)
        # Check if the total number of records increased by the number of new records
        self.assertEqual(len(self.manager.sales_data), len(TEST_DATA) + len(new_data))
        # Verify the new data is present
        self.assertIn('Cheese', self.manager.sales_data['Product'].values)

    def test_save_data(self):
        """Unit Test 6: Save data back to CSV - verifies data can be saved and reloaded."""
        # The _save_data method in main.py does not take a path argument.
        # It saves to the self.data_file initialized in DataManager.
        # We need to verify that saving affects the file it's supposed to.
        # Add some data to ensure there's something to save beyond initial load
        original_len = len(self.manager.sales_data)
        new_row = pd.DataFrame({
            'Date': ['2024-07-18'], 'Branch': ['Kandy'], 'Product': ['Coffee'],
            'Quantity': [10], 'UnitPrice': [20.0], 'Total': [200.0]
        })
        self.manager.sales_data = pd.concat([self.manager.sales_data, new_row], ignore_index=True)
        self.manager._save_data() # Call the private method without arguments

        # Reload data from the same file to verify changes were saved
        reloaded_manager = DataManager(data_file=self.data_file)
        self.assertEqual(len(reloaded_manager.sales_data), original_len + 1)
        self.assertIn('Coffee', reloaded_manager.sales_data['Product'].values)

    def test_monthly_sales(self):
        """Unit Test 7: Monthly sales aggregation - verifies correct monthly sales calculation."""
        # Test for a specific branch, year, and month
        monthly = self.manager.get_monthly_sales(branch="Colombo", year=2024, month=1)
        self.assertFalse(monthly.empty)
        self.assertIn("Milk", monthly['Product'].values)
        # Expected total for Milk in Colombo, Jan 2024: (2*50.0) + (1*52.0) + (3*51.0) = 100 + 52 + 153 = 305
        self.assertAlmostEqual(monthly[monthly['Product'] == 'Milk']['Total'].iloc[0], 305.0)

        # Test for "All Branches"
        monthly_all_branches = self.manager.get_monthly_sales(branch="All Branches", year=2024, month=1)
        self.assertFalse(monthly_all_branches.empty)
        # Re-calculate expected total for Milk in Jan 2024 (All Branches) based on TEST_DATA
        # Milk sales in Jan 2024:
        # Colombo: (2*50.0) + (1*52.0) + (3*51.0) = 100 + 52 + 153 = 305
        # Kandy: No Milk sales in Jan 2024 in TEST_DATA
        # So total Milk sales for Jan 2024 across all branches is 305.0
        self.assertAlmostEqual(monthly_all_branches[monthly_all_branches['Product'] == 'Milk']['Total'].iloc[0], 305.0)

        # Test for "All Months"
        monthly_all_months = self.manager.get_monthly_sales(branch="Colombo", year=2024, month=None)
        self.assertFalse(monthly_all_months.empty)
        self.assertIn("Butter", monthly_all_months['Product'].values) # Check a product from Feb/Mar

        # Test for no data found
        empty_monthly = self.manager.get_monthly_sales(branch="NonExistentBranch", year=2025, month=1)
        self.assertTrue(empty_monthly.empty)
        self.assertEqual(list(empty_monthly.columns), ['Product', 'Quantity', 'UnitPrice', 'Total'])

    def test_get_product_price_history(self):
        """
        Unit Test 8: Price analysis of each product - verifies historical unit prices.
        """
        # Test for 'Milk'
        milk_price_history = self.manager.get_product_price_history('Milk')
        self.assertFalse(milk_price_history.empty)
        self.assertIn('Date', milk_price_history.columns)
        self.assertIn('UnitPrice', milk_price_history.columns)
        # Expected unique prices for Milk based on TEST_DATA: 50.0, 52.0, 55.0, 51.0
        expected_unique_prices = [50.0, 51.0, 52.0, 55.0]
        actual_unique_prices = sorted(milk_price_history['UnitPrice'].unique().tolist())
        self.assertListEqual(sorted(expected_unique_prices), sorted(actual_unique_prices))
        self.assertTrue(milk_price_history['Date'].is_monotonic_increasing) # Check if sorted by date

        # Test for a product with no history
        no_history = self.manager.get_product_price_history('NonExistentProduct')
        self.assertTrue(no_history.empty)
        self.assertEqual(list(no_history.columns), ['Date', 'UnitPrice'])

    def test_get_weekly_sales(self):
        """
        Unit Test 9: Weekly sales analysis - verifies daily sales totals for a week.
        """
        # Define a specific week (Jan 1 to Jan 7, 2024)
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)

        # Test for "All Branches"
        weekly_sales_all_branches = self.manager.get_weekly_sales(start_date, end_date, "All Branches")
        self.assertFalse(weekly_sales_all_branches.empty)
        self.assertIn('DayOfWeek', weekly_sales_all_branches.columns)
        self.assertIn('Total', weekly_sales_all_branches.columns)
        # Re-calculate expected sales for Monday (Jan 1, 2024) based on TEST_DATA:
        # '2024-01-01', 'Colombo', 'Milk', 'Total': 100.0
        # '2024-01-01', 'Kandy', 'Bread', 'Total': 124.0
        # '2024-01-01', 'Colombo', 'Bread', 'Total': 120.0
        # Total for Monday = 100.0 + 124.0 + 120.0 = 344.0
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Monday']['Total'].iloc[0], 344.0)

        # Expected sales for Tuesday (Jan 2): Bread (Kandy) 180 + Milk (Colombo) 153 = 333
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Tuesday']['Total'].iloc[0], 333.0)
        # Expected sales for Wednesday (Jan 3): Milk (Colombo) 52 + Eggs (Kandy) 31 = 83
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Wednesday']['Total'].iloc[0], 83.0)
        # Expected sales for Thursday (Jan 4): Eggs (Kandy) 120 + Butter (Colombo) 315 = 435
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Thursday']['Total'].iloc[0], 435.0)
        # Expected sales for Friday (Jan 5): Butter (Colombo) 200 + Bread (Kandy) 244 = 444
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Friday']['Total'].iloc[0], 444.0)
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Saturday']['Total'].iloc[0], 0.0)
        self.assertAlmostEqual(weekly_sales_all_branches[weekly_sales_all_branches['DayOfWeek'] == 'Sunday']['Total'].iloc[0], 0.0)


        # Test for a specific branch (Colombo)
        weekly_sales_colombo = self.manager.get_weekly_sales(start_date, end_date, "Colombo")
        self.assertFalse(weekly_sales_colombo.empty)
        # Expected sales for Monday (Jan 1) Colombo: Milk 100 + Bread 120 = 220
        self.assertAlmostEqual(weekly_sales_colombo[weekly_sales_colombo['DayOfWeek'] == 'Monday']['Total'].iloc[0], 220.0)
        # Expected sales for Tuesday (Jan 2) Colombo: Milk 153
        self.assertAlmostEqual(weekly_sales_colombo[weekly_sales_colombo['DayOfWeek'] == 'Tuesday']['Total'].iloc[0], 153.0)

        # Test for no sales in the given period
        empty_weekly = self.manager.get_weekly_sales(datetime(2025, 1, 1), datetime(2025, 1, 7))
        self.assertFalse(empty_weekly.empty) # Should return a DataFrame with 0s
        self.assertTrue(empty_weekly['Total'].sum() == 0)

    def test_get_product_preferences(self):
        """
        Unit Test 10: Product preference analysis - verifies product popularity based on units sold and revenue.
        """
        # Test for a specific date range (Jan 2024) and all branches
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        product_pref_df = self.manager.get_product_preferences((start_date, end_date), branch="All Branches")
        self.assertFalse(product_pref_df.empty)
        self.assertIn('Product', product_pref_df.columns)
        self.assertIn('UnitsSold', product_pref_df.columns)
        self.assertIn('Revenue', product_pref_df.columns)

        # Check sorting by UnitsSold (descending)
        self.assertTrue(product_pref_df['UnitsSold'].is_monotonic_decreasing)

        # Expected data for Jan 2024 (UnitsSold and Revenue from TEST_DATA for dates in Jan 2024):
        # Milk: (2+1+3) = 6 units, (100+52+153) = 305 total
        # Bread: (3+2+4+2) = 11 units, (180+124+244+120) = 668 total
        # Eggs: (4+1) = 5 units, (120+31) = 151 total
        # Butter: (2+3) = 5 units, (200+315) = 515 total

        milk_row = product_pref_df[product_pref_df['Product'] == 'Milk']
        self.assertFalse(milk_row.empty)
        self.assertEqual(milk_row['UnitsSold'].iloc[0], 6)
        self.assertAlmostEqual(milk_row['Revenue'].iloc[0], 305.0)

        bread_row = product_pref_df[product_pref_df['Product'] == 'Bread']
        self.assertFalse(bread_row.empty)
        self.assertEqual(bread_row['UnitsSold'].iloc[0], 11)
        self.assertAlmostEqual(bread_row['Revenue'].iloc[0], 668.0)

        # Test with a specific branch (Colombo)
        product_pref_colombo = self.manager.get_product_preferences((start_date, end_date), branch="Colombo")
        self.assertFalse(product_pref_colombo.empty)
        # Expected data for Jan 2024, Colombo:
        # Milk: Quantity = 2+1+3 = 6, Total = 100+52+153 = 305
        # Butter: Quantity = 2+3 = 5, Total = 200+315 = 515
        # Bread: Quantity = 2, Total = 120
        colombo_milk_row = product_pref_colombo[product_pref_colombo['Product'] == 'Milk']
        self.assertFalse(colombo_milk_row.empty)
        self.assertEqual(colombo_milk_row['UnitsSold'].iloc[0], 6)
        self.assertAlmostEqual(colombo_milk_row['Revenue'].iloc[0], 305.0)

        # Test for no data found
        empty_pref = self.manager.get_product_preferences((datetime(2025, 1, 1), datetime(2025, 1, 31)))
        self.assertTrue(empty_pref.empty)
        self.assertEqual(list(empty_pref.columns), ['Product', 'UnitsSold', 'Revenue'])

    def test_get_sales_distribution(self):
        """
        Unit Test 11: Analysis of the distribution of total sales amount of purchases -
        verifies the series of total sales amounts.
        """
        # Test for all data
        sales_dist_all = self.manager.get_sales_distribution()
        self.assertIsInstance(sales_dist_all, pd.Series)
        self.assertFalse(sales_dist_all.empty)
        self.assertEqual(len(sales_dist_all), len(TEST_DATA)) # Should return all 'Total' values

        # Test with a date range (Jan 2024)
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        sales_dist_jan = self.manager.get_sales_distribution((start_date, end_date))
        self.assertFalse(sales_dist_jan.empty)
        # Expected number of sales in Jan 2024 from TEST_DATA: 11 transactions
        self.assertEqual(len(sales_dist_jan), 11)
        self.assertIn(100.0, sales_dist_jan.values)
        self.assertIn(180.0, sales_dist_jan.values)

        # Test with a specific branch (Kandy) and date range (Jan 2024)
        sales_dist_kandy_jan = self.manager.get_sales_distribution((start_date, end_date), branch="Kandy")
        self.assertFalse(sales_dist_kandy_jan.empty)
        # Expected Kandy sales in Jan 2024: 180.0, 120.0, 31.0, 244.0
        self.assertEqual(len(sales_dist_kandy_jan), 4)
        self.assertIn(180.0, sales_dist_kandy_jan.values)
        self.assertIn(120.0, sales_dist_kandy_jan.values)

        # Test for no data found
        empty_dist = self.manager.get_sales_distribution((datetime(2025, 1, 1), datetime(2025, 1, 31)))
        self.assertTrue(empty_dist.empty)
        self.assertIsInstance(empty_dist, pd.Series)


class TestIntegration(unittest.TestCase):
    """
    Integration tests for interactions between DataManager and UI pages.
    These tests simulate user actions to ensure components work together.
    """
    def setUp(self):
        """
        Set up a temporary directory and CSV file for each test,
        and initialize DataManager.
        """
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.test_dir.name, "sales_data.csv")
        TEST_DATA.to_csv(self.data_file, index=False)
        self.manager = DataManager(data_file=self.data_file)

        # Create a dummy Tkinter root for UI page instantiation
        self.root = tk.Tk()
        self.root.withdraw() # Hide the root window

    def tearDown(self):
        """
        Clean up the temporary directory and destroy the Tkinter root.
        """
        self.test_dir.cleanup()
        self.root.destroy()

    def test_full_monthly_flow_integration(self):
        """
        Integration Test 1: End-to-end monthly report generation.
        Simulates selecting filters and generating a report.
        """
        # Pass a dummy parent frame (self.root) as MonthlySalesPage expects a Tkinter widget
        monthly_page = MonthlySalesPage(parent=self.root, data_manager=self.manager)
        # Simulate user selections
        monthly_page.branch_var.set("Colombo")
        monthly_page.year_var.set("2024")
        monthly_page.month_var.set("January")
        monthly_page.generate_report()

        # Assertions based on expected report data
        self.assertIsNotNone(monthly_page.last_report_df)
        self.assertFalse(monthly_page.last_report_df.empty)
        self.assertIn("Milk", monthly_page.last_report_df['Product'].values)
        # Verify a specific value in the generated report
        colombo_jan_milk_total = monthly_page.last_report_df[monthly_page.last_report_df['Product'] == 'Milk']['Total'].iloc[0]
        self.assertAlmostEqual(colombo_jan_milk_total, 305.0)

    def test_price_analysis_page_integration(self):
        """
        Integration Test 2: Price Analysis Page - simulates selecting a product and analyzing price.
        """
        price_page = PriceAnalysisPage(parent=self.root, data_manager=self.manager)
        price_page.product_var.set("Milk")
        price_page.analyze_price()

        # Check if the chart was drawn (by checking if ax has content)
        # Note: ax.lines will be populated if plot() is called.
        self.assertGreater(len(price_page.ax.lines), 0, "Chart should have lines (data plotted)")
        # Check if stats labels were updated
        self.assertNotEqual(price_page.avg_price_label.cget("text"), "Average Price: N/A")
        self.assertNotEqual(price_page.max_price_label.cget("text"), "Max Price: N/A")
        self.assertNotEqual(price_page.min_price_label.cget("text"), "Min Price: N/A")
        self.assertNotEqual(price_page.current_price_label.cget("text"), "Current Price: N/A")
        # Check if treeview was populated
        self.assertGreater(len(price_page.tree.get_children()), 0)

    def test_weekly_sales_page_integration(self):
        """
        Integration Test 3: Weekly Sales Page - simulates setting dates and generating summary.
        """
        weekly_page = WeeklySalesPage(parent=self.root, data_manager=self.manager)
        weekly_page.start_date_entry.delete(0, tk.END)
        weekly_page.start_date_entry.insert(0, "2024-01-01")
        weekly_page.end_date_entry.delete(0, tk.END)
        weekly_page.end_date_entry.insert(0, "2024-01-07")
        weekly_page.branch_var.set("All Branches")
        weekly_page.generate_summary()

        # Check if the chart was drawn
        self.assertGreater(len(weekly_page.ax.patches), 0, "Chart should have bars (data plotted)")
        # Check if summary labels were updated
        self.assertNotEqual(weekly_page.total_revenue_label.cget("text"), "Total Revenue: N/A")
        self.assertNotEqual(weekly_page.avg_daily_sales_label.cget("text"), "Average Daily Sales: N/A")
        # Check if treeview was populated
        self.assertGreater(len(weekly_page.tree.get_children()), 0)

    def test_product_preference_page_integration(self):
        """
        Integration Test 4: Product Preference Page - simulates setting filters and analyzing preferences.
        """
        pref_page = ProductPreferencePage(parent=self.root, data_manager=self.manager)
        pref_page.start_date_entry.delete(0, tk.END)
        pref_page.start_date_entry.insert(0, "2024-01-01")
        pref_page.end_date_entry.delete(0, tk.END)
        pref_page.end_date_entry.insert(0, "2024-01-31")
        pref_page.branch_var.set("All Branches")
        pref_page.analyze_preferences()

        # Check if the chart was drawn
        self.assertGreater(len(pref_page.ax.patches), 0, "Chart should have bars (data plotted)")
        # Check if treeview was populated
        self.assertGreater(len(pref_page.tree.get_children()), 0)
        self.assertIsNotNone(pref_page.last_report_data)
        self.assertFalse(pref_page.last_report_data.empty)

    def test_sales_distribution_page_integration(self):
        """
        Integration Test 5: Sales Distribution Page - simulates setting filters and analyzing distribution.
        """
        dist_page = SalesDistributionPage(parent=self.root, data_manager=self.manager)
        dist_page.start_date_entry.delete(0, tk.END)
        dist_page.start_date_entry.insert(0, "2024-01-01")
        dist_page.end_date_entry.delete(0, tk.END)
        dist_page.end_date_entry.insert(0, "2024-01-31")
        dist_page.branch_var.set("All Branches")
        dist_page.analyze_distribution()

        # Check if the chart was drawn
        self.assertGreater(len(dist_page.ax.patches), 0, "Chart should have bars (data plotted)")
        # Check if stats labels were updated
        self.assertNotEqual(dist_page.mean_label.cget("text"), "Mean: N/A")
        self.assertNotEqual(dist_page.median_label.cget("text"), "Median: N/A")


class TestRegression(unittest.TestCase):
    """
    Regression tests to ensure that existing functionalities maintain
    consistent output after code changes.
    """
    def setUp(self):
        """
        Set up a temporary directory and CSV file for each test.
        """
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.test_dir.name, "sales_data.csv")
        TEST_DATA.to_csv(self.data_file, index=False)
        self.manager = DataManager(data_file=self.data_file)

    def tearDown(self):
        """
        Clean up the temporary directory after each test.
        """
        self.test_dir.cleanup()

    def test_regression_get_monthly_sales_against_previous_result(self):
        """
        Regression Test 1: Ensure consistent output of get_monthly_sales for a known input.
        """
        # Filter TEST_DATA to match the expected result's scope (Colombo, Jan 2024)
        # and re-calculate expected values for robustness against TEST_DATA changes
        filtered_test_data = TEST_DATA[
            (TEST_DATA['Branch'] == 'Colombo') &
            (pd.to_datetime(TEST_DATA['Date']).dt.year == 2024) &
            (pd.to_datetime(TEST_DATA['Date']).dt.month == 1)
        ].copy()

        if not filtered_test_data.empty:
            expected_result_calculated = filtered_test_data.groupby('Product').agg(
                Quantity=('Quantity', 'sum'),
                UnitPrice=('UnitPrice', 'mean'),
                Total=('Total', 'sum')
            ).reset_index().sort_values(by='Product').reset_index(drop=True)
        else:
            expected_result_calculated = pd.DataFrame(columns=['Product', 'Quantity', 'UnitPrice', 'Total'])


        result = self.manager.get_monthly_sales(branch="Colombo", year=2024, month=1)

        # Sort both dataframes by 'Product' to ensure consistent comparison
        result_sorted = result.sort_values(by='Product').reset_index(drop=True)
        expected_result_sorted = expected_result_calculated.sort_values(by='Product').reset_index(drop=True)

        # Use pandas.testing.assert_frame_equal for robust DataFrame comparison
        pd.testing.assert_frame_equal(result_sorted, expected_result_sorted, check_dtype=False)


def coverage_test():
    """
    Coverage Testing: Runs unit tests with coverage analysis and generates reports.
    """
    import coverage

    # Initialize coverage, specifying the source directory to monitor
    cov = coverage.Coverage(source=['sales_analysis_system'])
    cov.start()

    # Load and run all tests from TestDataManager
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataManager)
    unittest.TextTestRunner(verbosity=2).run(suite) # Increased verbosity for detailed output

    cov.stop()
    cov.save()
    print("\n--- Code Coverage Report ---\n")
    cov.report() # Print summary report to console
    cov.html_report(directory='coverage_report') # Generate HTML report in 'coverage_report' directory


if __name__ == "__main__":
    print("Running Unit Tests...")
    # Run unit tests from TestDataManager
    unittest.main(module='sales_analysis_system.test', argv=['first-arg-is-ignored'], exit=False, verbosity=2)

    print("\nRunning Integration Tests...")
    # Load and run all tests from TestIntegration
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
    unittest.TextTestRunner(verbosity=2).run(integration_suite)

    print("\nRunning Regression Tests...")
    # Load and run all tests from TestRegression
    regression_suite = unittest.TestLoader().loadTestsFromTestCase(TestRegression)
    unittest.TextTestRunner(verbosity=2).run(regression_suite)

    print("\nRunning Coverage Analysis...")
    coverage_test()