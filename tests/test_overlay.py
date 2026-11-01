from src.parse.extract import extract_html


def test_viewport_overlay_dropped_content_kept():
    html = """<html><body><main><h1>Scheme</h1><p>Real eligibility text that matters for citizens applying here today.</p>
    <div><div class="h-screen w-screen bg-black/20"><div class="p-6"><h3>You're being redirected</h3></div></div></div>
    <div class="fixed inset-0"><p>Cookie popup text</p></div></main></body></html>"""
    text = " ".join(b.text for b in extract_html(html).blocks)
    assert "Real eligibility text" in text
    assert "redirected" not in text and "Cookie popup" not in text
