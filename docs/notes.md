cd D:/ai-balance/macro-report/app/lambdas/fred_collector
python test_local.py
cd D:/ai-balance/macro-report/app
python .\main.py
npx next dev -H 0.0.0.0
curl http://localhost:8000/api/v1/macro/snapshots/latest