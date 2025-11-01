# 🏛️ MGNREGA District Data Portal

## Mahatma Gandhi National Rural Employment Guarantee Scheme - Performance Dashboard

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive, bilingual data visualization portal for tracking MGNREGA performance across Indian districts. Features government-standard design, educational tooltips, and real-time data from data.gov.in API.

## 📋 Table of Contents

- [Features](#-features)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🌐 Bilingual Interface
- Complete Hindi & English support throughout the application
- Educational tooltips with 3-tier explanations:
  - Simple Hindi (for low-literacy users)
  - Detailed Hindi (for educated users)
  - Technical English (for administrators and analysts)

### 📊 Data Visualization
- Interactive dashboards with key performance indicators
- District-wise performance metrics
- Time-series analysis of MGNREGA implementation
- Comparative analysis between different regions

### 🏗️ Technical Features
- FastAPI backend for high-performance data processing
- Streamlit-based responsive frontend
- Caching mechanism for improved performance
- Environment-based configuration
- Secure API endpoints

## 📁 Project Structure

```
mgnrega-portal/
├── backend/                  # Backend FastAPI application
│   ├── .env                 # Environment variables
│   ├── data_loader.py       # Data loading and processing
│   ├── geolocation.py       # Geographic data handling
│   ├── main.py              # Main FastAPI application
│   ├── mgnrega_cache.db     # Local cache database
│   └── requirements.txt     # Python dependencies
└── frontend/                # Frontend Streamlit application
    ├── .env                # Frontend environment variables
    ├── app.py              # Main Streamlit application
    ├── mgnrega_logo.jpg    # Application logo
    └── requirements.txt    # Frontend dependencies
```

## 🛠️ Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for version control)
- API key from data.gov.in (for real-time data)

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mgnrega-portal.git
   cd mgnrega-portal
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```bash
   cd ../frontend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

### Backend Configuration
Create a `.env` file in the `backend` directory with the following variables:
```
DATABASE_URL=sqlite:///./mgnrega_cache.db
DATA_GOV_API_KEY=your_data_gov_in_api_key
CACHE_TTL=86400  # Cache time-to-live in seconds
```

### Frontend Configuration
Create a `.env` file in the `frontend` directory with the following variables:
```
BACKEND_URL=http://localhost:8000
DEFAULT_LANGUAGE=hi  # 'hi' for Hindi, 'en' for English
```

## 🏃 Running the Application

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. In a new terminal, start the frontend:
   ```bash
   cd frontend
   streamlit run app.py
   ```

3. Open your browser and navigate to `http://localhost:8501`

## 📚 API Documentation

Once the backend server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🛠 Development

### Setting up a development environment
1. Install development dependencies:
   ```bash
   pip install black flake8 pytest
   ```

2. Run tests:
   ```bash
   cd backend
   pytest
   ```

3. Format code:
   ```bash
   black .
   ```

## 🐛 Troubleshooting

### Common Issues
- **API Connection Errors**: Ensure the backend server is running and the `BACKEND_URL` in the frontend `.env` file is correct.
- **Missing Dependencies**: Run `pip install -r requirements.txt` in both frontend and backend directories.
- **CORS Errors**: Make sure CORS is properly configured in the backend.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Data provided by [data.gov.in](https://data.gov.in/)
- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Streamlit](https://streamlit.io/)
- Icons by [Font Awesome](https://fontawesome.com/)
