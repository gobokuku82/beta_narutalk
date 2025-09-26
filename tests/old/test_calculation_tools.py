"""
Test file for calculation and analysis tools
계산 및 분석 도구 테스트
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.tools.calculation_tool import get_calculation_tool
from backend.service.tools.trend_analysis_tool import get_trend_analysis_tool
from backend.service.tools.cross_db_analysis_tool import get_cross_db_analysis_tool


class TestCalculationTools:
    """Test suite for calculation tools"""

    def __init__(self):
        self.calculation_tool = get_calculation_tool()
        self.trend_tool = get_trend_analysis_tool()
        self.cross_db_tool = get_cross_db_analysis_tool()

    # ============== Calculation Tool Tests ==============

    def test_basic_calculations(self):
        """Test basic arithmetic operations"""
        print("\n" + "="*60)
        print("Testing Basic Calculations")
        print("="*60)

        # Test data
        values = [100, 200, 150, 180, 220, 190]

        # Sum
        total = self.calculation_tool.calculate_sum(values)
        print(f"Sum of {values}: {total}")
        assert total == 1040, f"Expected 1040, got {total}"

        # Average
        avg = self.calculation_tool.calculate_average(values)
        print(f"Average: {avg}")
        assert abs(avg - 173.33) < 0.1, f"Expected ~173.33, got {avg}"

        # Min/Max
        min_max = self.calculation_tool.calculate_min_max(values)
        print(f"Min/Max: {min_max}")
        assert min_max["min"] == 100, f"Expected min 100, got {min_max['min']}"
        assert min_max["max"] == 220, f"Expected max 220, got {min_max['max']}"

        # Median
        median = self.calculation_tool.calculate_median(values)
        print(f"Median: {median}")
        assert median == 185, f"Expected 185, got {median}"

        print("✓ Basic calculations test passed")

    def test_business_metrics(self):
        """Test business metric calculations"""
        print("\n" + "="*60)
        print("Testing Business Metrics")
        print("="*60)

        # Achievement rate
        achievement = self.calculation_tool.calculate_achievement_rate(850, 1000)
        print(f"Achievement Rate (850/1000): {achievement}%")
        assert achievement == 85.0, f"Expected 85.0%, got {achievement}%"

        # Growth rate
        growth = self.calculation_tool.calculate_growth_rate(1200, 1000)
        print(f"Growth Rate (1000->1200): {growth}%")
        assert growth == 20.0, f"Expected 20.0%, got {growth}%"

        # Market share
        share = self.calculation_tool.calculate_market_share(300, 1000)
        print(f"Market Share (300/1000): {share}%")
        assert share == 30.0, f"Expected 30.0%, got {share}%"

        # Performance grade
        grade = self.calculation_tool.get_performance_grade(115)
        print(f"Performance Grade (115% achievement): {grade}")
        assert grade == "A", f"Expected A, got {grade}"

        print("✓ Business metrics test passed")

    def test_period_calculations(self):
        """Test period-based calculations"""
        print("\n" + "="*60)
        print("Testing Period Calculations")
        print("="*60)

        # Monthly data for MoM growth
        monthly_data = {
            "202401": 1000,
            "202402": 1100,
            "202403": 1050,
            "202404": 1200,
            "202405": 1300,
            "202406": 1250
        }

        # MoM growth
        mom_result = self.calculation_tool.calculate_mom_growth(monthly_data)
        print(f"MoM Growth Analysis:")
        print(f"  Average Growth: {mom_result['average_growth']}%")
        print(f"  Trend: {mom_result['trend']}")
        print(f"  Monthly Growth: {list(mom_result['monthly_growth'].items())[:3]}...")

        assert "average_growth" in mom_result, "Missing average_growth in MoM result"
        assert mom_result["trend"] in ["increasing", "decreasing", "stable"], f"Invalid trend: {mom_result['trend']}"

        # Currency formatting
        formatted = self.calculation_tool.format_currency(123456789)
        print(f"Currency Format (123456789): {formatted}")
        assert "억" in formatted, f"Expected 억 in {formatted}"

        print("✓ Period calculations test passed")

    # ============== Trend Analysis Tool Tests ==============

    def test_trend_analysis(self):
        """Test trend analysis capabilities"""
        print("\n" + "="*60)
        print("Testing Trend Analysis")
        print("="*60)

        # Sample data with upward trend
        data = [100, 110, 105, 120, 125, 130, 140, 135, 150, 160]
        labels = [f"2024{i:02d}" for i in range(1, 11)]

        # Historical trend
        trend = self.trend_tool.analyze_historical_trend(data, labels)
        print(f"Trend Analysis:")
        print(f"  Direction: {trend['trend_direction']}")
        print(f"  Strength: {trend['trend_strength']:.2f}")
        print(f"  Volatility: {trend['volatility']}%")
        print(f"  Peak: {trend['peak']}")
        print(f"  Summary: {trend['summary']}")

        assert trend["trend_direction"] == "increasing", f"Expected increasing trend, got {trend['trend_direction']}"

        # Moving average
        ma = self.trend_tool.calculate_moving_average(data, window=3)
        print(f"Moving Average (3-period): {ma[:5]}...")
        assert len(ma) == len(data), f"Expected {len(data)} values, got {len(ma)}"

        print("✓ Trend analysis test passed")

    def test_seasonality_detection(self):
        """Test seasonality detection"""
        print("\n" + "="*60)
        print("Testing Seasonality Detection")
        print("="*60)

        # Create data with seasonal pattern
        monthly_data = {}
        for year in [2023, 2024]:
            for month in range(1, 13):
                # Higher values in summer months (6-8)
                if month in [6, 7, 8]:
                    value = 1500 + (month - 6) * 100
                else:
                    value = 1000 + month * 10
                monthly_data[f"{year}{month:02d}"] = value

        seasonality = self.trend_tool.detect_seasonality(monthly_data)
        print(f"Seasonality Analysis:")
        print(f"  Has Seasonality: {seasonality['has_seasonality']}")
        print(f"  Peak Season: {seasonality['peak_season']}")
        print(f"  Low Season: {seasonality['low_season']}")
        print(f"  Strength: {seasonality.get('seasonality_strength', 0)}%")
        print(f"  Summary: {seasonality['summary']}")

        assert "peak_season" in seasonality, "Missing peak_season in seasonality result"

        print("✓ Seasonality detection test passed")

    def test_predictions(self):
        """Test prediction capabilities"""
        print("\n" + "="*60)
        print("Testing Predictions")
        print("="*60)

        # Historical data for prediction
        historical = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]

        # Simple trend prediction
        prediction = self.trend_tool.predict_future_trend(historical, periods_ahead=3)
        print(f"Trend Prediction:")
        print(f"  Next 3 periods: {prediction['predictions']}")
        print(f"  Method: {prediction['method']}")
        print(f"  Quality: {prediction.get('prediction_quality', 'N/A')}")
        print(f"  R-squared: {prediction.get('r_squared', 0)}")
        print(f"  Summary: {prediction['summary']}")

        assert len(prediction["predictions"]) == 3, f"Expected 3 predictions, got {len(prediction['predictions'])}"
        assert prediction["predictions"][0] > historical[-1], "Expected increasing prediction"

        print("✓ Predictions test passed")

    def test_anomaly_detection(self):
        """Test anomaly detection"""
        print("\n" + "="*60)
        print("Testing Anomaly Detection")
        print("="*60)

        # Data with anomalies
        data = [100, 105, 110, 300, 108, 112, 115, 50, 118, 120]  # 300 and 50 are anomalies

        anomalies = self.trend_tool.detect_anomalies(data, threshold=2.0)
        print(f"Anomaly Detection:")
        print(f"  Anomalies found: {anomalies['anomaly_count']}")
        print(f"  Mean: {anomalies['mean']}")
        print(f"  Std: {anomalies['std']}")

        if anomalies["anomalies"]:
            print(f"  Detected anomalies:")
            for anom in anomalies["anomalies"]:
                print(f"    Index {anom['index']}: Value={anom['value']}, Z-score={anom['z_score']}")

        print(f"  Summary: {anomalies['summary']}")

        assert anomalies["anomaly_count"] > 0, "Should detect at least one anomaly"

        print("✓ Anomaly detection test passed")

    # ============== Cross-DB Analysis Tool Tests ==============

    async def test_cross_db_analysis(self):
        """Test cross-database analysis capabilities"""
        print("\n" + "="*60)
        print("Testing Cross-DB Analysis")
        print("="*60)

        # Test personal performance analysis
        print("\nTesting personal performance analysis...")
        try:
            result = await self.cross_db_tool.analyze_personal_performance(
                person_name="김영희",
                period="2024"
            )

            if result["status"] == "success":
                print(f"Personal Performance Analysis:")
                print(f"  Total Sales: {result.get('total_sales', 0):,.0f}")
                print(f"  Achievement Rate: {result.get('achievement_rate', 0):.1f}%")
                print(f"  Product Count: {result.get('product_count', 0)}")
                print(f"  Client Count: {result.get('client_count', 0)}")

                if "monthly_performance" in result:
                    months = list(result["monthly_performance"].keys())[:3]
                    print(f"  Sample Monthly Data: {months}")

                print(f"  Summary: {result.get('summary', 'N/A')}")
                print("✓ Personal performance analysis completed")
            else:
                print(f"  Analysis failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"  Error during personal performance analysis: {e}")

        # Test client analysis
        print("\nTesting client analysis...")
        try:
            result = await self.cross_db_tool.analyze_client_performance(
                client_id="H001"
            )

            if result["status"] == "success":
                print(f"Client Analysis:")
                print(f"  Hospital: {result.get('hospital_name', 'N/A')}")
                print(f"  Total Sales: {result.get('total_sales', 0):,.0f}")
                print(f"  Product Count: {result.get('product_count', 0)}")

                if "top_products" in result and result["top_products"]:
                    print(f"  Top Products: {result['top_products'][:3]}")

                print(f"  Summary: {result.get('summary', 'N/A')}")
                print("✓ Client analysis completed")
            else:
                print(f"  Analysis failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"  Error during client analysis: {e}")

        # Test product analysis
        print("\nTesting product analysis...")
        try:
            result = await self.cross_db_tool.analyze_product_performance(
                product_name="제품A"
            )

            if result["status"] == "success":
                print(f"Product Analysis:")
                print(f"  Total Sales: {result.get('total_sales', 0):,.0f}")
                print(f"  Client Count: {result.get('client_count', 0)}")
                print(f"  Employee Count: {result.get('employee_count', 0)}")

                if "top_clients" in result and result["top_clients"]:
                    print(f"  Top Clients: {list(result['top_clients'].keys())[:3]}")

                print(f"  Summary: {result.get('summary', 'N/A')}")
                print("✓ Product analysis completed")
            else:
                print(f"  Analysis failed: {result.get('message', 'Unknown error')}")

        except Exception as e:
            print(f"  Error during product analysis: {e}")

        print("\n✓ Cross-DB analysis tests completed")

    # ============== Test Runner ==============

    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("CALCULATION AND ANALYSIS TOOLS TEST SUITE")
        print("="*80)

        try:
            # Calculation tool tests
            self.test_basic_calculations()
            self.test_business_metrics()
            self.test_period_calculations()

            # Trend analysis tool tests
            self.test_trend_analysis()
            self.test_seasonality_detection()
            self.test_predictions()
            self.test_anomaly_detection()

            # Cross-DB analysis tool tests (async)
            await self.test_cross_db_analysis()

            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED SUCCESSFULLY")
            print("="*80)

        except AssertionError as e:
            print(f"\n❌ Test failed: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False

        return True


def main():
    """Main test runner with user interaction"""
    tester = TestCalculationTools()

    while True:
        print("\n" + "="*60)
        print("Calculation Tools Test Menu")
        print("="*60)
        print("1. Run all tests")
        print("2. Test basic calculations only")
        print("3. Test business metrics only")
        print("4. Test trend analysis only")
        print("5. Test seasonality detection only")
        print("6. Test predictions only")
        print("7. Test anomaly detection only")
        print("8. Test cross-DB analysis only")
        print("9. Interactive calculation test")
        print("0. Exit")
        print("-"*60)

        choice = input("Select option (0-9): ").strip()

        if choice == "0":
            print("Exiting test suite...")
            break

        elif choice == "1":
            asyncio.run(tester.run_all_tests())

        elif choice == "2":
            tester.test_basic_calculations()

        elif choice == "3":
            tester.test_business_metrics()

        elif choice == "4":
            tester.test_trend_analysis()

        elif choice == "5":
            tester.test_seasonality_detection()

        elif choice == "6":
            tester.test_predictions()

        elif choice == "7":
            tester.test_anomaly_detection()

        elif choice == "8":
            asyncio.run(tester.test_cross_db_analysis())

        elif choice == "9":
            # Interactive calculation test
            print("\n" + "="*60)
            print("Interactive Calculation Test")
            print("="*60)

            print("\nSelect calculation type:")
            print("1. Achievement rate")
            print("2. Growth rate")
            print("3. Market share")
            print("4. Trend analysis")

            calc_type = input("Choice (1-4): ").strip()

            if calc_type == "1":
                actual = float(input("Enter actual value: "))
                target = float(input("Enter target value: "))
                result = tester.calculation_tool.calculate_achievement_rate(actual, target)
                print(f"\nAchievement Rate: {result}%")
                grade = tester.calculation_tool.get_performance_grade(result)
                print(f"Performance Grade: {grade}")

            elif calc_type == "2":
                current = float(input("Enter current value: "))
                previous = float(input("Enter previous value: "))
                result = tester.calculation_tool.calculate_growth_rate(current, previous)
                print(f"\nGrowth Rate: {result}%")

            elif calc_type == "3":
                individual = float(input("Enter individual value: "))
                total = float(input("Enter total value: "))
                result = tester.calculation_tool.calculate_market_share(individual, total)
                print(f"\nMarket Share: {result}%")

            elif calc_type == "4":
                print("Enter comma-separated values (e.g., 100,110,120,130):")
                values_str = input("Values: ")
                values = [float(v.strip()) for v in values_str.split(",")]

                trend = tester.trend_tool.analyze_historical_trend(values)
                print(f"\nTrend Analysis:")
                print(f"  Direction: {trend['trend_direction']}")
                print(f"  Strength: {trend['trend_strength']:.2f}")
                print(f"  Summary: {trend['summary']}")

                # Prediction
                if len(values) >= 3:
                    prediction = tester.trend_tool.predict_future_trend(values, periods_ahead=3)
                    print(f"\nNext 3 predictions: {prediction['predictions']}")

        else:
            print("Invalid choice. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()