# Poker HUD 3.01

OBS 아키텍처 기반 통합 포커 HUD 시스템

## 기능

- 실시간 포커 HUD 표시
- OCR 기반 카드 인식
- 플러그인 기반 모듈식 아키텍처
- PyQt6 기반 GUI 인터페이스
- 디자인 패턴 적용 (Factory, Observer, Strategy)

## 시스템 요구사항

- Python 3.8 이상
- Windows/Linux/macOS
- Tesseract OCR (텍스트 인식용)

## 설치 방법

### 1. GitHub에서 프로젝트 다운로드

```bash
git clone https://github.com/dahun0510-ui/poker-hud-project.git
cd poker-hud-project/myhud3.01
```

### 2. Python 가상환경 생성 (권장)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. 의존성 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. Tesseract OCR 설치

#### Windows:
1. [Tesseract 설치 페이지](https://github.com/UB-Mannheim/tesseract/wiki)에서 설치 파일 다운로드
2. 설치 시 "Additional script data"도 함께 설치
3. 환경변수 PATH에 Tesseract 설치 경로 추가

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
```

#### macOS:
```bash
brew install tesseract
```

## 실행 방법

### 기본 테스트 실행

플러그인 시스템이 정상 작동하는지 확인하는 간단한 테스트:

```bash
python run_test.py
```

성공 시 다음과 같은 출력이 나타납니다:
```
=== Poker HUD Application Test ===
✓ 모의 플러그인 임포트 성공
플러그인 시스템 초기화 중...
플러그인 시스템 시작 중...
MockHUDPlugin 초기화: {'enabled': True, 'priority': 1}
MockHUDPlugin 시작
✅ 플러그인 시스템 테스트 성공!
플러그인 시스템 중지 중...
MockHUDPlugin 중지
✅ 모든 테스트 완료!
```

### 메인 애플리케이션 실행

실제 GUI 애플리케이션 실행:

```bash
python main.py
```

## 프로젝트 구조

```
myhud3.01/
├── main.py                 # 메인 애플리케이션
├── run_test.py            # 테스트 실행 스크립트
├── config.py              # 설정 파일
├── poker_hud_manager.py   # HUD 관리자
├── requirements.txt       # 의존성 패키지 목록
├── plugins/               # 플러그인 시스템
│   ├── interfaces.py      # 플러그인 인터페이스
│   ├── plugin_manager.py  # 플러그인 관리자
│   ├── plugin_factory.py  # 플러그인 팩토리
│   └── mock_plugins.py    # 테스트용 모의 플러그인
├── control_panel/         # 컨트롤 패널 GUI
├── hud/                   # HUD 표시 컴포넌트
├── widgets/               # GUI 위젯들
├── async/                 # 비동기 처리
├── events/                # 이벤트 시스템
├── data/                  # 데이터 처리
└── patterns/              # 디자인 패턴 구현
```

## 사용법

1. 애플리케이션 실행 후 컨트롤 패널이 나타납니다
2. "스캔 시작" 버튼을 클릭하여 포커 테이블 스캔을 시작합니다
3. HUD가 자동으로 플레이어 정보를 표시합니다
4. 설정 탭에서 HUD 표시 옵션을 조정할 수 있습니다

## 문제 해결

### PyQt6 설치 오류
```bash
# Linux
sudo apt install python3-pyqt6 python3-pyqt6.qtwidgets

# macOS
brew install pyqt6
```

### Tesseract OCR 인식 오류
- Tesseract가 제대로 설치되었는지 확인
- 환경변수 PATH에 Tesseract 경로가 포함되어 있는지 확인
- `tesseract --version` 명령어로 설치 확인

### 모듈 임포트 오류
- Python 버전이 3.8 이상인지 확인
- 가상환경이 활성화되어 있는지 확인
- `pip install -r requirements.txt` 재실행

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 환영합니다.