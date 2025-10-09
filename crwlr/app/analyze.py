import re


RULE_PACKS = {
    'base': [
        {
            'id': 'data_sale',
            'label': 'Data Sale/Sharing',
            'severity': 'high',
            'regex': r'\b(sell|sale|sharing|share|sold)\b.*\b(data|information|personal)\b|\b(data|information|personal)\b.*\b(sell|sale|sharing|share|sold)\b'
        },
        {
            'id': 'arb_waiver',
            'label': 'Arbitration / Class Action Waiver',
            'severity': 'medium',
            'regex': r'\barbitrat(e|ion|or)\b|\bclass action waiver\b|\bwaive.*class action\b'
        },
        {
            'id': 'tracking',
            'label': 'Tracking/Advertising',
            'severity': 'medium',
            'regex': r'\b(cookie|cookies|tracking|track|beacon|pixel|advertising|advertise)\b'
        },
        {
            'id': 'location',
            'label': 'Location Data',
            'severity': 'medium',
            'regex': r'\b(location|geolocation|gps|geographic)\b.*\b(data|information|track)\b|\b(collect|use|process)\b.*\b(location|geolocation)\b'
        },
        {
            'id': 'retention',
            'label': 'Data Retention',
            'severity': 'low',
            'regex': r'\b(retain|retention|keep|store|storing)\b.*\b(data|information|records)\b'
        },
        {
            'id': 'children',
            'label': "Children's Data (COPPA)",
            'severity': 'high',
            'regex': r'\b(child(ren)?|minor|minors|under (13|18)|kids|coppa)\b'
        }
    ]
}


def tag_section(text: str, packs: list[str]) -> list[dict]:
    tags = []
    text_lower = text.lower()
    
    for pack_name in packs:
        if pack_name not in RULE_PACKS:
            continue
        
        for rule in RULE_PACKS[pack_name]:
            pattern = re.compile(rule['regex'], re.IGNORECASE)
            if pattern.search(text_lower):
                tags.append({
                    'id': rule['id'],
                    'label': rule['label'],
                    'severity': rule['severity']
                })
    
    return tags


def analyze_sections(sections: list[dict], packs: list[str]) -> list[dict]:
    findings = []
    
    for section in sections:
        text = section['text']
        tags = tag_section(text, packs)
        
        if tags:
            snippet = text[:500] if len(text) > 500 else text
            
            findings.append({
                'heading': section['heading'],
                'text': text,
                'snippet': snippet,
                'tags': tags
            })
    
    return findings
