"""Add the fixed memo feature to the verified v7 without rewriting existing markup."""
from pathlib import Path
import hashlib
import re
import subprocess
import tempfile
import sys

SOURCE_SHA = 'dcc1b259ceaadf3a2f983dd19e011693d76473a0'

def upgrade(source: bytes) -> bytes:
    sha = hashlib.sha1(b'blob ' + str(len(source)).encode() + b'\0' + source).hexdigest()
    if sha != SOURCE_SHA:
        raise ValueError('Source changed; refusing to overwrite unreviewed changes: ' + sha)
    s = source.decode('utf-8')
    def replace(old, new):
        nonlocal s
        if s.count(old) != 1:
            raise ValueError('Expected exactly one anchor: ' + old[:100])
        s = s.replace(old, new, 1)

    css = '''
/* v8: Fixed notes stay outside the rotating message and its text fitting. */
.control-panel .tabs{gap:0;padding-left:10px;padding-right:10px}
.control-panel .tab{padding-left:4px;padding-right:4px;font-size:11px;white-space:nowrap}
.fixed-memo{grid-row:3;align-self:stretch;min-width:0;min-height:0;display:flex;flex-direction:column;gap:12px;padding:18px 22px;border:1px solid var(--stage-line);border-radius:12px;background:var(--bg);color:var(--fg);text-align:left;overflow:hidden;box-shadow:inset 3px 0 var(--stage-accent)}
.fixed-memo[hidden]{display:none!important}
.fixed-memo-head{display:flex;align-items:center;gap:9px;min-width:0;flex:0 0 26px}
.fixed-memo-head svg{width:18px;height:18px;flex:none;fill:none;stroke:var(--stage-accent);stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
.fixed-memo-title{font-size:19px;line-height:26px;letter-spacing:-.02em;font-weight:650;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fixed-memo-label{margin-left:auto;flex:none;font-size:12px;font-weight:500;letter-spacing:0;color:var(--dim);line-height:24px}
.fixed-memo-fit{flex:1;min-width:0;min-height:0;overflow:hidden}
.fixed-memo-text{margin:0;font-size:29px;line-height:1.48;font-weight:500;letter-spacing:-.025em;white-space:pre-wrap;word-break:keep-all;overflow-wrap:anywhere;color:var(--fg);text-align:left}
.stage[data-memo=true] .message-block{grid-template-rows:32px minmax(0,1fr) 208px;row-gap:24px;padding-bottom:0}
.stage[data-mode=clock][data-memo=true] .stage-main{display:grid;grid-template-columns:minmax(0,1fr) 480px;gap:40px;align-items:stretch}
.stage[data-mode=clock][data-memo=true] .message-block{display:grid!important;grid-template-rows:minmax(0,1fr);padding:0;row-gap:0}
.stage[data-mode=clock][data-memo=true] .message-category,.stage[data-mode=clock][data-memo=true] .message-fit,.stage[data-mode=clock][data-memo=true] .message-point{display:none!important}
.stage[data-mode=clock][data-memo=true] .fixed-memo{grid-row:1}
.stage[data-mode=clock][data-memo=true] .main-time{font-size:208px}
.stage[data-mode=clock][data-memo=true] .seconds{font-size:36px}
.memo-editor-hint{line-height:1.75;margin:12px 0 0}
#fixedMemoInput{min-height:180px;line-height:1.75}
'''
    replace('</style>', css + '</style>')
    old = '<button class="tab" role="tab" id="tab-appearance"'
    replace(old, '<button class="tab" role="tab" id="tab-memo" aria-controls="pane-memo" aria-selected="false" data-tab="memo">고정 메모</button>' + old)
    pane = '''  <section class="tabpane" id="pane-memo" role="tabpanel" aria-labelledby="tab-memo" hidden>
   <div class="section-head">고정 메모</div>
   <p class="hint" style="margin:0 0 18px;line-height:1.75">메시지가 넘어가도 같은 자리에 남아요.<br>과제, 준비물, 수업 중 적어둘 내용을 입력하세요.</p>
   <label class="checkrow" for="fixedMemoEnabled"><input id="fixedMemoEnabled" type="checkbox">화면에 고정 메모 표시</label>
   <div class="rule"></div>
   <label class="field"><span class="field-label">메모 제목 <small>선택 사항</small></span><input id="fixedMemoTitleInput" type="text" maxlength="28" placeholder="예: 오늘 할 일"></label>
   <label class="field"><span class="field-label">메모 내용 <small id="memoCharCount">0 / 400</small></span><textarea id="fixedMemoInput" rows="7" maxlength="400" placeholder="예시&#10;독해 12~15쪽&#10;틀린 문장 3개 다시 쓰기&#10;다음 시간: 단어장 가져오기"></textarea></label>
   <p class="hint" id="memoFitHint" style="margin:-8px 0 18px;line-height:1.75">비워두면 메모칸이 숨겨져요. 2~5줄 권장 · 최대 8줄.</p>
   <label class="field"><span class="field-label">메모 글자 크기 <small id="memoFontValue">100%</small></span><input id="memoFontScale" type="range" min="80" max="140" step="10" value="100"></label>
   <div class="saved-notice memo-editor-hint">이 전광판에 자동 저장되고 <b>설정 공유에도 포함</b>돼요. 개인적인 기록이 아닌, 아이들에게 보여줄 내용을 적어 주세요.</div>
  </section>
'''
    anchor = '  <section class="tabpane" id="pane-appearance"'
    replace(anchor, pane + anchor)
    memo = '''<aside class="fixed-memo" id="fixedMemo" aria-labelledby="fixedMemoTitle" hidden><div class="fixed-memo-head"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 3 6 0-1 6 4 4v2H6v-2l4-4-1-6ZM12 15v6"/></svg><h3 class="fixed-memo-title" id="fixedMemoTitle">메모</h3><span class="fixed-memo-label">고정</span></div><div class="fixed-memo-fit" id="fixedMemoFit"><p class="fixed-memo-text" id="fixedMemoText"></p></div></aside>'''
    anchor = '<p class="stage-message" id="stageMessage">답은 맞혔고,&#10;이유는?</p></div></div></div>'
    replace(anchor, '<p class="stage-message" id="stageMessage">답은 맞혔고,&#10;이유는?</p></div>' + memo + '</div></div>')
    anchor = '<button class="btn small" id="exitDisplay">'
    replace(anchor, '<button class="btn small" id="editFixedMemoBtn">메모 수정</button>' + anchor)
    replace("clockNote:'',mode:'both'", "clockNote:'',fixedMemo:'',fixedMemoTitle:'메모',fixedMemoEnabled:true,memoFontScale:100,mode:'both'")
    replace("clockNote:text(raw.clockNote,48,d.clockNote),mode:", "clockNote:text(raw.clockNote,48,d.clockNote),fixedMemo:memoValue(raw.fixedMemo),fixedMemoTitle:text(raw.fixedMemoTitle,28,'메모'),fixedMemoEnabled:raw.fixedMemoEnabled!==false,memoFontScale:bounded(raw.memoFontScale,80,140,100),mode:")
    anchor = 'function bounded(v,min,max,fallback)'
    replace(anchor, "function memoValue(value){const raw=text(value,400).replace(/\\r\\n?/g,'\\n');const lines=raw.split('\\n');return lines.length<=8?raw:lines.slice(0,7).concat(lines.slice(7).join(' ')).join('\\n');}\n" + anchor)
    replace('function renderSettings(){loading=true;', "function renderSettings(){loading=true;renderMemoSettings();")
    replace('function fitText(){\n fitNotice();', 'function fitText(){\n fitNotice();\n fitMemo();')
    replace('const maxHeight=Math.max(24,block.clientHeight-labelHeight-gap-', "const memoHeight=$('fixedMemo').hidden?0:$('fixedMemo').offsetHeight+gap;\n const maxHeight=Math.max(24,block.clientHeight-labelHeight-gap-memoHeight-")
    replace('function renderStage(){const s=', 'function renderStage(){renderMemo();const s=')
    funcs = '''
function renderMemoSettings(){
 $('fixedMemoEnabled').checked=board.fixedMemoEnabled;
 $('fixedMemoTitleInput').value=board.fixedMemoTitle;
 $('fixedMemoInput').value=board.fixedMemo;
 $('memoCharCount').textContent=board.fixedMemo.length+' / 400';
 $('memoFontScale').value=board.memoFontScale;
 $('memoFontValue').textContent=board.memoFontScale+'%';
}
function renderMemo(){
 const visible=board.fixedMemoEnabled&&!!board.fixedMemo.trim();
 $('stage').dataset.memo=String(visible);
 $('fixedMemo').hidden=!visible;
 // Avoid replacing memo text on message rotation, including text selection.
 const title=board.fixedMemoTitle.trim()||'메모';
 if($('fixedMemoTitle').textContent!==title)$('fixedMemoTitle').textContent=title;
 if($('fixedMemoText').textContent!==board.fixedMemo)$('fixedMemoText').textContent=board.fixedMemo;
}
function fitMemo(){
 if($('fixedMemo').hidden)return;
 const el=$('fixedMemoText'),box=$('fixedMemoFit');
 const target=Math.round(29*board.memoFontScale/100);let size=target;
 el.style.fontSize=size+'px';
 while(size>8&&(el.scrollHeight>box.clientHeight+1||el.scrollWidth>box.clientWidth+1))el.style.fontSize=(--size)+'px';
 $('memoFitHint').textContent=size<target?'메모칸에 맞게 글자를 줄였어요. 내용을 줄이면 더 크게 보여요.':'비워두면 메모칸이 숨겨져요. 2~5줄 권장 · 최대 8줄.';
}
function updateMemoText(){
 const el=$('fixedMemoInput'),value=memoValue(el.value);
 if(value!==el.value){el.value=value;toast('8줄을 넘는 줄바꿈은 공백으로 바꿨어요. 내용은 이어서 표시돼요.');}
 board.fixedMemo=value;$('memoCharCount').textContent=value.length+' / 400';renderStage();queueSave();
}
$('fixedMemoInput').addEventListener('input',e=>{if(!e.isComposing)updateMemoText();});
$('fixedMemoInput').addEventListener('compositionend',updateMemoText);
$('fixedMemoTitleInput').addEventListener('input',e=>{board.fixedMemoTitle=e.target.value;renderStage();queueSave();});
$('fixedMemoEnabled').addEventListener('change',e=>{board.fixedMemoEnabled=e.target.checked;renderStage();queueSave();});
$('memoFontScale').addEventListener('input',e=>{board.memoFontScale=bounded(e.target.value,80,140,100);$('memoFontValue').textContent=board.memoFontScale+'%';fitMemo();queueSave();});
$('editFixedMemoBtn').addEventListener('click',async()=>{await stopPresentation();setTab('memo');$('fixedMemoInput').focus();});
'''
    replace('// Editor events. User-authored content is always rendered through textContent/value.', funcs + '\n// Editor events. User-authored content is always rendered through textContent/value.')
    replace("downloadFile('classroom-board-v7.html'", "downloadFile('classroom-board-v8.html'")
    replace('<title>교실 보드 · v7</title>', '<title>교실 보드 · v8</title>')
    replace('교실 보드 · v7.0', '교실 보드 · v8.0')
    replace('숨김·만료 메시지를 포함한 현재 전광판의 모든 문구가 링크에 들어가요.', '숨김·만료 메시지와 고정 메모를 포함한 현재 전광판의 모든 문구가 링크에 들어가요.')
    for attrs, script in re.findall(r'<script([^>]*)>([\s\S]*?)</script>', s, re.I):
        if 'application/json' in attrs:
            continue
        with tempfile.NamedTemporaryFile(suffix='.js', mode='w', encoding='utf-8') as f:
            f.write(script);f.flush();subprocess.run(['node','--check',f.name],check=True)
    return s.encode('utf-8')

if __name__=='__main__':
    target=Path(sys.argv[1] if len(sys.argv)>1 else 'board/index.html')
    output=upgrade(target.read_bytes())
    target.write_bytes(output)
    print('Fixed memo added; UTF-8 bytes:',len(output),'SHA256:',hashlib.sha256(output).hexdigest())
