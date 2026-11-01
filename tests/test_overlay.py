from src.parse.extract import extract_html


def test_viewport_overlay_dropped_content_kept():
    html = """<html><body><main><h1>Scheme</h1><p>Real eligibility text that matters for citizens applying here today.</p>
    <div><div class="h-screen w-screen bg-black/20"><div class="p-6"><h3>You're being redirected</h3></div></div></div>
    <div class="fixed inset-0"><p>Cookie popup text</p></div></main></body></html>"""
    text = " ".join(b.text for b in extract_html(html).blocks)
    assert "Real eligibility text" in text
    assert "redirected" not in text and "Cookie popup" not in text


def test_wikipedia_references_and_navboxes_dropped():
    html = """<html><body><main><h1>Scheme</h1><p>The scheme pays a fixed amount every month to eligible households in the state.</p>
    <ol class="references"><li>↑ Study on Implementation - page 22</li></ol>
    <div class="navbox"><a>Related schemes</a></div><div class="reflist"><p>Retrieved 2020</p></div></main></body></html>"""
    text = " ".join(b.text for b in extract_html(html).blocks)
    assert "fixed amount every month" in text
    assert "Study on Implementation" not in text and "Related schemes" not in text and "Retrieved" not in text


def test_generic_or_empty_title_falls_back_to_h1():
    html = "<html><head><title>UX4G Accessibility Tool</title></head><body><h1><button></button></h1><h1>Old Age Pension Scheme</h1><p>Some body text here that is long enough to matter for the page.</p></body></html>"
    assert extract_html(html).title == "Old Age Pension Scheme"
    assert extract_html("<html><head><title>Real Title</title></head><body><p>x</p></body></html>").title == "Real Title"
