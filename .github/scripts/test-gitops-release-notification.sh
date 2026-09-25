#!/usr/bin/env bash

set -euo pipefail

workflow_file=".github/workflows/deploy.yml"

grep -Fqx "  notify-infra:" "$workflow_file"
grep -Fq "needs: build" "$workflow_file"
grep -Fq "github.event_name == 'push'" "$workflow_file"
grep -Fq "github.ref_type == 'tag'" "$workflow_file"
grep -Fq "actions/create-github-app-token@v2" "$workflow_file"
grep -Fq "createDispatchEvent" "$workflow_file"
grep -Fq "K8S_INFRA_APP_ID" "$workflow_file"
grep -Fq "K8S_INFRA_APP_PRIVATE_KEY" "$workflow_file"

echo "GitOps release notification contract passed"
