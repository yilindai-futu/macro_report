#!/bin/bash

repos_list=(
    "research-report"
    "ai-compliance"
    "meerkat"
    "mineru"
    "infra"
    "bge-m3"
    "app-onboarding"
    "app-registry"
    "ideclare"
    "app-template"
    "shared-middleware"
    "request-recorder"
    "test-app"
    "handbook"
    "echopoc"
    "futu-llm-proxy"
    "bl-dev"
    "bl-truststore"
)

org="ai-balance"

for r in "${repos_list[@]}"; do
    out="$(pwd)/$r"
    if [ -d "$out" ]; then
        echo "跳过 $r"
        continue
    fi
    git clone "git@github.com:$org/$r.git" "$out"
done