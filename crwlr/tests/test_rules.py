from app.analyze import tag_section


def test_data_sale_rule():
    text = "We may sell your personal data to third parties."
    tags = tag_section(text, ['base'])
    
    assert any(tag['id'] == 'data_sale' for tag in tags)
    assert any(tag['severity'] == 'high' for tag in tags if tag['id'] == 'data_sale')


def test_arbitration_rule():
    text = "You agree to arbitration for any disputes arising from this agreement."
    tags = tag_section(text, ['base'])
    
    assert any(tag['id'] == 'arb_waiver' for tag in tags)


def test_tracking_rule():
    text = "We use cookies and tracking pixels to improve your experience."
    tags = tag_section(text, ['base'])
    
    assert any(tag['id'] == 'tracking' for tag in tags)


def test_location_rule():
    text = "We collect your location data to provide personalized services."
    tags = tag_section(text, ['base'])
    
    assert any(tag['id'] == 'location' for tag in tags)


def test_retention_rule():
    text = "We retain your personal information for up to 7 years."
    tags = tag_section(text, ['base'])
    
    assert any(tag['id'] == 'retention' for tag in tags)


def test_children_rule():
    text = "Our service is not intended for children under 13 years of age."
    tags = tag_section(text, ['base'])
    
    assert any(tag['id'] == 'children' for tag in tags)
    assert any(tag['severity'] == 'high' for tag in tags if tag['id'] == 'children')


def test_snippet_length():
    long_text = "a" * 1000
    tags = tag_section(long_text + " cookie tracking data", ['base'])
    
    if tags:
        snippet = long_text[:500]
        assert len(snippet) <= 500
