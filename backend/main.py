from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import httpx
import sqlite3
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
import logging
from collections import defaultdict
import os
from dotenv import load_dotenv  # Add this import

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
DB_PATH = os.getenv("DB_PATH", "mgnrega_cache.db")  # Default if not in .env

# Validate critical configuration
if not API_KEY:
    raise ValueError("API_KEY not found in environment variables. Please check .env file")
if not BASE_URL:
    raise ValueError("BASE_URL not found in environment variables. Please check .env file")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log configuration (without exposing full API key)
logger.info(f"Configuration loaded:")
logger.info(f"  BASE_URL: {BASE_URL}")
logger.info(f"  API_KEY: {API_KEY[:10]}...{API_KEY[-10:]}")  # Only show first/last 10 chars
logger.info(f"  DB_PATH: {DB_PATH}")

# Initialize FastAPI app
app = FastAPI(
    title="MGNREGA Data Portal API",
    description="Backend API for MGNREGA District Performance Data",
    version="1.0.0"
)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 50
RATE_LIMIT_WINDOW = 60

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Rate limiter
class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)

    async def check_limit(self, key: str = "global"):
        now = datetime.now()
        self.requests[key] = [req_time for req_time in self.requests[key]
                              if now - req_time < timedelta(seconds=RATE_LIMIT_WINDOW)]

        if len(self.requests[key]) >= RATE_LIMIT_REQUESTS:
            return False

        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


# Database initialization
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mgnrega_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fin_year TEXT,
            month TEXT,
            state_code TEXT,
            state_name TEXT,
            district_code TEXT,
            district_name TEXT,
            approved_labour_budget INTEGER,
            average_wage_rate INTEGER,
            average_days_employment INTEGER,
            differently_abled_worked INTEGER,
            material_skilled_wages INTEGER,
            completed_works INTEGER,
            gps_nil_exp INTEGER,
            ongoing_works INTEGER,
            persondays_central_liability INTEGER,
            sc_persondays INTEGER,
            sc_workers INTEGER,
            st_persondays INTEGER,
            st_workers INTEGER,
            total_adm_expenditure INTEGER,
            total_exp INTEGER,
            total_households_worked INTEGER,
            total_individuals_worked INTEGER,
            total_active_job_cards INTEGER,
            total_active_workers INTEGER,
            total_hhs_100days INTEGER,
            total_jobcards_issued INTEGER,
            total_workers INTEGER,
            total_works_takenup INTEGER,
            wages INTEGER,
            women_persondays INTEGER,
            percent_category_b INTEGER,
            percent_agri_allied INTEGER,
            percent_nrm INTEGER,
            percent_payments_15days INTEGER,
            remarks TEXT,
            last_updated TIMESTAMP,
            UNIQUE(fin_year, month, state_code, district_code)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_state_district 
        ON mgnrega_data(state_name, district_name, fin_year)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_year_month 
        ON mgnrega_data(fin_year, month)
    ''')

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Application shutting down")


app = FastAPI(title="MGNREGA API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class DistrictData(BaseModel):
    fin_year: str
    month: str
    state_name: str
    district_name: str
    total_households_worked: int
    total_individuals_worked: int
    average_days_employment: int
    average_wage_rate: int
    total_exp: int
    wages: int
    women_persondays: int
    sc_persondays: int
    st_persondays: int
    completed_works: int
    ongoing_works: int


class DistrictSummary(BaseModel):
    district_name: str
    state_name: str
    latest_month: str
    total_households: int
    total_expenditure: int
    avg_wage_rate: int
    women_participation_pct: float
    completion_rate: float


# Helper functions
async def fetch_from_api(state_name: str, fin_year: str, offset: int = 0, limit: int = 1000):
    """Fetch data from data.gov.in API with retry logic"""

    if not await rate_limiter.check_limit():
        logger.warning("Rate limit reached, using cached data")
        return None

    params = {
        "api-key": API_KEY,
        "format": "json",
        "offset": offset,
        "limit": limit,
        "filters[state_name]": state_name.upper(),
        "filters[fin_year]": fin_year
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("records", [])
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            return None


def save_to_cache(records: List[Dict]):
    """Save API records to local database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for record in records:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO mgnrega_data VALUES (
                    NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
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
        except Exception as e:
            logger.error(f"Error saving record: {e}")
            continue

    conn.commit()
    conn.close()


def get_from_cache(state_name: str, district_name: Optional[str] = None,
                   fin_year: Optional[str] = None):
    """Retrieve data from local cache with flexible year matching"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM mgnrega_data WHERE state_name = ?"
    params = [state_name.upper()]

    if district_name:
        query += " AND district_name = ?"
        params.append(district_name.upper())

    if fin_year:
        # Flexible year matching - handles "2025", "2024-2025", etc.
        query += " AND (fin_year = ? OR fin_year LIKE ? OR fin_year LIKE ?)"
        params.append(fin_year)
        params.append(f"{fin_year}-%")  # Matches "2025-*"
        params.append(f"%-{fin_year}")  # Matches "*-2025"

    query += " ORDER BY fin_year DESC, month DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# API Endpoints

@app.get("/")
async def root():
    return {"message": "MGNREGA API - Production Ready", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/api/states")
async def get_states():
    """Get list of available states"""
    states = [
        {"code": "09", "name": "UTTAR PRADESH"},
        {"code": "23", "name": "MADHYA PRADESH"},
        {"code": "20", "name": "JHARKHAND"},
        {"code": "10", "name": "BIHAR"},
        {"code": "22", "name": "CHHATTISGARH"}
    ]
    return {"states": states}


@app.get("/api/districts/{state_name}")
async def get_districts(state_name: str):
    """Get districts for a given state"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT district_name, district_code 
        FROM mgnrega_data 
        WHERE state_name = ?
        ORDER BY district_name
    ''', (state_name.upper(),))

    districts = [{"name": row[0], "code": row[1]} for row in cursor.fetchall()]
    conn.close()

    if not districts:
        records = await fetch_from_api(state_name, "2025")
        if records:
            save_to_cache(records)
            return await get_districts(state_name)

    return {"districts": districts}


@app.get("/api/all-districts")
async def get_all_districts():
    """Get overview of all districts with latest data"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            state_name,
            district_name,
            MAX(fin_year) as latest_year,
            MAX(month) as latest_month,
            SUM(total_households_worked) as total_households,
            AVG(average_wage_rate) as avg_wage,
            SUM(total_exp) as total_expenditure
        FROM mgnrega_data
        GROUP BY state_name, district_name
        ORDER BY state_name, district_name
    ''')

    rows = cursor.fetchall()
    conn.close()

    districts = []
    for row in rows:
        districts.append({
            "state": row["state_name"],
            "district": row["district_name"],
            "latest_year": row["latest_year"],
            "latest_month": row["latest_month"],
            "total_households": row["total_households"] or 0,
            "avg_wage": int(row["avg_wage"]) if row["avg_wage"] else 0,
            "total_expenditure": row["total_expenditure"] or 0
        })

    return {"count": len(districts), "districts": districts}


@app.get("/api/blocks/{state_name}/{district_name}")
async def get_blocks(state_name: str, district_name: str):
    """Get blocks/GPs for a given state and district"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Note: Current database doesn't have block/GP level data
    # This returns unique combinations from available data
    cursor.execute('''
        SELECT DISTINCT month 
        FROM mgnrega_data 
        WHERE state_name = ? AND district_name = ?
        ORDER BY month
    ''', (state_name.upper(), district_name.upper()))

    # For now, return months as proxy for blocks
    # In production, this would query actual block/GP data
    months = [{"name": f"All Blocks", "code": "ALL"}]
    for row in cursor.fetchall():
        if row[0]:
            months.append({"name": row[0], "code": row[0]})

    conn.close()

    return {"blocks": months}


@app.get("/api/data/{state_name}/{district_name}")
async def get_district_data(
        state_name: str,
        district_name: str,
        fin_year: Optional[str] = "2025",
        background_tasks: BackgroundTasks = None
):
    """Get detailed data for a specific district"""

    cached_data = get_from_cache(state_name, district_name, fin_year)

    if not cached_data or len(cached_data) == 0:
        records = await fetch_from_api(state_name, fin_year)
        if records:
            save_to_cache(records)
            cached_data = get_from_cache(state_name, district_name, fin_year)

    if not cached_data:
        raise HTTPException(status_code=404, detail="No data found for this district")

    processed_data = []
    for row in cached_data:
        processed_data.append({
            "month": row.get("month"),
            "fin_year": row.get("fin_year"),
            "households_worked": row.get("total_households_worked", 0),
            "individuals_worked": row.get("total_individuals_worked", 0),
            "avg_days_employment": row.get("average_days_employment", 0),
            "avg_wage_rate": row.get("average_wage_rate", 0),
            "total_expenditure": row.get("total_exp", 0),
            "wages": row.get("wages", 0),
            "women_persondays": row.get("women_persondays", 0),
            "sc_persondays": row.get("sc_persondays", 0),
            "st_persondays": row.get("st_persondays", 0),
            "completed_works": row.get("completed_works", 0),
            "ongoing_works": row.get("ongoing_works", 0),
            "hhs_100_days": row.get("total_hhs_100days", 0)
        })

    return {
        "state": state_name,
        "district": district_name,
        "data": processed_data
    }


@app.get("/api/summary/{state_name}/{district_name}")
async def get_district_summary(state_name: str, district_name: str):
    """Get summary statistics for a district"""

    cached_data = get_from_cache(state_name, district_name)

    if not cached_data:
        records = await fetch_from_api(state_name, "2025")
        if records:
            save_to_cache(records)
            cached_data = get_from_cache(state_name, district_name)

    if not cached_data:
        raise HTTPException(status_code=404, detail="No data found")

    latest = cached_data[0]

    total_persondays = (
            latest.get("sc_persondays", 0) +
            latest.get("st_persondays", 0) +
            latest.get("women_persondays", 0)
    )

    women_pct = (
        (latest.get("women_persondays", 0) / total_persondays * 100)
        if total_persondays > 0 else 0
    )

    total_works = latest.get("completed_works", 0) + latest.get("ongoing_works", 0)
    completion_rate = (
        (latest.get("completed_works", 0) / total_works * 100)
        if total_works > 0 else 0
    )

    return {
        "district_name": district_name,
        "state_name": state_name,
        "latest_month": latest.get("month"),
        "latest_year": latest.get("fin_year"),
        "total_households": latest.get("total_households_worked", 0),
        "total_expenditure": latest.get("total_exp", 0),
        "avg_wage_rate": latest.get("average_wage_rate", 0),
        "avg_days_employment": latest.get("average_days_employment", 0),
        "women_participation_pct": round(women_pct, 2),
        "completion_rate": round(completion_rate, 2),
        "completed_works": latest.get("completed_works", 0),
        "ongoing_works": latest.get("ongoing_works", 0)
    }


@app.post("/api/sync/{state_name}")
async def sync_state_data(state_name: str, background_tasks: BackgroundTasks):
    """Manually trigger data sync for a state"""

    async def sync_task():
        for year in ["2024", "2025"]:
            records = await fetch_from_api(state_name, year)
            if records:
                save_to_cache(records)
                logger.info(f"Synced {len(records)} records for {state_name} - {year}")
            await asyncio.sleep(2)

    background_tasks.add_task(sync_task)

    return {"message": f"Sync initiated for {state_name}"}


@app.get("/api/compare")
async def compare_districts(
        state_name: str,
        district1: str,
        district2: str,
        fin_year: str = "2025"
):
    """Compare two districts"""

    data1 = get_from_cache(state_name, district1, fin_year)
    data2 = get_from_cache(state_name, district2, fin_year)

    if not data1 or not data2:
        raise HTTPException(status_code=404, detail="Data not found for comparison")

    return {
        "district1": {
            "name": district1,
            "data": data1[0] if data1 else {}
        },
        "district2": {
            "name": district2,
            "data": data2[0] if data2 else {}
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
