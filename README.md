# 장전 매크로 대시보드

매일 아침 1번, 환율·금리·원자재·증시 지표를 자동으로 모아서 보여주는 개인용 웹 대시보드입니다.
출처: Stooq.com (무료, 가입/API 키 불필요, 약 15~20분 지연 데이터).

## 무엇이 들어있나요

- `scripts/fetch_data.py` — Stooq에서 26개 지표를 가져와 `docs/data.json`에 저장하는 스크립트
- `.github/workflows/daily-update.yml` — 매일 자동으로 위 스크립트를 실행하는 GitHub Actions 설정 (한국시간 오전 7시)
- `docs/index.html` — 실제로 보게 될 대시보드 화면 (GitHub Pages로 호스팅)

## 설치 방법 (한 번만 하면 됩니다)

### 1. GitHub 계정 만들기
이미 있으면 건너뛰세요. https://github.com/signup

### 2. 새 저장소(repository) 만들기
- GitHub 우측 상단 `+` → `New repository`
- 이름: `macro-dashboard` (원하는 이름으로 가능)
- **Public으로 설정**해야 GitHub Pages 무료 호스팅이 됩니다. (Private도 가능하지만 유료 플랜 필요)
- "Create repository" 클릭

> Public이라는 게 걸리신다면 — 저장소 코드는 누구나 볼 수 있지만, 어차피 시장 지표일 뿐 개인정보는 없습니다. URL을 직접 공유하지 않으면 사실상 본인만 보는 페이지입니다.

### 3. 이 폴더의 파일들 업로드
저장소 페이지에서 `Add file` → `Upload files`로 이 프로젝트의 모든 파일(폴더 구조 그대로)을 끌어다 놓고 커밋합니다.
(또는 git을 다룰 줄 아시면 `git clone` 받은 폴더에 복사 후 `git add . && git commit -m "init" && git push`)

### 4. GitHub Actions 권한 설정
- 저장소의 `Settings` → `Actions` → `General`
- "Workflow permissions"에서 **"Read and write permissions"** 선택 → Save
(이게 없으면 Actions가 데이터를 갱신해도 저장(commit)을 못 합니다.)

### 5. GitHub Pages 켜기
- 저장소의 `Settings` → `Pages`
- "Build and deployment" → Source: `Deploy from a branch`
- Branch: `main` (또는 `master`), 폴더: `/docs` 선택 → Save
- 몇 분 후 `https://[내아이디].github.io/macro-dashboard/` 형태의 URL이 생성됩니다. 이 URL을 북마크하세요.

### 6. 첫 데이터 수집 수동 실행
- 저장소의 `Actions` 탭 → 좌측 "매크로 대시보드 일일 갱신" 클릭
- 우측의 `Run workflow` 버튼으로 한 번 수동 실행 (다음날부터는 자동으로 매일 실행됩니다)
- 1~2분 후 완료되면 `docs/data.json`이 실제 데이터로 갱신됩니다

이후로는 매일 한국시간 오전 7시경 자동으로 갱신되고, 북마크해둔 페이지를 열면 그날의 숫자를 볼 수 있습니다.

## 데이터가 일부 N/A로 보인다면

Stooq의 티커 코드 중 일부(특히 한국/독일 국채금리, 유로스톡스50, 대만지수)는 정확성을 100% 보장하지 못했습니다.
`scripts/fetch_data.py` 상단의 `ITEMS` 리스트에서 해당 항목의 티커를 Stooq 사이트(https://stooq.com)에서 직접 검색해 올바른 코드로 교체하면 됩니다.

## 갱신 시간/주기를 바꾸고 싶다면

`.github/workflows/daily-update.yml`의 `cron: '0 22 * * *'` 부분을 수정하세요.
(cron은 UTC 기준이라 한국시간 -9시간으로 계산합니다. 예: 한국시간 오전 8시 = UTC 전날 23시 = `'0 23 * * *'`)
