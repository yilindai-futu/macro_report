$reposList = @(
    "research-report",
    "ai-compliance",
    "meerkat",
    "mineru",
    "infra",
    "bge-m3",
    "app-onboarding",
    "app-registry",
    "ideclare",
    "app-template",
    "shared-middleware",
    "request-recorder",
    "test-app",
    "handbook",
    "echopoc",
    "futu-llm-proxy",
    "bl-dev",
    "bl-truststore"
)
$org = "ai-balance"
foreach($r in $reposList){
    $out = Join-Path $PWD $r
    if(Test-Path $out) {Write-Host "跳过 $r";continue}
    git clone "git@github.com:$org/$r.git" $out
}