#!/bin/bash
echo ""
echo "🌾  FarmRent Nigeria – Starting Application"
echo "==========================================="
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q --break-system-packages

echo ""
echo "🚀 Starting server at http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""
echo "📖 Pages:"
echo "   Home:              http://localhost:8000/"
echo "   Marketplace:       http://localhost:8000/marketplace"
echo "   Auth:              http://localhost:8000/auth"
echo "   Farmer Dashboard:  http://localhost:8000/farmer-dashboard"
echo "   Company Dashboard: http://localhost:8000/company-dashboard"
echo "   API Docs:          http://localhost:8000/docs"
echo ""
echo "🔑 Demo Login:"
echo "   Company: agromech@demo.com / demo123"
echo "   Farmer:  Create new account via Sign Up"
echo ""

cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
