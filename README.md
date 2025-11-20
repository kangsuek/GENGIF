# GIF 생성기 웹앱

두 개의 이미지를 업로드하여 부드럽게 움직이는 애니메이션 GIF를 생성하는 웹 애플리케이션입니다.

## 기능

- 두 이미지 간의 부드러운 전환 애니메이션 생성
- 프레임 수 조절 (5~30 프레임)
- 프레임 지속시간 조절 (20~500ms)
- 실시간 미리보기
- GIF 다운로드 기능
- 반응형 디자인 (모바일 지원)

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
python app.py
```

웹 브라우저에서 `http://localhost:5000` 으로 접속하세요.

## 사용 방법

1. 첫 번째 이미지 업로드 (왼쪽 박스 클릭)
2. 두 번째 이미지 업로드 (오른쪽 박스 클릭)
3. 원하는 설정 조정:
   - **프레임 수**: 높을수록 부드러운 애니메이션
   - **프레임 지속시간**: 낮을수록 빠른 애니메이션
4. "GIF 생성하기" 버튼 클릭
5. 생성된 GIF 다운로드

## 지원 파일 형식

- PNG
- JPG/JPEG
- GIF
- WebP

## 파일 구조

```
genGif/
├── app.py              # Flask 웹 애플리케이션
├── genGif.py           # GIF 생성 로직 (원본)
├── requirements.txt    # Python 패키지 의존성
├── templates/
│   └── index.html     # 메인 웹 페이지
├── uploads/           # 업로드된 이미지 (자동 생성)
└── outputs/           # 생성된 GIF (자동 생성)
```

## 참고사항

- 최대 파일 크기: 16MB
- 생성된 파일은 24시간 후 자동 삭제됩니다
- 두 이미지의 크기가 다른 경우, 첫 번째 이미지 크기에 맞춰 자동 조정됩니다

## GitHub에 업로드 및 배포하기

### 1. GitHub에 코드 업로드

```bash
# Git 저장소 초기화 (이미 완료된 경우 생략)
git init

# 모든 파일 추가
git add .

# 커밋 생성
git commit -m "Initial commit: GIF Generator Web App"

# GitHub에서 새 저장소 생성 후 원격 저장소 추가
git remote add origin https://github.com/your-username/your-repo-name.git

# GitHub에 푸시
git push -u origin main
```

### 2. 무료 배포 옵션

#### Option 1: Render.com (추천)

1. [Render.com](https://render.com)에 가입
2. "New +" 클릭 → "Web Service" 선택
3. GitHub 저장소 연결
4. 설정:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
5. "Create Web Service" 클릭

#### Option 2: Railway.app

1. [Railway.app](https://railway.app)에 가입
2. "New Project" → "Deploy from GitHub repo" 선택
3. 저장소 선택
4. 자동으로 배포됩니다 (Procfile 사용)

#### Option 3: PythonAnywhere

1. [PythonAnywhere](https://www.pythonanywhere.com)에 가입
2. "Web" 탭 → "Add a new web app" 선택
3. Flask 선택
4. 코드 업로드 및 실행

### 3. 환경 변수 설정

배포 플랫폼에서 다음 환경 변수를 설정할 수 있습니다:

- `PORT`: 앱이 실행될 포트 (기본값: 8080)

### 4. 주의사항

- **무료 플랜 제한**: 대부분의 무료 플랫폼은 일정 시간 비활성화 시 슬립 모드로 전환됩니다
- **메모리 제한**: AI 배경 제거 기능(rembg)은 메모리를 많이 사용하므로, 무료 플랫폼에서는 제한될 수 있습니다
- **파일 저장**: uploads/ 및 outputs/ 폴더는 임시 스토리지를 사용하므로, 재시작 시 삭제될 수 있습니다
