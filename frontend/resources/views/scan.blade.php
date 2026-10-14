<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Document Scanner</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: light;
    --bg: #f5f6fa; --card: #fff; --text: #111827; --muted: #6b7280; --line: #eceef3;
    --accent: #4f46e5; --accent-soft: #eef0ff;
    --ok: #15803d; --ok-bg: #e8f6ee; --warn: #b45309; --warn-bg: #fdf3df; --bad: #b91c1c; --bad-bg: #fdecec;
    --shadow: 0 1px 3px rgba(17,24,39,.06), 0 10px 28px rgba(17,24,39,.05);
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--text); font: 15px/1.5 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }

  .topbar { background: var(--card); border-bottom: 1px solid var(--line); }
  .topbar .in { max-width: 1000px; margin: 0 auto; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 16px; color: var(--text); text-decoration: none; }
  .brand i { width: 32px; height: 32px; border-radius: 9px; background: var(--accent); color: #fff; display: grid; place-items: center; }
  .btn { background: var(--accent); color: #fff; border: 0; border-radius: 10px; padding: 10px 18px; font: inherit; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn.sm { padding: 8px 14px; font-size: 14px; }

  .card { background: var(--card); border-radius: 16px; box-shadow: var(--shadow); padding: 22px; }
  .card h2 { margin: 0 0 14px; font-size: 12px; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }

  /* upload state */
  .center { min-height: calc(100vh - 62px); display: flex; align-items: center; justify-content: center; padding: 24px 16px; }
  .up { width: 100%; max-width: 760px; padding: 48px 56px; text-align: center; border-radius: 22px; }
  .up h1 { font-size: 32px; letter-spacing: -.02em; margin: 0 0 8px; } .up p { margin: 0 0 32px; color: var(--muted); font-size: 17px; }
  #drop { border: 2px dashed #d5d9e4; border-radius: 18px; padding: 72px 24px; cursor: pointer; transition: .15s; }
  #drop:hover, #drop.over { border-color: var(--accent); background: var(--accent-soft); }
  #drop svg { color: var(--accent); margin-bottom: 14px; width: 52px; height: 52px; } #drop .t { font-weight: 600; font-size: 19px; } #drop .h { color: var(--muted); font-size: 14px; margin-top: 4px; }
  #picked { display: none; font-weight: 600; word-break: break-all; } #picked small { display: block; color: var(--muted); font-weight: 400; }
  .up .btn { width: 100%; margin-top: 24px; padding: 16px; font-size: 17px; border-radius: 14px; }
  @media (max-width: 640px) { .up { padding: 28px 20px; } #drop { padding: 44px 16px; } .up h1 { font-size: 26px; } }
  .spin { display: none; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.4); border-top-color: #fff; border-radius: 50%; animation: s .7s linear infinite; }
  .loading .spin { display: block; } @keyframes s { to { transform: rotate(360deg); } }
  .err { margin-top: 14px; background: var(--bad-bg); color: var(--bad); padding: 11px 14px; border-radius: 10px; font-size: 14px; text-align: left; }

  /* result state */
  .res { max-width: 1000px; margin: 0 auto; padding: 24px 20px 56px; display: grid; gap: 16px; }
  .hero { display: flex; gap: 24px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
  .file { color: var(--muted); font-size: 13px; word-break: break-all; }
  .type { font-size: 30px; font-weight: 700; letter-spacing: -.02em; margin: 2px 0 10px; }
  .badges { display: flex; gap: 8px; flex-wrap: wrap; }
  .badge { background: var(--bg); border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 500; }
  .badge.ok { background: var(--ok-bg); color: var(--ok); } .badge.warn { background: var(--warn-bg); color: var(--warn); } .badge.bad { background: var(--bad-bg); color: var(--bad); }
  .ring { position: relative; width: 104px; height: 104px; flex: none; }
  .ring svg { transform: rotate(-90deg); } .ring .track { stroke: var(--line); }
  .ring .num { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; line-height: 1.15; }
  .ring b { font-size: 22px; } .ring span { font-size: 11px; color: var(--muted); display: block; }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
  .stat .k { font-size: 12px; color: var(--muted); } .stat .v { font-size: 20px; font-weight: 700; margin-top: 2px; word-break: break-word; }
  .cols { display: grid; grid-template-columns: 3fr 2fr; gap: 16px; align-items: start; }

  .row { display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .row:first-of-type { padding-top: 0; } .row:last-child { border-bottom: 0; padding-bottom: 0; }
  .row .k { color: var(--muted); flex: none; }
  .row .v { font-weight: 600; text-align: right; word-break: break-word; display: flex; gap: 8px; align-items: flex-start; justify-content: flex-end; }
  .row .v.na { color: #a1a7b5; font-weight: 400; }
  .cp { border: 0; background: none; color: #9ca3af; cursor: pointer; padding: 2px; border-radius: 6px; line-height: 0; margin-top: 2px; }
  .cp:hover { color: var(--accent); background: var(--accent-soft); }

  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { background: var(--accent-soft); color: var(--accent); border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 500; }
  .verify { background: var(--warn-bg); color: var(--warn); border-radius: 12px; padding: 12px 16px; font-size: 14px; }
  details summary { cursor: pointer; font-weight: 600; color: var(--muted); font-size: 13px; }
  pre { margin: 12px 0 0; background: #0f172a; color: #e2e8f0; border-radius: 10px; padding: 14px; overflow: auto; font-size: 12.5px; line-height: 1.5; }

  .doc { display: grid; gap: 12px; }
  .doc .top { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
  .doc .type { font-size: 20px; margin: 2px 0 6px; }
  .doc .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 32px; }
  .cats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 28px; text-align: left; }
  .cat { border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; font-size: 13px; color: var(--muted); }
  .cat b { display: block; color: var(--text); font-size: 14px; margin-bottom: 2px; }
  .cat.on { border-color: var(--accent); background: var(--accent-soft); } .cat.on b { color: var(--accent); }
  .cats.sm { margin-top: 0; } .cats.sm .cat { padding: 10px 14px; }
  @media (max-width: 640px) { .cats { grid-template-columns: 1fr 1fr; } }
  .sum { color: var(--muted); font-size: 14px; }
  @media (max-width: 760px) { .doc .grid { grid-template-columns: 1fr; } }
  @media (max-width: 760px) { .stats { grid-template-columns: repeat(2, 1fr); } .cols { grid-template-columns: 1fr; } }
</style>
</head>
<body>
@php
  $categories = [
    'Vehicles' => 'RC, registration, insurance',
    'Company' => 'Incorporation, CIN, GST',
    'Equipments' => 'Invoices, serial no., PAT test',
    'People' => 'Employee ID, identity cards',
  ];
@endphp
<div class="topbar"><div class="in">
  <a class="brand" href="{{ route('scan.index') }}"><i>
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>
  </i>AI Document Scanner</a>
  @if (session('result') || session('batch'))<a class="btn sm" href="{{ route('scan.index') }}">Scan another</a>@endif
</div></div>

@if (session('batch'))
  @php
    $b = session('batch');
    $statusMap = ['valid' => ['ok', 'Valid'], 'expiring_soon' => ['warn', 'Expiring soon'], 'expired' => ['bad', 'Expired'], 'unknown' => ['', 'Expiry unknown']];
  @endphp
  <div class="res">
    <div class="card">
      <div class="file">{{ $b['zip'] }}</div>
      <div class="type" style="font-size:24px">{{ count($b['items']) }} documents scanned</div>
      <div class="sum">
        {{ collect($b['items'])->filter(fn ($i) => isset($i['result']))->count() }} parsed
        @if (collect($b['items'])->filter(fn ($i) => isset($i['error']))->count()) · {{ collect($b['items'])->filter(fn ($i) => isset($i['error']))->count() }} failed @endif
        @if ($b['skipped']) · {{ $b['skipped'] }} skipped (unsupported or over limit) @endif
      </div>
    </div>

    @foreach ($b['items'] as $item)
      <div class="card doc">
        @if (isset($item['error']))
          <div class="file">{{ $item['filename'] }}</div>
          <div class="err" style="margin:0">{{ $item['error'] }}</div>
        @else
          @php
            $r = $item['result']; $e = $r['expiry'] ?? []; $conf = (float) ($r['confidence'] ?? 0);
            [$sCls, $sLabel] = $statusMap[$e['status'] ?? 'unknown'] ?? ['', ucfirst($e['status'] ?? '')];
          @endphp
          <div class="top">
            <div>
              <div class="file">{{ $item['filename'] }}</div>
              <div class="type">{{ $r['document_type'] ?? 'Unknown document' }}</div>
              <div class="badges">
                @if (!empty($r['country']))<span class="badge">{{ $r['country'] }}</span>@endif
                <span class="badge {{ $sCls }}">{{ $sLabel }}</span>
                <span class="badge {{ $conf >= 0.5 ? 'ok' : ($conf >= 0.25 ? 'warn' : 'bad') }}">{{ round($conf * 100) }}% match</span>
              </div>
            </div>
          </div>
          <div class="grid">
            <div>
              @forelse ($r['metadata'] ?? [] as $key => $value)
                <div class="row"><span class="k">{{ \Illuminate\Support\Str::headline($key) }}</span>
                  <span class="v {{ ($value === null || $value === '') ? 'na' : '' }}">{{ ($value === null || $value === '') ? 'Not found' : $value }}</span></div>
              @empty
                <div class="sum">No details extracted.</div>
              @endforelse
            </div>
            <div>
              <div class="row"><span class="k">Start date</span><span class="v {{ empty($e['start_date']) ? 'na' : '' }}">{{ $e['start_date'] ?? 'Not found' }}</span></div>
              <div class="row"><span class="k">Expiry date</span><span class="v {{ empty($e['expiry_date']) ? 'na' : '' }}">{{ $e['expiry_date'] ?? 'Not found' }}</span></div>
              @php $d = $e['days_remaining'] ?? null; @endphp
              <div class="row"><span class="k">Days remaining</span><span class="v {{ $d === null ? 'na' : '' }}">{{ $d === null ? 'Not found' : ($d >= 0 ? $d . ' days' : abs($d) . ' days overdue') }}</span></div>
            </div>
          </div>
        @endif
      </div>
    @endforeach
  </div>

@elseif (session('result'))
  @php
    $r = session('result');
    $e = $r['expiry'] ?? [];
    $status = $e['status'] ?? 'unknown';
    $conf = (float) ($r['confidence'] ?? 0);
    $band = $conf >= 0.5 ? ['ok', 'High'] : ($conf >= 0.25 ? ['warn', 'Medium'] : ['bad', 'Low']);
    $ringColor = ['ok' => '#15803d', 'warn' => '#d97706', 'bad' => '#dc2626'][$band[0]];
    $circ = 2 * M_PI * 44;
    $meta = $r['metadata'] ?? [];
    $statusMap = ['valid' => ['ok', 'Valid'], 'expiring_soon' => ['warn', 'Expiring soon'], 'expired' => ['bad', 'Expired'], 'unknown' => ['', 'Expiry unknown']];
    [$sCls, $sLabel] = $statusMap[$status] ?? ['', ucfirst($status)];
    $days = $e['days_remaining'] ?? null;
    $methods = ['keyword' => 'Keyword match', 'embedding' => 'Semantic match', 'filename' => 'Filename hint', 'none' => 'None'];
  @endphp
  <div class="res">
    <div class="card hero">
      <div>
        <div class="file">{{ session('filename') }}</div>
        <div class="type">{{ $r['document_type'] ?? 'Unknown document' }}</div>
        <div class="badges">
          @if (!empty($r['country']))<span class="badge">{{ $r['country'] }}</span>@endif
          <span class="badge {{ $sCls }}">{{ $sLabel }}</span>
        </div>
      </div>
      <div class="ring">
        <svg width="104" height="104" viewBox="0 0 104 104">
          <circle class="track" cx="52" cy="52" r="44" fill="none" stroke-width="9"/>
          <circle cx="52" cy="52" r="44" fill="none" stroke-width="9" stroke-linecap="round" stroke="{{ $ringColor }}"
                  stroke-dasharray="{{ $circ }}" stroke-dashoffset="{{ $circ * (1 - min(max($conf, 0), 1)) }}"/>
        </svg>
        <div class="num"><div><b>{{ round($conf * 100) }}%</b><span>{{ $band[1] }} match</span></div></div>
      </div>
    </div>

    <div class="cats sm">
      @foreach ($categories as $name => $desc)<div class="cat {{ ($r['document_type'] ?? null) === $name ? 'on' : '' }}"><b>{{ $name }}</b>{{ $desc }}</div>@endforeach
    </div>

    @if ($conf < 0.25)
      <div class="verify">Low match score. Please verify the extracted details below.</div>
    @endif

    <div class="stats">
      <div class="card stat"><div class="k">Confidence</div><div class="v">{{ number_format($conf * 100, 1) }}%</div></div>
      <div class="card stat"><div class="k">Detection method</div><div class="v">{{ $methods[$r['method'] ?? 'none'] ?? ($r['method'] ?? '—') }}</div></div>
      <div class="card stat"><div class="k">Processing time</div><div class="v">{{ $r['processing_time_ms'] ?? 0 }} ms</div></div>
      <div class="card stat"><div class="k">Text extracted</div><div class="v">{{ number_format($r['text_length'] ?? 0) }} chars</div></div>
    </div>

    <div class="cols">
      <div class="card">
        <h2>Extracted details</h2>
        @forelse ($meta as $key => $value)
          <div class="row">
            <span class="k">{{ \Illuminate\Support\Str::headline($key) }}</span>
            @if ($value !== null && $value !== '')
              <span class="v">{{ $value }}
                <button type="button" class="cp" title="Copy" data-copy="{{ $value }}"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg></button>
              </span>
            @else
              <span class="v na">Not found</span>
            @endif
          </div>
        @empty
          <div class="v na" style="color:var(--muted)">No details could be extracted from this document.</div>
        @endforelse
      </div>

      <div class="card">
        <h2>Expiry</h2>
        <div class="row"><span class="k">Status</span><span class="v"><span class="badge {{ $sCls }}">{{ $sLabel }}</span></span></div>
        <div class="row"><span class="k">Start date</span><span class="v {{ empty($e['start_date']) ? 'na' : '' }}">{{ $e['start_date'] ?? 'Not found' }}</span></div>
        <div class="row"><span class="k">Expiry date</span><span class="v {{ empty($e['expiry_date']) ? 'na' : '' }}">{{ $e['expiry_date'] ?? 'Not found' }}</span></div>
        <div class="row"><span class="k">Days remaining</span>
          <span class="v {{ $days === null ? 'na' : '' }}">{{ $days === null ? 'Not found' : ($days >= 0 ? $days . ' days' : abs($days) . ' days overdue') }}</span></div>
      </div>
    </div>

    <div class="card">
      <h2>Keywords detected ({{ count($r['keywords_detected'] ?? []) }})</h2>
      <div class="chips">
        @forelse ($r['keywords_detected'] ?? [] as $kw)<span class="chip">{{ $kw }}</span>@empty<span style="color:var(--muted)">None</span>@endforelse
      </div>
    </div>

    <div class="card">
      <details>
        <summary>Raw response (JSON)</summary>
        <pre>{{ json_encode($r, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) }}</pre>
      </details>
    </div>
  </div>

@else
  <div class="center">
    <form method="POST" action="{{ route('scan.run') }}" enctype="multipart/form-data" id="form" class="card up">
      @csrf
      <h1>Scan documents</h1>
      <p>Upload one document, or a ZIP with many (vehicle, GST, company…).</p>
      <input type="file" name="file" id="file" hidden accept=".zip,.pdf,.jpg,.jpeg,.png,.tif,.tiff,.docx,.doc,.pptx,.ppt,.txt">
      <div id="drop">
        <div id="empty">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>
          <div class="t">Drop a file or a ZIP folder here, or click to browse</div>
          <div class="h">ZIP of many documents, or a single PDF / image / Word / PowerPoint / TXT · ZIP up to 50 MB</div>
        </div>
        <div id="picked"><span id="pname"></span><small id="psize"></small></div>
      </div>
      <button type="submit" class="btn" id="go" disabled><span class="spin"></span><span id="golabel">Scan document</span></button>
      @if ($errors->any())<div class="err">{{ $errors->first() }}</div>@endif
    </form>
  </div>
@endif

<script>
  const drop = document.getElementById('drop'), input = document.getElementById('file'), go = document.getElementById('go');
  if (drop) {
    const isZip = f => /\.zip$/i.test(f.name);
    const tooBig = f => f.size > (isZip(f) ? 52428800 : 20971520);
    const size = b => b < 1048576 ? (b / 1024).toFixed(0) + ' KB' : (b / 1048576).toFixed(1) + ' MB';
    const show = () => {
      const f = input.files[0];
      document.getElementById('empty').style.display = f ? 'none' : '';
      document.getElementById('picked').style.display = f ? 'block' : 'none';
      if (f) {
        document.getElementById('pname').textContent = f.name;
        document.getElementById('psize').textContent = size(f.size) + (tooBig(f) ? ' · too large' : '');
      }
      go.disabled = !f || tooBig(f);
    };
    drop.onclick = () => input.click();
    input.onchange = show;
    drop.ondragover = e => { e.preventDefault(); drop.classList.add('over'); };
    drop.ondragleave = () => drop.classList.remove('over');
    drop.ondrop = e => { e.preventDefault(); drop.classList.remove('over'); input.files = e.dataTransfer.files; show(); };
    document.getElementById('form').onsubmit = () => {
      go.disabled = true; go.classList.add('loading');
      document.getElementById('golabel').textContent = (input.files[0] && isZip(input.files[0])) ? 'Scanning all documents… this may take a while' : 'Scanning…';
    };
  }
  document.querySelectorAll('.cp').forEach(b => b.onclick = async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); b.style.color = 'var(--ok)'; setTimeout(() => b.style.color = '', 1200); } catch (e) {}
  });
</script>
</body>
</html>
