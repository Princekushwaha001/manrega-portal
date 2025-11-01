import asyncio
import httpx
from datetime import datetime
import sqlite3

API_KEY = "579b464db66ec23bdd000001bfdb36c33cec4a6b700503cae473ca92"
BASE_URL = "https://api.data.gov.in/resource/ee03643a-ee4c-48c2-ac30-9f2ff26ab722"
DB_PATH = "mgnrega_cache.db"


async def fetch_and_cache_state_data(state_name: str, year: str = "2025"):
    """Fetch data from API and cache it"""
    print(f"Fetching data for {state_name} - {year}...")

    # Fixed filter syntax - no nested brackets for fin_year
    params = {
        "api-key": API_KEY,
        "format": "json",
        "offset": 0,
        "limit": 10000,
        "filters[state_name]": state_name.upper()
    }

    # Try without year filter first to see what data is available
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # First, try to get ANY data for the state
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])

            if records:
                # Filter by year in post-processing
                year_filtered_records = [r for r in records if r.get("fin_year") == year]

                if year_filtered_records:
                    save_to_cache(year_filtered_records)
                    print(f"✓ Cached {len(year_filtered_records)} records for {state_name} - {year}")
                    return len(year_filtered_records)
                else:
                    # If no records for specific year, save all and show what years we have
                    available_years = set(r.get("fin_year") for r in records if r.get("fin_year"))
                    print(f"⚠ No records for {year}, but found data for years: {available_years}")
                    save_to_cache(records)
                    return len(records)
            else:
                print(f"✗ No records found for {state_name}")
                # Print the API response for debugging
                print(f"API Response: {data}")
                return 0

        except Exception as e:
            print(f"✗ Error fetching {state_name}: {e}")
            return 0


def save_to_cache(records):
    """Save records to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    saved_count = 0
    for record in records:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO mgnrega_data (
                    fin_year, month, state_code, state_name, district_code, district_name,
                    approved_labour_budget, average_wage_rate, average_days_employment,
                    differently_abled_worked, material_skilled_wages, completed_works,
                    gps_nil_exp, ongoing_works, persondays_central_liability,
                    sc_persondays, sc_workers, st_persondays, st_workers,
                    total_adm_expenditure, total_exp, total_households_worked,
                    total_individuals_worked, total_active_job_cards, total_active_workers,
                    total_hhs_100days, total_jobcards_issued, total_workers,
                    total_works_takenup, wages, women_persondays, percent_category_b,
                    percent_agri_allied, percent_nrm, percent_payments_15days,
                    remarks, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get("fin_year"),
                record.get("month"),
                record.get("state_code"),
                record.get("state_name"),
                record.get("district_code"),
                record.get("district_name"),
                record.get("Approved_Labour_Budget", 0),
                record.get("Average_Wage_rate_per_day_per_person", 0),
                record.get("Average_days_of_employment_provided_per_Household", 0),
                record.get("Differently_abled_persons_worked", 0),
                record.get("Material_and_skilled_Wages", 0),
                record.get("Number_of_Completed_Works", 0),
                record.get("Number_of_GPs_with_NIL_exp", 0),
                record.get("Number_of_Ongoing_Works", 0),
                record.get("Persondays_of_Central_Liability_so_far", 0),
                record.get("SC_persondays", 0),
                record.get("SC_workers_against_active_workers", 0),
                record.get("ST_persondays", 0),
                record.get("ST_workers_against_active_workers", 0),
                record.get("Total_Adm_Expenditure", 0),
                record.get("Total_Exp", 0),
                record.get("Total_Households_Worked", 0),
                record.get("Total_Individuals_Worked", 0),
                record.get("Total_No_of_Active_Job_Cards", 0),
                record.get("Total_No_of_Active_Workers", 0),
                record.get("Total_No_of_HHs_completed_100_Days_of_Wage_Employment", 0),
                record.get("Total_No_of_JobCards_issued", 0),
                record.get("Total_No_of_Workers", 0),
                record.get("Total_No_of_Works_Takenup", 0),
                record.get("Wages", 0),
                record.get("Women_Persondays", 0),
                record.get("percent_of_Category_B_Works", 0),
                record.get("percent_of_Expenditure_on_Agriculture_Allied_Works", 0),
                record.get("percent_of_NRM_Expenditure", 0),
                record.get("percentage_payments_gererated_within_15_days", 0),
                record.get("Remarks", ""),
                datetime.now()
            ))
            saved_count += 1
        except Exception as e:
            print(f"Error saving record: {e}")
            continue

    conn.commit()
    conn.close()
    print(f"  Saved {saved_count} records to database")


async def test_api_connection():
    """Test the API with a simple request"""
    print("\n" + "=" * 60)
    print("Testing API connection...")
    print("=" * 60)

    params = {
        "api-key": API_KEY,
        "format": "json",
        "offset": 0,
        "limit": 5  # Just get a few records to test
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            print(f"✓ API is responding!")
            print(f"Total records available: {data.get('total', 'Unknown')}")
            print(f"Records returned: {data.get('count', 0)}")

            if data.get('records'):
                sample_record = data['records'][0]
                print(f"\nSample record:")
                print(f"  State: {sample_record.get('state_name')}")
                print(f"  District: {sample_record.get('district_name')}")
                print(f"  Year: {sample_record.get('fin_year')}")
                print(f"  Month: {sample_record.get('month')}")

                # Show all available years
                all_years = set(r.get('fin_year') for r in data.get('records', []) if r.get('fin_year'))
                print(f"\nAvailable years in sample: {all_years}")
            else:
                print("⚠ No records returned")
                print(f"Response: {data}")

            return True

        except Exception as e:
            print(f"✗ API connection failed: {e}")
            return False


async def load_initial_data():
    """Load data for major states"""

    # First test API connection
    api_working = await test_api_connection()

    if not api_working:
        print("\n" + "!" * 60)
        print("API test failed. Cannot proceed with data loading.")
        print("!" * 60)
        return

    states = ["UTTAR PRADESH", "MADHYA PRADESH", "BIHAR", "JHARKHAND", "CHHATTISGARH"]

    print("\n" + "=" * 60)
    print("Loading initial MGNREGA data...")
    print("=" * 60)

    total_records = 0
    for state in states:
        count = await fetch_and_cache_state_data(state, "2024-2025")  # Try different year format
        total_records += count
        await asyncio.sleep(2)

    print("=" * 60)
    print(f"Data loading complete! Total records cached: {total_records}")
    print("=" * 60)

    # Show what we have in database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mgnrega_data")
    db_count = cursor.fetchone()[0]

    cursor.execute("SELECT DISTINCT state_name FROM mgnrega_data")
    states_in_db = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT fin_year FROM mgnrega_data")
    years_in_db = [row[0] for row in cursor.fetchall()]

    conn.close()

    print(f"\nDatabase Summary:")
    print(f"  Total records: {db_count}")
    print(f"  States: {states_in_db}")
    print(f"  Years: {years_in_db}")


if __name__ == "__main__":
    asyncio.run(load_initial_data())
