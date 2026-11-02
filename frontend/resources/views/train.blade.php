<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Train Categories · AI Document Scanner</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: light;
    --bg: #f2f7ff; --card: #ffffff; --text: #0f2540; --muted: #5f7390; --line: #dce8f7; --soft: #eaf2ff;
    --accent: #2563eb; --accent-2: #1d4ed8; --accent-soft: #e2edff;
    --ok: #15803d; --ok-bg: #e6f6ec; --warn: #b45309; --warn-bg: #fdf3dc; --bad: #b91c1c; --bad-bg: #fdecec;
    --shadow: 0 1px 2px rgba(37,99,235,.05), 0 8px 24px rgba(37,99,235,.08);
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: linear-gradient(180deg, #e8f1ff 0%, var(--bg) 360px); background-attachment: fixed; color: var(--text); font: 15px/1.55 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; min-height: 100vh; }
  @keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  .rise { animation: rise .4s ease both; }

  .topbar { position: sticky; top: 0; z-index: 10; background: color-mix(in srgb, var(--card) 82%, transparent); backdrop-filter: blur(12px); border-bottom: 1px solid var(--line); }
  .topbar .in { max-width: 1240px; margin: 0 auto; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }
  .brand { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 16px; color: var(--text); text-decoration: none; letter-spacing: -.01em; }
  .brand i { width: 34px; height: 34px; border-radius: 10px; background: var(--accent); color: #fff; display: grid; place-items: center; box-shadow: 0 6px 16px rgba(37,99,235,.35); }
  .btn { background: var(--accent); color: #fff; border: 0; border-radius: 12px; padding: 10px 18px; font: inherit; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 8px; transition: transform .12s, box-shadow .12s, opacity .12s, background .12s; box-shadow: 0 6px 18px rgba(37,99,235,.3); }
  .btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(37,99,235,.4); }
  .btn:disabled { opacity: .45; cursor: not-allowed; box-shadow: none; }
  .btn.sm { padding: 7px 13px; font-size: 13.5px; border-radius: 10px; }
  .btn.ghost { background: var(--card); color: var(--text); border: 1px solid var(--line); box-shadow: none; }
  .btn.ghost:hover:not(:disabled) { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); box-shadow: none; }
  .btn.danger { color: var(--bad); }
  .btn.danger:hover:not(:disabled) { border-color: var(--bad); color: var(--bad); background: var(--bad-bg); }

  .wrap { max-width: 1240px; margin: 0 auto; padding: 28px 20px 70px; }
  .hero { position: relative; overflow: hidden; border-radius: 24px; padding: 32px 34px; margin-bottom: 22px; color: #fff; background: radial-gradient(900px 300px at 90% -20%, rgba(255,255,255,.22), transparent 60%), linear-gradient(120deg, #1d4ed8 0%, #2563eb 55%, #3b82f6 100%); box-shadow: 0 18px 40px rgba(37,99,235,.28); display: flex; justify-content: space-between; align-items: center; gap: 24px; flex-wrap: wrap; }
  .hero h1 { font-size: 34px; letter-spacing: -.035em; line-height: 1.12; margin: 0 0 8px; font-weight: 800; }
  .hero p { margin: 0; max-width: 560px; color: rgba(255,255,255,.85); font-size: 15.5px; }
  .stats { display: flex; gap: 10px; flex-wrap: wrap; }
  .stat { background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28); backdrop-filter: blur(6px); border-radius: 16px; padding: 12px 20px; min-width: 120px; }
  .stat b { display: block; font-size: 28px; letter-spacing: -.03em; line-height: 1.15; }
  .stat span { font-size: 12.5px; color: rgba(255,255,255,.82); font-weight: 500; }

  .card { background: var(--card); border-radius: 22px; box-shadow: var(--shadow); padding: 26px; border: 1px solid var(--line); }
  .sec { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; margin: 30px 2px 14px; }
  .sec h2 { margin: 0; font-size: 20px; letter-spacing: -.02em; }
  .sec p { margin: 0; color: var(--muted); font-size: 13.5px; }

  /* training panel */
  .train form { display: grid; grid-template-columns: minmax(0, 5fr) minmax(0, 7fr); gap: 30px; }
  @media (max-width: 860px) { .train form { grid-template-columns: 1fr; gap: 22px; } }
  .col { display: flex; flex-direction: column; min-width: 0; }
  .lab { display: flex; align-items: center; gap: 10px; font-weight: 700; margin: 0 0 10px; }
  .lab b { flex: none; width: 24px; height: 24px; border-radius: 50%; background: var(--accent); color: #fff; display: grid; place-items: center; font-size: 12.5px; }
  .lab small { font-weight: 500; color: var(--muted); }
  input[type=text], input[type=search] { width: 100%; border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; font: inherit; color: var(--text); background: #fff; transition: border-color .12s, box-shadow .12s; }
  input[type=text]:focus, input[type=search]:focus { outline: 0; border-color: var(--accent); box-shadow: 0 0 0 4px var(--accent-soft); }
  .hint { color: var(--muted); font-size: 13px; margin: 8px 0 0; }
  .suggest { display: flex; gap: 6px; flex-wrap: wrap; margin: 12px 0 0; }
  .suggest button { border: 1px solid var(--line); background: var(--card); border-radius: 999px; padding: 3px 12px; font: inherit; font-size: 12.5px; color: var(--muted); cursor: pointer; transition: .12s; }
  .suggest button:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-soft); }
  .go { margin-top: auto; width: 100%; padding: 15px; font-size: 16px; border-radius: 14px; }
  .spacer { height: 22px; }
  .field-err { color: var(--bad); font-size: 13px; margin: 8px 0 0; }

  #drop { border: 2px dashed #a9c6ee; border-radius: 18px; padding: 30px 16px; text-align: center; cursor: pointer; background: var(--soft); transition: .18s; }
  #drop:hover, #drop.over { border-color: var(--accent); background: #f4f8ff; }
  #drop .ico { width: 52px; height: 52px; border-radius: 16px; background: var(--card); display: grid; place-items: center; margin: 0 auto 12px; box-shadow: var(--shadow); color: var(--accent); }
  #drop b { display: block; font-size: 16px; }
  #drop span { color: var(--muted); font-size: 13px; }
  #picked { margin: 12px 0 0; padding: 0; list-style: none; display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 8px; max-height: 190px; overflow: auto; }
  #picked:empty { display: none; }
  #picked li { display: flex; align-items: center; gap: 8px; background: var(--soft); border-radius: 10px; padding: 6px 6px 6px 10px; font-size: 13px; min-width: 0; }
  #picked .ext { flex: none; background: var(--accent); color: #fff; border-radius: 6px; font-size: 10px; font-weight: 700; padding: 1px 6px; letter-spacing: .04em; text-transform: uppercase; }
  #picked .fn { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  #picked .sz { color: var(--muted); font-size: 11.5px; flex: none; }
  #picked button { flex: none; border: 0; background: transparent; color: var(--muted); font-size: 18px; line-height: 1; cursor: pointer; border-radius: 6px; width: 24px; height: 24px; }
  #picked button:hover { background: var(--bad-bg); color: var(--bad); }
  #count { margin: 8px 0 0; font-size: 13px; color: var(--muted); }

  .note { border-radius: 12px; padding: 12px 16px; font-size: 14px; margin-bottom: 16px; }
  .note.bad { background: var(--bad-bg); color: var(--bad); } .note.ok { background: var(--ok-bg); color: var(--ok); }
  .result { background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 18px 22px; margin-bottom: 20px; box-shadow: var(--shadow); display: flex; gap: 16px; }
  .result .tick { flex: none; width: 40px; height: 40px; border-radius: 50%; display: grid; place-items: center; font-size: 20px; font-weight: 700; }
  .result.ok .tick { background: var(--ok-bg); color: var(--ok); } .result.warn .tick { background: var(--warn-bg); color: var(--warn); }
  .result h3 { margin: 0; font-size: 16.5px; letter-spacing: -.01em; }
  .result p { margin: 2px 0 8px; color: var(--muted); font-size: 13.5px; }
  .report { margin: 0; padding: 0; list-style: none; font-size: 13px; display: grid; gap: 2px; }
  .report li { display: flex; justify-content: space-between; gap: 14px; word-break: break-all; }
  .report .yes { color: var(--ok); font-weight: 600; flex: none; } .report .no { color: var(--bad); flex: none; text-align: right; }

  /* categories */
  .tools { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  .tools input { width: 250px; padding: 9px 14px; }
  .tabs { display: flex; gap: 4px; background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 4px; }
  .tabs button { border: 0; background: transparent; border-radius: 9px; padding: 6px 12px; font: inherit; font-size: 13.5px; font-weight: 600; color: var(--muted); cursor: pointer; }
  .tabs button.on { background: var(--accent); color: #fff; }
  .tabs small { font-weight: 600; opacity: .75; margin-left: 4px; }
  .cats { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }
  @media (max-width: 480px) { .cats { grid-template-columns: 1fr; } }
  .cat { border: 1px solid var(--line); border-radius: 20px; padding: 20px; background: var(--card); box-shadow: var(--shadow); display: flex; flex-direction: column; gap: 14px; transition: transform .15s, box-shadow .15s; }
  .cat:hover { transform: translateY(-2px); box-shadow: 0 14px 30px rgba(37,99,235,.13); }
  .cat[hidden] { display: none; }
  .cat.auto { border: 1.5px dashed #e8c871; background: #fffdf6; }
  .cat .top { display: flex; align-items: center; gap: 14px; }
  .cat .av { flex: none; width: 46px; height: 46px; border-radius: 14px; display: grid; place-items: center; font-weight: 800; font-size: 19px; background: var(--accent-soft); color: var(--accent); }
  .cat.trained .av { background: var(--ok-bg); color: var(--ok); } .cat.auto .av { background: var(--warn-bg); color: var(--warn); }
  .cat .info { flex: 1; min-width: 0; }
  .cat .name { font-weight: 700; font-size: 17px; letter-spacing: -.015em; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .meta { color: var(--muted); font-size: 13px; }
  .badge { flex: none; border-radius: 999px; padding: 2px 11px; font-size: 12px; font-weight: 600; background: var(--soft); color: var(--accent); }
  .badge.trained { background: var(--ok-bg); color: var(--ok); } .badge.auto { background: var(--warn-bg); color: var(--warn); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chips span { background: var(--soft); border-radius: 8px; padding: 2px 10px; font-size: 12.5px; }
  .chips span.new { background: var(--ok-bg); color: var(--ok); }
  .chips .more { background: transparent; border: 1px dashed #b9d1f4; color: var(--accent); cursor: pointer; font: inherit; font-size: 12.5px; font-weight: 600; border-radius: 8px; padding: 2px 10px; }
  .chips .more:hover { background: var(--accent-soft); }
  .chips [hidden] { display: none; }
  .foot { margin-top: auto; border-top: 1px solid var(--line); padding-top: 14px; display: flex; gap: 8px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
  .foot form { display: flex; gap: 8px; align-items: center; margin: 0; }
  .foot form.grow { flex: 1; }
  .foot input[type=text] { padding: 7px 11px; font-size: 13.5px; border-radius: 10px; }
  .foot:empty { display: none; }
  .legend { color: var(--muted); font-size: 12.5px; margin-top: 18px; display: flex; gap: 16px; flex-wrap: wrap; }
  .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; background: var(--ok-bg); border: 1px solid var(--ok); margin-right: 6px; vertical-align: -1px; }
  .legend i.base { background: var(--soft); border-color: #b9d1f4; }
  .empty { color: var(--muted); text-align: center; padding: 40px 0; }
  .empty b { display: block; color: var(--text); margin-bottom: 4px; }

  /* training overlay */
  #busy { position: fixed; inset: 0; z-index: 50; background: rgba(15,37,64,.45); backdrop-filter: blur(3px); display: none; place-items: center; padding: 20px; }
  #busy.on { display: grid; }
  #busy .box { background: var(--card); border-radius: 22px; padding: 34px 38px; text-align: center; max-width: 380px; box-shadow: 0 24px 70px rgba(15,37,64,.35); }
  #busy .orb { width: 64px; height: 64px; margin: 0 auto 18px; border-radius: 50%; border: 5px solid var(--line); border-top-color: var(--accent); animation: s 1s linear infinite; }
  @keyframes s { to { transform: rotate(360deg); } }
  #busy h3 { margin: 0 0 6px; font-size: 18px; letter-spacing: -.01em; } #busy p { margin: 0; color: var(--muted); font-size: 14px; }
  @media (max-width: 560px) { .hero { padding: 24px 20px; } .hero h1 { font-size: 27px; } .tools input { width: 100%; } }
</style>
</head>
<body>
@php
  $trainedDocs = collect($categories)->sum('trained_documents');
  $autoCount = collect($categories)->where('kind', 'auto')->count();
  $counts = ['all' => count($categories), 'built-in' => collect($categories)->where('kind', 'built-in')->count(), 'trained' => collect($categories)->where('kind', 'trained')->count(), 'auto' => $autoCount];
@endphp
<div class="topbar"><div class="in">
  <a class="brand" href="{{ route('scan.index') }}"><i>
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>
  </i>AI Document Scanner</a>
  <a class="btn sm ghost" href="{{ route('scan.index') }}">← Back to scanner</a>
</div></div>

<div class="wrap">
  <div class="hero rise">
    <div>
      <h1>Train categories</h1>
      <p>Upload a few sample documents and name the category. The scanner learns the wording on its own and recognises that kind of document straight away. No files to edit, no restart.</p>
    </div>
    <div class="stats">
      <div class="stat"><b>{{ $counts['all'] }}</b><span>categories</span></div>
      <div class="stat"><b>{{ $trainedDocs }}</b><span>documents learned</span></div>
      @if ($autoCount)<div class="stat"><b>{{ $autoCount }}</b><span>to review</span></div>@endif
    </div>
  </div>

  @if (session('status'))<div class="note ok rise">{{ session('status') }}</div>@endif
  @if ($loadError)<div class="note bad">{{ $loadError }}</div>@endif
  @error('action')<div class="note bad">{{ $message }}</div>@enderror

  @if (session('trained'))
    @php $t = session('trained'); $okCount = $t['trained_documents']; @endphp
    <div class="result {{ $okCount > 0 ? 'ok' : 'warn' }} rise">
      <div class="tick">{{ $okCount > 0 ? '✓' : '!' }}</div>
      <div style="flex:1;min-width:0">
        <h3>{{ $okCount > 0 ? 'Learned "'.$t['category'].'" from '.$okCount.' document'.($okCount === 1 ? '' : 's') : 'Nothing was learned' }}</h3>
        <p>{{ $okCount > 0 ? 'It will be recognised in the very next scan.' : 'None of the files had readable text.' }}</p>
        <ul class="report">
          @foreach ($t['files'] as $f)
            <li><span>{{ $f['filename'] }}</span>@if ($f['ok'])<span class="yes">learned</span>@else<span class="no">{{ $f['error'] }}</span>@endif</li>
          @endforeach
        </ul>
      </div>
    </div>
  @endif

  <section class="card train rise">
    <form method="POST" action="{{ route('train.store') }}" enctype="multipart/form-data" id="trainForm">
      @csrf
      <div class="col">
        <div class="lab"><b>1</b>Name the category</div>
        <input type="text" id="category" name="category" list="known" value="{{ old('category') }}" placeholder="e.g. Medical Prescription" maxlength="60" required autocomplete="off">
        <datalist id="known">@foreach ($categories as $c)<option value="{{ $c['name'] }}">@endforeach</datalist>
        <p class="hint">Pick an existing name to make it smarter, or type a new one.</p>
        @if (count($categories))
          <div class="suggest" aria-label="Existing categories">
            @foreach (collect($categories)->where('kind', '!=', 'auto')->take(6) as $c)<button type="button" data-name="{{ $c['name'] }}">{{ $c['name'] }}</button>@endforeach
          </div>
        @endif
        @error('category')<div class="field-err">{{ $message }}</div>@enderror
        <div class="spacer"></div>
        <button type="submit" class="btn go" id="go" disabled>Train category</button>
      </div>

      <div class="col">
        <div class="lab"><b>2</b>Add sample documents <small>· 3 to 10 work best</small></div>
        <div id="drop" role="button" tabindex="0">
          <div class="ico"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/></svg></div>
          <b>Drop files here or click to browse</b>
          <span>PDF, images, Word, PowerPoint, text, or a zip of them</span>
        </div>
        <input type="file" id="files" name="files[]" multiple hidden accept=".pdf,.jpg,.jpeg,.png,.tif,.tiff,.docx,.doc,.pptx,.ppt,.txt,.zip">
        <ul id="picked"></ul>
        <div id="count"></div>
        @error('files')<div class="field-err">{{ $message }}</div>@enderror
        @error('files.*')<div class="field-err">{{ $message }}</div>@enderror
      </div>
    </form>
  </section>

  <div class="sec">
    <div><h2>What the scanner knows</h2><p>Built-in, trained and auto-created categories</p></div>
    <div class="tools">
      <input type="search" id="q" placeholder="Search categories or keywords" aria-label="Search categories">
      <div class="tabs" id="tabs">
        @foreach (['all' => 'All', 'built-in' => 'Built-in', 'trained' => 'Trained', 'auto' => 'Auto'] as $key => $label)
          <button type="button" data-tab="{{ $key }}" class="{{ $key === 'all' ? 'on' : '' }}">{{ $label }}<small>{{ $counts[$key] }}</small></button>
        @endforeach
      </div>
    </div>
  </div>

  <div class="cats" id="cats">
    @forelse ($categories as $c)
      @php $trainedWords = $c['trained_keywords'] ?? []; $words = $c['keywords']; @endphp
      <div class="cat {{ $c['kind'] === 'built-in' ? '' : $c['kind'] }}" data-kind="{{ $c['kind'] }}" data-search="{{ strtolower($c['name'].' '.implode(' ', $words)) }}">
        <div class="top">
          <div class="av">{{ strtoupper(mb_substr($c['name'], 0, 1)) }}</div>
          <div class="info">
            <span class="name" title="{{ $c['name'] }}">{{ $c['name'] }}</span>
            <div class="meta">
              @if ($c['kind'] === 'auto'){{ $c['documents'] }} document{{ $c['documents'] === 1 ? '' : 's' }} grouped automatically
              @else {{ $c['trained_documents'] }} trained document{{ $c['trained_documents'] === 1 ? '' : 's' }}@if (! empty($c['updated_at'])) · {{ \Illuminate\Support\Carbon::parse($c['updated_at'])->diffForHumans() }}@endif
              @endif
            </div>
          </div>
          <span class="badge {{ $c['kind'] === 'built-in' ? '' : $c['kind'] }}">{{ $c['kind'] === 'auto' ? 'auto-created' : $c['kind'] }}</span>
        </div>
        <div class="chips">
          @foreach ($words as $i => $k)<span class="{{ in_array($k, $trainedWords, true) ? 'new' : '' }}" @if ($i >= 6) hidden data-extra @endif>{{ $k }}</span>@endforeach
          @if (count($words) > 6)<button type="button" class="more" data-more="{{ count($words) - 6 }}">+{{ count($words) - 6 }} more</button>@endif
        </div>
        @if ($c['kind'] === 'auto' || $c['kind'] !== 'built-in' || $c['trained_documents'] > 0)
          <div class="foot">
            @if ($c['kind'] === 'auto')
              <form method="POST" action="{{ route('train.promote', $c['name']) }}" class="grow">@csrf
                <input type="text" name="name" value="{{ $c['name'] }}" maxlength="60" aria-label="Category name" style="flex:1;min-width:0">
                <button class="btn sm" type="submit">Confirm</button>
              </form>
            @endif
            <form method="POST" action="{{ route('train.destroy', $c['name']) }}" data-confirm="{{ $c['kind'] === 'built-in' ? 'Remove the extra training for' : 'Delete' }} &quot;{{ $c['name'] }}&quot;?">@csrf @method('DELETE')
              <button class="btn sm ghost danger" type="submit">{{ $c['kind'] === 'built-in' ? 'Reset training' : 'Delete' }}</button>
            </form>
          </div>
        @endif
      </div>
    @empty
      <div class="empty"><b>No categories yet</b>Train your first one above.</div>
    @endforelse
  </div>
  <div class="empty" id="none" hidden><b>No match</b>Try another search or filter.</div>
  <div class="legend"><span><i></i>learned from your documents</span><span><i class="base"></i>built-in keyword</span></div>
</div>

<div id="busy"><div class="box"><div class="orb"></div><h3>Reading and learning…</h3><p>Extracting text, running OCR where needed and mining keywords. This can take a minute for scanned files.</p></div></div>

<script>
  const $ = id => document.getElementById(id);
  const input = $('files'), drop = $('drop'), list = $('picked'), go = $('go'), form = $('trainForm'), category = $('category'), count = $('count');
  let files = [];

  const sync = () => { const dt = new DataTransfer(); files.forEach(f => dt.items.add(f)); input.files = dt.files; };
  const render = () => {
    list.innerHTML = '';
    files.forEach((f, i) => {
      const li = document.createElement('li');
      const ext = (f.name.split('.').pop() || '').slice(0, 4);
      li.innerHTML = '<span class="ext"></span><span class="fn"></span><span class="sz"></span><button type="button" title="Remove" aria-label="Remove file">×</button>';
      li.children[0].textContent = ext; li.children[1].textContent = f.name; li.children[1].title = f.name;
      li.children[2].textContent = f.size > 1048576 ? (f.size / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(f.size / 1024)) + ' KB';
      li.children[3].onclick = () => { files.splice(i, 1); sync(); render(); };
      list.appendChild(li);
    });
    count.textContent = files.length ? files.length + ' file' + (files.length === 1 ? '' : 's') + ' ready' : '';
    go.disabled = !files.length || !category.value.trim();
  };
  const add = picked => { [...picked].forEach(f => { if (!files.some(x => x.name === f.name && x.size === f.size)) files.push(f); }); sync(); render(); };

  drop.addEventListener('click', () => input.click());
  drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); } });
  ['dragover', 'dragenter'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', e => add(e.dataTransfer.files));
  input.addEventListener('change', () => add(input.files));
  category.addEventListener('input', render);
  document.querySelectorAll('.suggest button').forEach(b => b.addEventListener('click', () => { category.value = b.dataset.name; render(); category.focus(); }));
  form.addEventListener('submit', () => { go.disabled = true; $('busy').classList.add('on'); });
  window.addEventListener('pageshow', () => $('busy').classList.remove('on'));

  // category list: search + filter tabs + expandable keywords + delete confirmation
  let tab = 'all';
  const cards = [...document.querySelectorAll('#cats .cat')];
  const apply = () => {
    const q = $('q').value.trim().toLowerCase(); let shown = 0;
    cards.forEach(c => { const on = (tab === 'all' || c.dataset.kind === tab) && (!q || c.dataset.search.includes(q)); c.hidden = !on; shown += on; });
    $('none').hidden = shown > 0 || !cards.length;
  };
  $('q').addEventListener('input', apply);
  document.querySelectorAll('#tabs button').forEach(b => b.addEventListener('click', () => {
    tab = b.dataset.tab; document.querySelectorAll('#tabs button').forEach(x => x.classList.toggle('on', x === b)); apply();
  }));
  document.querySelectorAll('.more').forEach(b => b.addEventListener('click', () => {
    const open = b.dataset.open !== '1';
    b.parentElement.querySelectorAll('[data-extra]').forEach(s => s.hidden = !open);
    b.dataset.open = open ? '1' : ''; b.textContent = open ? 'Show less' : '+' + b.dataset.more + ' more';
  }));
  document.querySelectorAll('form[data-confirm]').forEach(f => f.addEventListener('submit', e => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));
  render();
</script>
</body>
</html>
