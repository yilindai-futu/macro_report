# Install
winget install --id GitHub.cli
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

git config user.name "yilindai-futu"
git config user.email "yilindai@futunn.com"

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
