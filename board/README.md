# 교실 보드 v7

김가영어학원의 시계 · 메시지 · 공지 전광판입니다.

- 접속 주소: https://kimsenglish.github.io/board/
- 디자인과 기능은 승인된 `WarmWise_Classroom_Board_v7.html`과 동일합니다.
- 계정 로그인, 원격 제어, 분석 도구 또는 별도 서버 데이터 저장은 없습니다.
- 전광판 설정은 각 브라우저의 localStorage에 저장됩니다. 공유 링크는 보내는 시점의 복사본입니다.
- 개인정보를 메시지에 넣어 공유하지 마세요. 같은 브라우저를 사용하는 사람은 저장된 전광판을 볼 수 있습니다.
- 기존 학원 홈페이지 파일은 변경하지 않았습니다.

## 배포 소스 복원

배포 전송을 위해 원본을 gzip + Base64 청크로 보관합니다. 각 청크의 유효 길이를 적용하고 연결한 뒤 압축을 풀면 원본 HTML이 바이트 단위로 복원됩니다. `index.html`은 로딩 시 SHA-256을 검증하고 원본 HTML을 실행합니다. 원본 내보내기 기능으로 저장한 HTML은 별도의 청크 없이 실행됩니다.

```python
from pathlib import Path
import base64, gzip, hashlib
root = Path(__file__).parent
lengths = [12988, 12988, 10651, 2333]
encoded = ''.join((root / f'v7.part{i+1}.txt').read_text()[:n] for i, n in enumerate(lengths))
html = gzip.decompress(base64.b64decode(encoded))
assert hashlib.sha256(html).hexdigest() == '7f9e55151546216ada0545e2d8494e31aecb048171e5249a11e0fc566ace8ff9'
(root / 'standalone.html').write_bytes(html)
```

원본 크기: 119,515 bytes. 최신 Chrome, Safari, Edge의 DecompressionStream 및 Web Crypto를 사용합니다.
