# YouTube PO Token Provider Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let Comandita download public YouTube videos subject to its existing ten-minute limit without using account cookies.

**Architecture:** A pinned upstream BgUtils provider runs as a second, internal-only Kubernetes Deployment. The bot installs its yt-dlp plugin and enables it only through an explicit service URL, while the GitHub workflow publishes both immutable images from one commit.

**Tech Stack:** Python 3.14, Node.js 22, yt-dlp, yt-dlp-ejs 0.8.0, bgutil-ytdlp-pot-provider 1.3.1, Docker, GitHub Actions, Helm, Flux.

### Task 1: Configure yt-dlp to use an optional internal provider

**Files:**
- Modify: `requirements/pro.txt`
- Modify: `media_downloads/downloader.py`
- Modify: `media_downloads/handler.py`
- Test: `tests/test_media_downloader.py`
- Test: `tests/test_media_settings.py`

**Step 1:** Write failing tests for parsing `YOUTUBE_POT_PROVIDER_URL`, enabling the mweb client and provider base URL only for YouTube, and leaving X/Instagram options unchanged.

**Step 2:** Run `make build_dev && docker run --rm --env-file .env comanditabot:latest python -m pytest -o addopts='' tests/test_media_downloader.py tests/test_media_settings.py -q`; expect failure.

**Step 3:** Add the pinned plugin and EJS package, copy Node.js 22 into the runtime image, extend `MediaSettings`, and pass the optional URL to `YtDlpExtractor`. Configure `youtube:player_client=mweb`, `youtubepot-bgutilhttp:base_url=<internal URL>`, and the Node JavaScript runtime only for public YouTube links.

**Step 4:** Rerun the focused tests; expect pass. Commit `feat: configure YouTube PO Token provider`.

### Task 2: Add the second image and build it in GitHub Actions

**Files:**
- Create: `youtube-pot-provider/Dockerfile`
- Modify: `.github/workflows/deploy.yml`
- Test: `tests/test_container_contract.py`

**Step 1:** Add failing static tests requiring the provider Dockerfile, pinned upstream version, and a workflow matrix that publishes both registry repositories with `GITHUB_SHA`.

**Step 2:** Run the focused container test; expect failure.

**Step 3:** Create a minimal provider Dockerfile based on the pinned Node flavour of the upstream image. Convert the build job to a two-entry matrix with image repository, context, and app-only build arguments.

**Step 4:** Build the provider image locally and rerun the focused test; expect pass. Commit `build: publish YouTube PO Token provider image`.

### Task 3: Deploy the internal provider through the existing Helm chart

**Files:**
- Modify: `helm-charts/comanditabot/values.yaml` in `k8s-infra`
- Create: `helm-charts/comanditabot/templates/youtube-pot-provider-deployment.yaml` in `k8s-infra`
- Create: `helm-charts/comanditabot/templates/youtube-pot-provider-service.yaml` in `k8s-infra`
- Modify: `clusters/ovh-k3s/apps/comanditabot.yaml` in `k8s-infra`

**Step 1:** Add a render assertion or inspect a Helm template command that fails before the provider resources exist.

**Step 2:** Add provider image, resources, secure contexts, Deployment, ClusterIP Service, and `YOUTUBE_POT_PROVIDER_URL` pointing to the Service. Use the same immutable source SHA for both images.

**Step 3:** Run `helm lint helm-charts/comanditabot`, render with production values, inspect the two image references and confirm no Ingress is added.

**Step 4:** Commit the GitOps deployment update separately.

### Task 4: Verify, publish, and test in production

**Step 1:** Run `make test`, `ruff check`, Docker builds for both contexts, and `git diff --check`.

**Step 2:** Push the source branch, dispatch the image workflow, and confirm it pushes both SHA tags.

**Step 3:** Update the GitOps image tag, open and merge the scoped PR, and request Flux reconciliation by annotation only.

**Step 4:** Confirm both Deployments and the HelmRelease are ready. From the bot pod, run yt-dlp metadata extraction for the previously failing Short and verify its verbose output lists the `bgutil:http` provider before testing attachment delivery through Telegram.
