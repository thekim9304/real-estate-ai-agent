# Docker 기반 데이터 분석 프로젝트 템플릿

## 폴더 및 파일 구조

- **`/workspace`**: **(메인 작업 공간)** Jupyter notebok
- **`/src`**: **(소스 코드)** 여러 노트북에서 공통으로 사용하는 함수나 클래스를 `.py` 모듈로 만들어 관리하는 곳
- **`/docs`**: 프로젝트의 기획, 아키텍처, 최종 보고서 등 상세 문서를 저장하는 곳
- **`/jupyter_config`**: JupyterLab의 UI 테마, 폰트 크기 등 초기 설정을 관리하는 곳

---

## 시작하기

### 사전 요구사항

- [Docker](https://www.docker.com/get-started) 설치

### 실행 순서

1.  **라이브러리 추가**
    `requirements.txt` 파일에 필요한 Python 라이브러리를 추가합니다.

2.  **컨테이너 실행**
    터미널에서 아래 명령어를 입력하여 Docker 컨테이너를 빌드하고 실행합니다.
    ```bash
    docker-compose up --build -d
    ```

3.  **JupyterLab 접속**
    웹 브라우저를 열고 `http://localhost:8888` 주소로 접속합니다.


작업을 마친 후 컨테이너를 종료
```bash
docker-compose down
