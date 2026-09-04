# Install
winget install --id GitHub.cli
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

git config user.name "yilindai-futu"
git config user.email "yilindai@futunn.com"

[System.Environment]::SetEnvironmentVariable("FRED_API_KEY", "a9a70fc1cbe4dcc8cdafe9b070f347cc", "User")
$env:FRED_API_KEY = "a9a70fc1cbe4dcc8cdafe9b070f347cc"
echo $env:FRED_API_KEY

uv run python run_script.py macro
uv run python main.py 

# Login
aws sso login --profile balance-dev

# Activate env
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\pyskill\Scripts\Activate.ps1
ssh-add C:\Users\Administrator\.ssh\id_ed25519 
aws sso login --profile balance-dev;ssh research-dev
<!-- aws sso login --profile balance-dev-debug -->

aws ec2 describe-instances --filters "Name=tag:Name,Values=meerkat-dev-server" "Name=instance-state-name,Values=running" --query "Reservations[0].Instances[0].InstanceId" --output text --profile balance-dev-debug

<!-- from walker -->
aws ssm start-session --target i-0d765c31d12d25669 --region ap-east-1 --profile balance-dev-debug
<!-- from wang zong -->
aws ssm start-session --target i-051fec612e2c14b8e --region ap-east-1 --profile balance-dev

# RUN App
cd D:/ai-balance/macro_report
cd app/lambdas/fred_collector
python test_local.py
cd D:/ai-balance/macro_report
cd app
python main.py
curl http://localhost:8000/api/v1/macro/snapshots/latest

cd D:/ai-balance/macro_report
cd frontend
npx next dev -H 0.0.0.0

# 开发Dev
git checkout dev
git pull origin dev
git checkout -b feature/fred_ism_data_pipeline

cd app
PG_HOST=127.0.0.1 PG_PORT=15432 PG_SSLMODE=disable PG_PASSWORD=x FUTU_PG_DBNAME=futu_data
uv run python run_script.py sync_notice_file
