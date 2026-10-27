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
    --bg: #f2f7ff; --card: #ffffff; --text: #0f2540; --muted: #5f7390; --line: #dce8f7; --soft: #eaf2ff;
    --accent: #2563eb; --accent-2: #1d4ed8; --accent-soft: #e2edff;
    --ok: #15803d; --ok-bg: #e6f6ec; --warn: #b45309; --warn-bg: #fdf3dc; --bad: #b91c1c; --bad-bg: #fdecec;
    --shadow: 0 1px 2px rgba(37,99,235,.05), 0 8px 24px rgba(37,99,235,.08);
    --glow: none;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body { margin: 0; background: linear-gradient(180deg, #e8f1ff 0%, var(--bg) 340px); background-attachment: fixed; color: var(--text); font: 15px/1.55 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; min-height: 100vh; }
  @keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
  .res > *, .up { animation: rise .45s ease both; }
  .res > *:nth-child(2) { animation-delay: .05s; } .res > *:nth-child(3) { animation-delay: .1s; } .res > *:nth-child(n+4) { animation-delay: .15s; }

  .topbar { position: sticky; top: 0; z-index: 10; background: color-mix(in srgb, var(--card) 82%, transparent); backdrop-filter: blur(12px); border-bottom: 1px solid var(--line); }
  .topbar .in { max-width: 1040px; margin: 0 auto; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 16px; color: var(--text); text-decoration: none; letter-spacing: -.01em; }
  .brand i { width: 34px; height: 34px; border-radius: 10px; background: var(--accent); color: #fff; display: grid; place-items: center; box-shadow: 0 6px 16px rgba(37,99,235,.35); }
  .actions { display: flex; gap: 8px; align-items: center; }
  .btn { background: var(--accent); color: #fff; border: 0; border-radius: 12px; padding: 10px 18px; font: inherit; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 8px; transition: transform .12s, box-shadow .12s, opacity .12s; box-shadow: 0 6px 18px rgba(37,99,235,.3); }
  .btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(37,99,235,.4); }
  .btn:disabled { opacity: .4; cursor: not-allowed; box-shadow: none; }
  .btn.sm { padding: 8px 14px; font-size: 14px; }
  .btn.ghost { background: var(--card); color: var(--text); border: 1px solid var(--line); box-shadow: none; }
  .btn.ghost:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); box-shadow: none; }

  .card { background: var(--card); border-radius: 18px; box-shadow: var(--shadow); padding: 22px; border: 1px solid var(--line); }
  .card h2 { margin: 0 0 14px; font-size: 12px; font-weight: 600; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }

  /* upload state */
  .center { min-height: calc(100vh - 62px); display: flex; align-items: center; justify-content: center; padding: 28px 16px; }
  .up { width: 100%; max-width: 780px; padding: 40px 36px 34px; text-align: center; border-radius: 26px; }
  .eyebrow { display: inline-flex; align-items: center; gap: 8px; background: var(--accent-soft); color: var(--accent); font-size: 12.5px; font-weight: 600; padding: 5px 12px; border-radius: 999px; margin-bottom: 16px; }
  .eyebrow::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 0 3px var(--ok-bg); }
  .up h1 { font-size: 36px; letter-spacing: -.03em; line-height: 1.15; margin: 0 0 10px; }
  .up h1 em { font-style: normal; color: var(--muted); }
  .up p { margin: 0 0 30px; color: var(--muted); font-size: 17px; }
  #drop { border: 2px dashed #a9c6ee; border-radius: 20px; padding: 60px 24px; cursor: pointer; transition: .18s; background: var(--soft); }
  #drop:hover, #drop.over { border-color: var(--accent); background: #f4f8ff; transform: translateY(-1px); }
  #drop .ico { width: 64px; height: 64px; border-radius: 18px; background: var(--card); display: grid; place-items: center; margin: 0 auto 16px; box-shadow: var(--shadow); color: var(--accent); }
  #drop .t { font-weight: 600; font-size: 19px; } #drop .h { color: var(--muted); font-size: 14px; margin-top: 6px; }
  #picked { display: none; font-weight: 600; word-break: break-all; } #picked small { display: block; color: var(--muted); font-weight: 400; margin-top: 2px; }
  #picked .ext { display: inline-block; background: var(--accent); color: #fff; font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 7px; margin-bottom: 10px; letter-spacing: .05em; }
  .formats { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; margin-top: 16px; }
  .formats span { font-size: 11.5px; font-weight: 600; color: var(--muted); background: var(--card); border: 1px solid var(--line); border-radius: 7px; padding: 2px 8px; }
  .up .btn { width: 100%; margin-top: 22px; padding: 16px; font-size: 17px; border-radius: 14px; }
  .steps { display: flex; justify-content: center; gap: 28px; margin-top: 28px; color: var(--muted); font-size: 13px; flex-wrap: wrap; }
  .steps b { display: inline-grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--accent-soft); color: var(--accent); font-size: 12px; margin-right: 6px; }
  @media (max-width: 640px) { .up { padding: 30px 20px; } #drop { padding: 40px 16px; } .up h1 { font-size: 28px; } .steps { gap: 12px; } }
  .spin { display: none; width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.35); border-top-color: #fff; border-radius: 50%; animation: s .7s linear infinite; }
  .loading .spin { display: block; } @keyframes s { to { transform: rotate(360deg); } }
  .err { margin-top: 14px; background: var(--bad-bg); color: var(--bad); padding: 11px 14px; border-radius: 10px; font-size: 14px; text-align: left; }

  /* waiting state */
  .wait .orb { width: 84px; height: 84px; margin: 0 auto 20px; border-radius: 50%; border: 5px solid var(--line); border-top-color: var(--accent); animation: s 1s linear infinite; }
  .bar { height: 10px; border-radius: 999px; background: var(--soft); overflow: hidden; margin: 8px 0 12px; }
  .bar i { display: block; height: 100%; width: 8%; border-radius: 999px; background: var(--accent); transition: width .5s ease; }
  .bar.indet i { width: 35%; animation: slide 1.3s ease-in-out infinite; } @keyframes slide { 0% { margin-left: -35%; } 100% { margin-left: 100%; } }
  .wait .sub { color: var(--muted); font-size: 14px; margin: 0; }

  /* result state */
  .res { max-width: 1040px; margin: 0 auto; padding: 26px 20px 60px; display: grid; gap: 16px; }
  .hero { display: flex; gap: 24px; align-items: center; justify-content: space-between; flex-wrap: wrap; padding: 26px; background: var(--card); }
  .file { color: var(--muted); font-size: 13px; word-break: break-all; }
  .type { font-size: 32px; font-weight: 800; letter-spacing: -.03em; margin: 2px 0 10px; }
  .badges { display: flex; gap: 8px; flex-wrap: wrap; }
  .badge { background: var(--soft); border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 600; }
  .badge.ok { background: var(--ok-bg); color: var(--ok); } .badge.warn { background: var(--warn-bg); color: var(--warn); } .badge.bad { background: var(--bad-bg); color: var(--bad); }
  .ring { position: relative; width: 112px; height: 112px; flex: none; }
  .ring svg { transform: rotate(-90deg); } .ring .track { stroke: var(--line); }
  .ring circle:not(.track) { transition: stroke-dashoffset 1s ease; }
  .ring .num { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; line-height: 1.15; }
  .ring b { font-size: 24px; } .ring span { font-size: 11px; color: var(--muted); display: block; }
  .hero .actions { margin-top: 14px; }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
  .stat { padding: 18px 20px; } .stat .k { font-size: 12px; color: var(--muted); font-weight: 500; } .stat .v { font-size: 21px; font-weight: 700; margin-top: 2px; word-break: break-word; letter-spacing: -.01em; }
  .cols { display: grid; grid-template-columns: 3fr 2fr; gap: 16px; align-items: start; }

  .row { display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .row:first-of-type { padding-top: 0; } .row:last-child { border-bottom: 0; padding-bottom: 0; }
  .row .k { color: var(--muted); flex: none; }
  .row .v { font-weight: 600; text-align: right; word-break: break-word; display: flex; gap: 8px; align-items: flex-start; justify-content: flex-end; }
  .row .v.na { color: var(--muted); font-weight: 400; opacity: .7; }
  .cp { border: 0; background: none; color: var(--muted); cursor: pointer; padding: 3px; border-radius: 7px; line-height: 0; margin-top: 1px; transition: .12s; }
  .cp:hover { color: var(--accent); background: var(--accent-soft); }

  .chips { display: flex; flex-wrap: wrap; gap: 8px; }
  .chip { background: var(--accent-soft); color: var(--accent); border-radius: 999px; padding: 4px 12px; font-size: 13px; font-weight: 600; }
  .verify { background: var(--warn-bg); color: var(--warn); border-radius: 14px; padding: 12px 16px; font-size: 14px; font-weight: 500; }
  details summary { cursor: pointer; font-weight: 600; color: var(--muted); font-size: 13px; }
  pre { margin: 12px 0 0; background: #0f2540; color: #e2e8f0; border-radius: 12px; padding: 14px; overflow: auto; font-size: 12.5px; line-height: 1.55; }

  .doc { display: grid; gap: 12px; transition: transform .15s, box-shadow .15s; }
  .doc:hover { transform: translateY(-2px); }
  .doc .top { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
  .doc .type { font-size: 21px; margin: 2px 0 6px; font-weight: 700; }
  .doc .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 32px; }
  .cats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 26px; text-align: left; }
  .cat { border: 1px solid var(--line); border-radius: 14px; padding: 12px 14px; font-size: 12.5px; color: var(--muted); background: var(--card); }
  .cat b { display: block; color: var(--text); font-size: 14px; margin-bottom: 2px; }
  .cat.on { border-color: var(--accent); background: var(--accent-soft); } .cat.on b { color: var(--accent); }
  .cats.sm { margin-top: 0; } .cats.sm .cat { padding: 10px 14px; }
  @media (max-width: 640px) { .cats { grid-template-columns: 1fr 1fr; } }
  .sum { color: var(--muted); font-size: 14px; }
  .tiles { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
  .tile { background: var(--soft); border-radius: 12px; padding: 8px 14px; font-size: 13px; color: var(--muted); } .tile b { color: var(--text); font-size: 17px; margin-right: 4px; }
  @media (max-width: 760px) { .doc .grid { grid-template-columns: 1fr; } }
  @media (max-width: 760px) { .stats { grid-template-columns: repeat(2, 1fr); } .cols { grid-template-columns: 1fr; } .type { font-size: 26px; } }

  /* document search */
  .sections { display: grid; gap: 16px; align-content: start; }
  .sections h2 .badge { margin-left: 8px; vertical-align: middle; }
  .topbar.wide .in { max-width: 1840px; padding-left: 32px; padding-right: 32px; }
  .center.stack { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; align-items: stretch; grid-template-rows: minmax(0, 1fr); min-height: calc(100vh - 62px); width: 100%; max-width: 1840px; margin: 0 auto; padding: 24px 32px; }
  .stack .up { display: flex; flex-direction: column; justify-content: center; }
  .stack #drop { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 260px; }
  .stack .up { max-width: none; padding: 40px 36px 34px; }
  .stack .up h1 { font-size: 32px; text-wrap: balance; }
  .stack .up p { font-size: 16px; text-wrap: balance; }

  /* search panel: same height as the upload card, results scroll inside */
  .find { contain: size; display: flex; flex-direction: column; padding: 28px; border-radius: 26px; min-height: 0; }
  .find .head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
  .find h2 { margin: 0; }
  .find .count { font-size: 12px; font-weight: 600; background: var(--accent-soft); color: var(--accent); border-radius: 999px; padding: 3px 10px; }
  .find .field { position: relative; }
  .find .field svg { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--muted); pointer-events: none; }
  .find input { width: 100%; font: inherit; font-size: 15px; padding: 13px 16px 13px 44px; border: 1px solid var(--line); border-radius: 14px; background: var(--soft); color: var(--text); outline: none; transition: .15s; }
  .find input:focus { border-color: var(--accent); background: var(--card); box-shadow: 0 0 0 4px var(--accent-soft); }
  .find .meta { color: var(--muted); font-size: 13px; margin: 14px 2px 10px; }
  #qres { flex: 1; min-height: 0; overflow-y: auto; display: grid; gap: 12px; align-content: start; padding: 2px 6px 4px 2px; margin-right: -6px; }
  #qres::-webkit-scrollbar { width: 6px; } #qres::-webkit-scrollbar-thumb { background: var(--line); border-radius: 6px; }
  .hit { display: grid; gap: 10px; padding: 14px 16px; border: 1px solid var(--line); border-radius: 14px; background: var(--card); transition: .15s; }
  .hit:hover { border-color: #9ec0f5; box-shadow: var(--shadow); }
  .hit .name { font-weight: 600; font-size: 14.5px; word-break: break-all; line-height: 1.35; }
  .hit .tags { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .hit .tag { font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px; background: var(--soft); color: var(--muted); }
  .hit .tag.type { background: var(--accent); color: #fff; }
  .hit .tag.ok { background: var(--ok-bg); color: var(--ok); } .hit .tag.warn { background: var(--warn-bg); color: var(--warn); } .hit .tag.bad { background: var(--bad-bg); color: var(--bad); }
  .hit .when { margin-left: auto; font-size: 12px; color: var(--muted); font-weight: 400; background: none; padding: 0; }
  .hit dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 18px; margin: 0; padding-top: 10px; border-top: 1px solid var(--line); }
  .hit dl div { min-width: 0; }
  .hit dt { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
  .hit dd { margin: 1px 0 0; font-size: 13px; font-weight: 600; word-break: break-word; }
  .hit mark { background: var(--warn-bg); color: inherit; border-radius: 3px; padding: 0 2px; }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
  .chips:empty { display: none; }
  .chip { font: inherit; font-size: 12.5px; font-weight: 600; padding: 4px 12px; border-radius: 999px; border: 1px solid var(--line); background: var(--card); color: var(--muted); cursor: pointer; transition: .15s; }
  .chip:hover { border-color: #9ec0f5; color: var(--text); }
  .chip.on { background: var(--accent); border-color: var(--accent); color: #fff; }
  .chip small { font-weight: 500; opacity: .75; margin-left: 4px; }
  .hit.slim { padding: 10px 16px; gap: 6px; }
  .hit.slim .name { font-size: 14px; }
  .empty { text-align: center; color: var(--muted); font-size: 14px; padding: 40px 10px; }
  @media (max-width: 980px) { .center.stack { grid-template-columns: 1fr; grid-template-rows: none; min-height: 0; } .find { contain: none; max-height: 640px; } }
  @media (max-width: 640px) { .find { padding: 20px 16px; } .hit dl { grid-template-columns: 1fr; } }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }
  @media print { .topbar, .actions, .cats { display: none; } body { background: #fff; } }
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
<div class="topbar {{ (session('result') || session('batch') || isset($waiting)) ? '' : 'wide' }}"><div class="in">
  <a class="brand" href="{{ route('scan.index') }}"><i>
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>
  </i>AI Document Scanner</a>
  @if (session('result') || session('batch'))<div class="actions"><button type="button" class="btn sm ghost" onclick="window.print()">Print</button><a class="btn sm" href="{{ route('scan.index') }}">Scan another</a></div>@endif
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
      <div class="tiles">
        <span class="tile"><b>{{ collect($b['items'])->filter(fn ($i) => isset($i['result']))->count() }}</b>parsed</span>
        <span class="tile"><b>{{ collect($b['items'])->filter(fn ($i) => isset($i['error']))->count() }}</b>failed</span>
        <span class="tile"><b>{{ collect($b['items'])->filter(fn ($i) => in_array($i['result']['expiry']['status'] ?? '', ['expired', 'expiring_soon']))->count() }}</b>need attention (expired / expiring)</span>
        <span class="tile"><b>{{ $b['skipped'] }}</b>skipped</span>
      </div>
      <div class="sum" style="display:none">
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
              @php $zs = $r['categories'] ?? []; @endphp
              @forelse ($zs as $section)
                @if (count($zs) > 1)<div class="sum" style="margin:10px 0 2px"><b>{{ $section['category'] }}</b> · {{ round(($section['confidence'] ?? 0) * 100) }}% match</div>@endif
                @foreach ($section['metadata'] ?? [] as $key => $value)
                  <div class="row"><span class="k">{{ \Illuminate\Support\Str::headline($key) }}</span>
                    <span class="v {{ ($value === null || $value === '') ? 'na' : '' }}">{{ ($value === null || $value === '') ? 'Not found' : $value }}</span></div>
                @endforeach
              @empty
                @forelse ($r['metadata'] ?? [] as $key => $value)
                  <div class="row"><span class="k">{{ \Illuminate\Support\Str::headline($key) }}</span>
                    <span class="v {{ ($value === null || $value === '') ? 'na' : '' }}">{{ ($value === null || $value === '') ? 'Not found' : $value }}</span></div>
                @empty
                  <div class="sum">No details extracted.</div>
                @endforelse
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
    $sections = $r['categories'] ?? [];
    if (! $sections && ($r['document_type'] ?? null)) {
        $sections = [['category' => $r['document_type'], 'confidence' => $conf, 'metadata' => $meta, 'keywords_detected' => []]];
    }
    $foundCategories = collect($sections)->pluck('category')->all();
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
        <div class="actions">
          <button type="button" class="btn sm ghost" id="dl">Download JSON</button>
        </div>
      </div>
      <div class="ring">
        <svg width="112" height="112" viewBox="0 0 104 104">
          <circle class="track" cx="52" cy="52" r="44" fill="none" stroke-width="9"/>
          <circle cx="52" cy="52" r="44" fill="none" stroke-width="9" stroke-linecap="round" stroke="{{ $ringColor }}"
                  stroke-dasharray="{{ $circ }}" stroke-dashoffset="{{ $circ * (1 - min(max($conf, 0), 1)) }}"/>
        </svg>
        <div class="num"><div><b>{{ round($conf * 100) }}%</b><span>{{ $band[1] }} match</span></div></div>
      </div>
    </div>

    <div class="cats sm">
      @foreach ($categories as $name => $desc)<div class="cat {{ in_array($name, $foundCategories, true) ? 'on' : '' }}"><b>{{ $name }}</b>{{ $desc }}</div>@endforeach
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
      <div class="sections">
        @forelse ($sections as $section)
          @php $sc = (float) ($section['confidence'] ?? 0); @endphp
          <div class="card">
            <h2>{{ $section['category'] }} <span class="badge {{ $sc >= 0.5 ? 'ok' : ($sc >= 0.25 ? 'warn' : 'bad') }}">{{ round($sc * 100) }}% match</span></h2>
            @forelse ($section['metadata'] ?? [] as $key => $value)
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
              <div class="v na" style="color:var(--muted)">No details could be extracted for this category.</div>
            @endforelse
            @if (! empty($section['keywords_detected']))
              <div class="chips" style="margin-top:12px">@foreach ($section['keywords_detected'] as $kw)<span class="chip">{{ $kw }}</span>@endforeach</div>
            @endif
          </div>
        @empty
          <div class="card">
            <h2>Extracted details</h2>
            <div class="v na" style="color:var(--muted)">No details could be extracted from this document.</div>
          </div>
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
      <h2>Keywords detected ({{ collect($sections)->pluck('keywords_detected')->flatten()->unique()->count() ?: count($r['keywords_detected'] ?? []) }})</h2>
      <div class="chips">
        @forelse (collect($sections)->pluck('keywords_detected')->flatten()->unique()->all() ?: ($r['keywords_detected'] ?? []) as $kw)<span class="chip">{{ $kw }}</span>@empty<span style="color:var(--muted)">None</span>@endforelse
      </div>
    </div>

    <div class="card">
      <details>
        <summary>Raw response (JSON)</summary>
        <pre>{{ json_encode($r, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) }}</pre>
      </details>
    </div>
  </div>

@elseif (isset($waiting))
  <div class="center">
    <div class="card up wait">
      <div class="orb"></div>
      <h1>Scanning your <em>document</em></h1>
      <p class="sub" id="wmsg">Reading text, detecting type and extracting details…</p>
      <div class="bar indet" id="bar" style="margin-top:26px"><i></i></div>
      <p class="sub" id="wprog">Waiting in queue…</p>
    </div>
  </div>
  <script>
    (function poll() {
      fetch(@json(route('scan.status', $waiting)), { headers: { Accept: 'application/json' } })
        .then(r => r.json())
        .then(d => {
          if (d.done) { document.getElementById('wprog').textContent = 'Done! Opening result…'; location.href = @json(route('scan.result', $waiting)); return; }
          const bar = document.getElementById('bar');
          if (d.total > 1) {
            bar.classList.remove('indet');
            bar.firstElementChild.style.width = Math.max(8, Math.round(d.finished / d.total * 100)) + '%';
            document.getElementById('wprog').textContent = d.finished + ' of ' + d.total + ' documents scanned';
          } else {
            document.getElementById('wprog').textContent = 'Processing…';
          }
          setTimeout(poll, 1500);
        })
        .catch(() => setTimeout(poll, 3000));
    })();
  </script>
@else
  <div class="center stack">
    <form method="POST" action="{{ route('scan.run') }}" enctype="multipart/form-data" id="form" class="card up">
      @csrf
      <span class="eyebrow">Private · runs on your machine</span>
      <h1>Turn documents into <em>structured data</em></h1>
      <p>Upload one document, or a ZIP with many (vehicle, GST, company…).</p>
      <input type="file" name="file" id="file" hidden accept=".zip,.pdf,.jpg,.jpeg,.png,.tif,.tiff,.docx,.doc,.pptx,.ppt,.txt">
      <div id="drop">
        <div id="empty">
          <div class="ico"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4m0 0L7 9m5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg></div>
          <div class="t">Drop a file or a ZIP folder here, or click to browse</div>
          <div class="h">ZIP up to 50 MB · single file up to 20 MB</div>
          <div class="formats"><span>PDF</span><span>PNG</span><span>JPG</span><span>TIFF</span><span>DOCX</span><span>PPTX</span><span>TXT</span><span>ZIP</span></div>
        </div>
        <div id="picked"><span class="ext" id="pext"></span><br><span id="pname"></span><small id="psize"></small></div>
      </div>
      <button type="submit" class="btn" id="go" disabled><span class="spin"></span><span id="golabel">Scan document</span></button>
      @if ($errors->any())<div class="err">{{ $errors->first() }}</div>@endif
      <div class="steps"><span><b>1</b>Upload</span><span><b>2</b>Auto-scan (OCR)</span><span><b>3</b>Review &amp; copy details</span></div>
      <div class="cats">
        @foreach ($categories as $name => $desc)<div class="cat"><b>{{ $name }}</b>{{ $desc }}</div>@endforeach
      </div>
    </form>

    <div class="card find">
      <div class="head"><h2>Search scanned documents</h2><span class="count" id="qcount" hidden></span></div>
      <div class="field">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
        <input type="search" id="q" placeholder="Search by name, number, type, country, keyword…" autocomplete="off">
      </div>
      <div class="chips" id="qtypes"></div>
      <div class="chips" id="qstatus"></div>
      <div class="meta" id="qmeta"></div>
      <div id="qres"></div>
    </div>
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
        document.getElementById('pext').textContent = (f.name.split('.').pop() || '').toUpperCase();
        document.getElementById('psize').textContent = size(f.size) + (tooBig(f) ? ' · too large, max ' + (isZip(f) ? '50' : '20') + ' MB' : '');
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
  const q = document.getElementById('q');
  if (q) {
    const out = document.getElementById('qres'), meta = document.getElementById('qmeta');
    const esc = t => String(t ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const words = () => q.value.trim().split(/\s+/).filter(Boolean).map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const mark = t => { const w = words(); const e = esc(t); return w.length ? e.replace(new RegExp('(' + w.join('|') + ')', 'gi'), '<mark>$1</mark>') : e; };
    const label = k => k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const statusCls = { valid: 'ok', expiring_soon: 'warn', expired: 'bad' };
    const count = document.getElementById('qcount');
    const types = document.getElementById('qtypes'), stats = document.getElementById('qstatus');
    let fType = '', fStatus = '';
    const STATUSES = [['valid', 'Valid'], ['expiring_soon', 'Expiring soon'], ['expired', 'Expired']];
    const chip = (kind, value, text, n) => '<button type="button" class="chip' + ((kind === 'type' ? fType : fStatus) === value ? ' on' : '') + '" data-' + kind + '="' + esc(value) + '">' + esc(text) + (n != null ? '<small>' + n + '</small>' : '') + '</button>';
    const renderChips = d => {
      const entries = Object.entries(d.types || {});
      const total = entries.reduce((a, [, n]) => a + n, 0);
      types.innerHTML = entries.length > 1 || fType
        ? chip('type', '', 'All', total) + entries.sort((a, b) => b[1] - a[1]).map(([t, n]) => chip('type', t || 'unknown', t || 'Unknown', n)).join('')
        : '';
      stats.innerHTML = total || fStatus ? chip('status', '', 'Any expiry') + STATUSES.map(([v, t]) => chip('status', v, t)).join('') : '';
    };
    const render = d => {
      renderChips(d);
      count.hidden = !d.count; count.textContent = d.count;
      const filtered = fType || fStatus;
      meta.textContent = d.query ? (d.count ? d.count + ' result' + (d.count > 1 ? 's' : '') + ' for “' + d.query + '”' : '') : (d.count ? (filtered ? d.count + ' document' + (d.count > 1 ? 's' : '') : 'Latest scanned documents') : '');
      if (!d.count) { out.innerHTML = '<div class="empty">' + (d.query || filtered ? 'No documents match' + (d.query ? ' “' + esc(d.query) + '”' : ' these filters') + '.' : 'No documents scanned yet.<br>Upload one on the left, then search it here, e.g. “petrol” or “HR06”.') + '</div>'; return; }
      out.innerHTML = d.documents.map(x => {
        const w = words().map(t => t.toLowerCase());
        const hit = ([k, v]) => w.some(t => String(v).toLowerCase().includes(t) || label(k).toLowerCase().includes(t));
        const details = Object.entries(x.metadata).filter(([, v]) => v).filter(e => !w.length || hit(e)).map(([k, v]) => '<div><dt>' + esc(label(k)) + '</dt><dd>' + mark(v) + '</dd></div>').join('');
        const known = x.expiry_status && x.expiry_status !== 'unknown';
        return '<div class="hit' + (details ? '' : ' slim') + '"><div class="name">' + mark(x.filename) + '</div><div class="tags">'
          + (x.document_type ? '<span class="tag type">' + mark(x.document_type) + '</span>' : '')
          + (x.country ? '<span class="tag">' + mark(x.country) + '</span>' : '')
          + (known ? '<span class="tag ' + (statusCls[x.expiry_status] || '') + '">' + esc(x.expiry_status.replace('_', ' ')) + (x.expiry_date ? ' · ' + esc(x.expiry_date) : '') + '</span>' : '')
          + '<span class="tag when">' + esc(x.scanned_at) + '</span></div>'
          + (details ? '<dl>' + details + '</dl>' : '') + '</div>';
      }).join('');
    };
    document.querySelector('.find').addEventListener('click', e => {
      const c = e.target.closest('.chip'); if (!c) return;
      if ('type' in c.dataset) fType = c.dataset.type; else fStatus = c.dataset.status;
      run();
    });
    let timer, seq = 0;
    const run = () => {
      const n = ++seq;
      fetch(@json(route('scan.search')) + '?q=' + encodeURIComponent(q.value) + '&type=' + encodeURIComponent(fType) + '&status=' + encodeURIComponent(fStatus), { headers: { Accept: 'application/json' } })
        .then(r => r.json()).then(d => { if (n === seq) render(d); }).catch(() => {});
    };
    q.oninput = () => { clearTimeout(timer); timer = setTimeout(run, 250); };
    run();
  }
  const dl = document.getElementById('dl');
  if (dl) dl.onclick = () => {
    const pre = document.querySelector('details pre'); if (!pre) return;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([pre.textContent], { type: 'application/json' }));
    a.download = 'scan-result.json'; a.click(); URL.revokeObjectURL(a.href);
  };
  document.querySelectorAll('.cp').forEach(b => b.onclick = async () => {
    try { await navigator.clipboard.writeText(b.dataset.copy); b.style.color = 'var(--ok)'; setTimeout(() => b.style.color = '', 1200); } catch (e) {}
  });
</script>
</body>
</html>
