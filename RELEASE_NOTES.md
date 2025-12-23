# 땅굴파기 게임 v1.0 - 배포 버전

## 🎮 빌드 정보

- **빌드 날짜**: 2025-12-18
- **버전**: 1.0.0
- **플랫폼**: Windows 64-bit
- **실행 파일**: `TunnelingGame.exe`
- **파일 크기**: ~50MB (단일 실행 파일)

## 📦 배포 파일

```
dist/
└── TunnelingGame.exe  ← 실행 파일 (Python 환경 불필요)
```

## ✅ 빌드 테스트 체크리스트

- [x] PyInstaller 설치 완료
- [x] .exe 파일 빌드 성공
- [x] 단일 파일로 패키징
- [x] 콘솔 창 숨김 (--noconsole)
- [ ] 실행 파일 동작 테스트
- [ ] 다른 PC에서 실행 테스트

## 🚀 배포 방법

### 1. 간단 배포 (개인/친구)
```
dist/TunnelingGame.exe 파일만 전달
→ 받는 사람은 더블클릭으로 바로 실행!
```

### 2. 전문 배포 (공개 배포)
```
1. 아이콘 추가
2. 디지털 서명
3. 설치 프로그램 제작 (NSIS, Inno Setup)
4. README, 라이선스 파일 포함
```

## 📝 사용자를 위한 설명

### 실행 방법
1. `TunnelingGame.exe` 파일을 더블클릭
2. Python 설치 불필요
3. 게임 실행!

### 시스템 요구사항
- **OS**: Windows 10/11 (64-bit)
- **메모리**: 최소 100MB RAM
- **용량**: 약 50MB 디스크 공간
- **Python**: 불필요 (실행 파일에 포함됨)

## 🔧 빌드 명령어

```bash
# 빌드 실행
pyinstaller --clean --onefile --noconsole --name "TunnelingGame" tunneling_game.py

# 결과물
dist/TunnelingGame.exe
```

## 📊 빌드 옵션 설명

| 옵션 | 설명 |
|-----|------|
| `--onefile` | 단일 실행 파일로 패키징 |
| `--noconsole` | 콘솔 창 숨김 (GUI 전용) |
| `--name` | 출력 파일 이름 지정 |
| `--clean` | 이전 빌드 캐시 제거 |

## 🎨 향후 개선사항

### 배포 품질 향상
1. **아이콘 추가**
   ```bash
   pyinstaller --icon=game_icon.ico ...
   ```

2. **버전 정보 추가**
   - FileVersion
   - ProductName
   - Copyright

3. **설치 프로그램 제작**
   - Inno Setup
   - NSIS
   - 바탕화면 바로가기
   - 시작 메뉴 등록

### 배포 플랫폼
- **itch.io**: 인디 게임 플랫폼
- **Steam**: 상용 배포
- **GitHub Releases**: 오픈소스 배포
- **Google Drive**: 간단한 공유

## 🐛 알려진 이슈

- ❌ 첫 실행 시 Windows Defender 경고 가능 (서명되지 않은 앱)
  - 해결: "추가 정보" → "실행" 클릭
- ❌ 안티바이러스가 차단할 수 있음
  - 해결: 예외 목록에 추가

## 📞 지원

문제가 발생하면:
1. `ranking.json` 파일 삭제 후 재실행
2. 관리자 권한으로 실행
3. Windows 방화벽/보안 설정 확인

---

**빌드 도구**: PyInstaller 6.17.0
**Python 버전**: 3.14.0
**Pygame 버전**: pygame-ce 2.5.6



