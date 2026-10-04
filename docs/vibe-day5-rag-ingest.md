# Day5 Vibe Coding — RAG ① 문서 처리 파이프라인 (청킹 → 임베딩 → FAISS 저장)

> 도구: VSCode + Copilot (FastAPI 프로젝트만 수정). Spring · React 는 변경 없음.
> 이번 단계는 **오프라인 파이프라인(스크립트)** 이다. 검색·답변 연결(RAG ②)과 API 엔드포인트는 다음 단계.

```
[범위] 이 프로젝트(FastAPI)만 수정합니다. SpringBoot, React 코드는 만들지 않습니다.
기존 API(/api/v1/route, /api/v1/route-stream)와 SSE 이벤트는 수정하지 않습니다.
이번 단계는 문서를 검색 가능한 인덱스로 만드는 "오프라인 파이프라인"이며, 서버 엔드포인트는 만들지 않습니다.

[FastAPI] 금융 상품 설명서(txt, pdf)를 처리하는 RAG 인덱싱 파이프라인을 만들어 주세요.

0. 먼저 파이프라인 단계를 설명한 뒤 코드를 작성한다
   - app/rag/README.md 에 단계를 5줄 이내로 정리 (문서 읽기 → 청킹 → 임베딩 → 인덱스 저장 → 메타데이터 저장)
   - 단계마다 입력과 출력 한 줄씩

1. 파일 구성 (app/rag/)
   - loader.py     문서 읽기: .txt(UTF-8) 는 전체 1페이지, .pdf 는 pypdf 로 페이지별 텍스트 추출
                   (텍스트가 비어 있는 PDF 는 "스캔 이미지로 보임, 텍스트 추출 불가" 경고 후 건너뜀)
   - chunker.py    청킹
   - embedder.py   OpenAI 임베딩
   - store.py      FAISS 인덱스 + 메타데이터 저장/불러오기
   - ingest.py     전체 실행(CLI): python -m app.rag.ingest --docs data/docs --out data/index
   - search_cli.py 검증용: python -m app.rag.search_cli "질문" --k 3 (질문 임베딩 → top-k 청크와 점수 출력)
                   ※ 정식 검색·답변 연결은 다음 단계, 여기서는 인덱스가 맞게 만들어졌는지 확인하는 용도

2. 청킹 (chunker.py)
   - chunk_size=500자, overlap=50자 (config.py 의 RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP 값 사용, 하드코딩 금지)
   - 슬라이딩 윈도우: 다음 시작 위치 = 이전 시작 + (chunk_size - overlap)
   - 연속 공백·빈 줄은 정리하되 조항 번호("제12조") 같은 줄바꿈 정보는 의미를 해치지 않게 유지
   - overlap >= chunk_size 이면 ValueError, 빈 텍스트는 청크 0개, 마지막에 너무 짧은 조각(overlap 이하)은 만들지 않는다
   - 각 청크는 { text, source, page, chunk_index, start, end } (start/end 는 해당 페이지 텍스트 안의 문자 위치)

3. 임베딩 (embedder.py)
   - 모델은 config.py 의 RAG_EMBEDDING_MODEL (기본 text-embedding-3-small), 키는 기존 OPENAI_API_KEY
   - 청크를 한 번에 하나씩 호출하지 말고 배치(기본 100개씩)로 요청
   - 429/일시 오류는 최대 3회 지수 백오프로 재시도, 그래도 실패하면 어느 배치인지 알려 주는 예외
   - 결과는 numpy float32 배열 (N, 차원). L2 정규화하여 반환 (코사인 유사도용)

4. FAISS 저장 (store.py)
   - 정규화된 벡터이므로 faiss.IndexFlatIP (내적 = 코사인 유사도) 사용
   - 저장: <out>/index.faiss (faiss.write_index) + <out>/chunks.json (청크 원문·출처 메타데이터) + <out>/meta.json
   - FAISS 는 텍스트를 저장하지 못하므로 index 의 i 번째 벡터 = chunks.json 의 i 번째 항목 (순서 일치가 계약)
   - chunks.json 항목: { chunk_id, source, page, chunk_index, start, end, text }
   - meta.json: { embedding_model, dim, chunk_size, overlap, num_chunks, created_at, sources:[{name, sha256}] }
   - load(): index.ntotal 과 chunks 개수가 다르면 예외, 질문 임베딩 모델이 meta 의 모델과 다르면 경고
   - 메타데이터는 JSON 으로 저장한다 (pickle 사용 금지)
   - 이미 인덱스가 있으면 덮어쓰기 전에 확인 옵션(--force)을 요구

5. 샘플 문서 (data/docs/, 가상 은행)
   - 실제 은행이 아닌 가상의 "진은행" 상품 설명서 3개를 txt 로 만든다 (각 1,500~2,500자, 조항 번호 포함)
     · JIN 스마트 신용대출 (한도·금리·중도상환수수료율 0.7%, 대출 실행 후 3년 이내 적용)
     · 직장인 든든 마이너스통장
     · JIN 자유적립 적금 (중도해지 이율, 만기 후 이율)
   - 일반적인 값과 다르게 정해서(예: 수수료율 0.7%) 모델의 환각 답변과 구분되게 한다
   - data/index/ 는 .gitignore 에 추가하고, data/docs/ 는 커밋한다

6. 의존성
   - requirements.txt 에 faiss-cpu, numpy, pypdf 추가 (버전 고정)

7. 테스트 (OpenAI 는 가짜 임베더로 대체, 네트워크 호출 없음)
   - 청킹: 청크 길이 ≤ 500, 인접 청크가 정확히 50자 겹침, 마지막 조각 처리, 빈 텍스트, overlap>=size 오류
   - 임베딩: 배치 크기대로 호출되는지(호출 횟수), 반환 벡터가 정규화(노름 1)되어 있는지
   - 저장/불러오기: 저장 후 불러온 index.ntotal == 청크 수, i 번째 벡터와 i 번째 청크가 일치
   - 개수 불일치·차원 불일치 파일은 불러올 때 예외
   - 검색: 가짜 임베더로 만든 벡터에서 특정 청크가 top-1 으로 나온다

[확인]
- python -m app.rag.ingest --docs data/docs --out data/index  → 청크 수, 차원, 소요 시간 출력, data/index/ 에 3개 파일 생성
- python -m app.rag.search_cli "JIN 스마트 신용대출 중도상환수수료율은?" --k 3
  → 1순위 청크에 "0.7%" 가 들어 있고 출처(파일명·페이지·청크 번호)가 함께 출력된다
- python -m app.rag.search_cli "진은행에서 점심 메뉴 추천해줘" → 점수가 낮게 나온다 (관련 없는 질문)
```

---

## 원래 문구에서 고친 점

| # | 원래 | 문제 | 수정 |
|---|---|---|---|
| 1 | "먼저 전체 파이프라인 단계를 설명한 후 코드를 작성해줘" | 채팅 설명은 사라지고 산출물에 남지 않음 | `app/rag/README.md`로 남기도록 지정 (학생 자료로도 재사용) |
| 2 | 범위 언급 없음 | Copilot이 Spring·React·API까지 만들려 할 수 있음 | `[범위]` 추가, 이번 단계는 서버 엔드포인트 없는 오프라인 파이프라인 |
| 3 | "PDF (텍스트 파일로 대체 가능)" | PDF 추출 방식과 스캔 PDF 처리가 불명확 | txt/pdf 지원 명시, 스캔 PDF는 경고 후 건너뜀 |
| 4 | 500자/50자 | 인자·경계 규칙 없음 (마지막 조각, overlap 검증) | 슬라이딩 윈도우 공식, 오류·경계 규칙, config 값 사용 |
| 5 | 임베딩 | 청크마다 호출하면 느리고 rate limit | 배치 호출, 재시도, 정규화 |
| 6 | "FAISS에 저장" | 인덱스 종류와 유사도 기준이 없음 | IndexFlatIP + 정규화(코사인), 순서 일치 계약 |
| 7 | "메타데이터로 함께 저장" | FAISS는 텍스트를 저장하지 못함 | chunks.json 별도 저장, 필드 목록, meta.json(모델·차원·청킹 설정) |
| 8 | 검증 방법 없음 | 만든 뒤 맞는지 확인 불가 | 검증용 search_cli, 확인 시나리오 |
| 9 | 샘플 문서 없음 | 환각과 비교할 정답을 모름 | 가상 "진은행" 문서 3개(0.7% 등 일반적이지 않은 값) |
