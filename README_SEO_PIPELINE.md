# Global SEO Content Pipeline - Documentation

## 📋 Overview

This automated pipeline generates SEO-optimized, localized pillar pages for **11 languages** targeting the keyword "new cameras 2026" across global markets. The system follows a **multi-agent architecture** inspired by CrewAI frameworks.

### Target Languages
- **es-ES** - Spain (Spanish)
- **it-IT** - Italy (Italian)
- **fr-FR** - France (French)
- **de-DE** - Germany (German)
- **ja-JP** - Japan (Japanese)
- **ko-KR** - South Korea (Korean)
- **zh-CN** - China (Simplified Chinese)
- **ar-SA** - Saudi Arabia (Arabic)
- **hi-IN** - India (Hindi)
- **tr-TR** - Turkey (Turkish)
- **ru-RU** - Russia (Russian)

---

## 🏗️ Architecture

### 7-Agent Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                    SEO Content Pipeline                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│   Keyword     │──▶│   Competitor    │──▶│   Content     │
│  Researcher   │   │    Analyzer     │   │  Strategist   │
└───────────────┘   └─────────────────┘   └───────────────┘
                             │
                             ▼
                  ┌───────────────────┐
                  │  Technical SEO &  │
                  │  Schema Architect │
                  └───────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│    EEAT       │◀──│    Content      │◀──│   Linking     │
│  Validator    │   │    Creator      │   │  Architect    │
└───────────────┘   └─────────────────┘   └───────────────┘
```

### Agent Roles

| Agent | Role | Temperature |
|-------|------|-------------|
| `keyword_researcher` | Identifies high-volume, low-competition keywords with local retailer terms | 0.3 |
| `competitor_analyzer` | Analyzes top 5 SERP results, identifies content gaps | 0.2 |
| `content_strategist` | Creates localized content briefs with cultural nuances | 0.6 |
| `tech_seo_auditor` | Generates JSON-LD schema (CollectionPage, FAQPage, BreadcrumbList) | 0.1 |
| `eeat_validator` | Validates Experience, Expertise, Authoritativeness, Trust signals | 0.4 |
| `content_creator` | Writes 4,000+ word HTML pillar pages in native language | 0.7 |
| `linking_architect` | Injects 15-25 contextual internal links | 0.2 |

---

## 📁 File Structure

```
/workspace/
├── global_seo_crew.yaml          # Multi-agent workflow configuration
├── output_schema.json            # Strict JSON schema for validation
├── global_seo_pipeline.py        # Python orchestration script
├── README.md                     # This documentation
└── workspace/                    # Generated output directory
    ├── es-ES/guias/
    │   └── seo-data-es-ES.json  # Intermediate SEO data for Spain
    ├── it-IT/guias/
    │   └── seo-data-it-IT.json  # Intermediate SEO data for Italy
    ├── fr-FR/guias/
    │   └── seo-data-fr-FR.json  # Intermediate SEO data for France
    ├── de-DE/guias/
    │   └── seo-data-de-DE.json  # Intermediate SEO data for Germany
    ├── ja-JP/guias/
    │   └── seo-data-ja-JP.json  # Intermediate SEO data for Japan
    ├── ko-KR/guias/
    │   └── seo-data-ko-KR.json  # Intermediate SEO data for Korea
    ├── zh-CN/guias/
    │   └── seo-data-zh-CN.json  # Intermediate SEO data for China
    ├── ar-SA/guias/
    │   └── seo-data-ar-SA.json  # Intermediate SEO data for Saudi Arabia
    ├── hi-IN/guias/
    │   └── seo-data-hi-IN.json  # Intermediate SEO data for India
    ├── tr-TR/guias/
    │   └── seo-data-tr-TR.json  # Intermediate SEO data for Turkey
    ├── ru-RU/guias/
    │   └── seo-data-ru-RU.json  # Intermediate SEO data for Russia
    └── pipeline-summary.json     # Complete pipeline execution summary
```

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install required dependencies
pip install pyyaml pathlib
```

### Execute the Pipeline

```bash
# Run for all 11 languages
python3 global_seo_pipeline.py

# Or run for specific languages only
python3 -c "
from global_seo_pipeline import GlobalSEOPipeline
pipeline = GlobalSEOPipeline('global_seo_crew.yaml')
results = pipeline.run_full_pipeline(['es-ES', 'de-DE', 'ja-JP'])
"
```

### Output Validation

The pipeline validates all outputs against `output_schema.json` to ensure:
- ✅ Meta titles under 60 characters
- ✅ Meta descriptions between 150-160 characters
- ✅ Valid JSON-LD schema (CollectionPage, FAQPage, BreadcrumbList)
- ✅ Minimum 2 hub links, 3 cluster links, 2 regional links
- ✅ 5+ long-tail keywords per language
- ✅ EEAT validation checklist (author box, methodology, locations, pros/cons, last updated)

---

## 📊 Generated Data Structure

Each language produces a JSON file with the following structure:

```json
{
  "language": "es-ES",
  "meta_data": {
    "title": "Nuevas Cámaras 2026: Guía Completa...",
    "description": "Descubre las nuevas cámaras 2026...",
    "canonical_url": "https://.../es-ES/guias/nuevas-camaras-2026/"
  },
  "schema_markup": {
    "collection_page": {...},
    "faq_page": {...},
    "breadcrumb_list": {...}
  },
  "content_brief": {
    "h2_outline": [...],
    "local_eeat_hooks": [...],
    "local_pricing_currency": "€",
    "local_retailers": ["Amazon.es", "El Corte Inglés", ...],
    "test_locations": ["Barcelona", "Madrid", ...],
    "target_word_count": 4000,
    "tone": "...",
    "target_audience": "..."
  },
  "internal_link_map": {
    "hub_links": [...],
    "cluster_links": [...],
    "regional_links": [...]
  },
  "keywords": {
    "primary": "nuevas cámaras 2026",
    "long_tail": [...],
    "search_intent": "commercial_investigation"
  },
  "competitor_data": {
    "competitor_gaps": [...],
    "avg_word_count": 2800,
    "recommended_h2s": [...],
    "missing_schema": [...],
    "content_quality_score": 6.5
  },
  "eeat_validation": {
    "author_box": true,
    "testing_methodology": true,
    "local_locations": true,
    "pros_and_cons": true,
    "last_updated": true
  }
}
```

---

## 🎯 Localization Features

### Currency & Pricing
Each market has localized currency symbols:
- € for EU (Spain, Italy, France, Germany)
- ¥ for Japan and China
- ₩ for South Korea
- ر.س for Saudi Arabia
- ₹ for India
- ₺ for Turkey
- ₽ for Russia

### Local Retailers
Pre-configured retailer networks for each market:
- **Spain**: Amazon.es, El Corte Inglés, Fnac España, MediaMarkt
- **Japan**: Yodobashi Camera, Bic Camera, Amazon.co.jp, Kakaku.com
- **Germany**: Amazon.de, MediaMarkt, Saturn, Foto Erhardt
- *(See `global_seo_pipeline.py` for complete list)*

### Test Locations
Localized testing scenarios for EEAT:
- **Spain**: Barcelona, Madrid, Costa del Sol, Pyrenees
- **Japan**: Tokyo, Osaka, Kyoto, Mount Fuji
- **India**: Delhi, Mumbai, Goa, Himalayas
- *(Each market has 4+ specific locations)*

---

## 🔧 Customization

### Adding New Languages

1. Add language code to `global_seo_crew.yaml`:
```yaml
target_languages: ["...","xx-XX"]
```

2. Add keyword mappings in `generate_keyword_research()`:
```python
"xx-XX": {
    "primary": "local keyword",
    "long_tail": [...],
    "search_intent": "commercial_investigation"
}
```

3. Add localization data in `generate_content_brief()`:
```python
"xx-XX": {
    "currency": "¤",
    "retailers": [...],
    "locations": [...]
}
```

4. Add schema content in `generate_schema_markup()`:
```python
"xx-XX": {
    "title": "...",
    "description": "...",
    "breadcrumb": [...],
    "faq": [...]
}
```

### Adjusting Temperature Settings

Modify agent temperatures in `global_seo_crew.yaml`:
```yaml
agents:
  - name: content_creator
    llm_config:
      model: "qwen-max"
      temperature: 0.7  # Increase for more creative output
```

---

## 📈 Performance Metrics

Pipeline execution summary (from `pipeline-summary.json`):

| Metric | Value |
|--------|-------|
| Total Languages | 11 |
| Success Rate | 100% |
| Avg Keywords per Language | 6 (1 primary + 5 long-tail) |
| Avg Internal Links | 7 per page |
| Schema Types | 3 (CollectionPage, FAQPage, BreadcrumbList) |
| EEAT Checks | 5 (all passed) |

---

## 🔍 SEO Best Practices Implemented

### On-Page SEO
- ✅ Primary keyword in H1 (first position)
- ✅ Meta description 150-160 characters
- ✅ H2-H3 hierarchical structure
- ✅ Keyword density optimization
- ✅ Image alt tags with keywords

### Technical SEO
- ✅ JSON-LD schema markup (3 types)
- ✅ Breadcrumb navigation (visible + schema)
- ✅ Canonical URLs
- ✅ Mobile-responsive structure
- ✅ Fast-loading minimal CSS

### Internal Linking
- ✅ Hub & Spoke architecture
- ✅ 2+ hub links (English pillar + language hub)
- ✅ 3+ cluster links (specific camera reviews)
- ✅ 2+ regional links (city guides)
- ✅ Keyword-rich anchor text

### EEAT Signals
- ✅ Author box with credentials
- ✅ Testing methodology section
- ✅ Local testing locations
- ✅ Honest pros/cons
- ✅ Last updated date

---

## 🛠️ Troubleshooting

### Issue: YAML parsing error
**Solution**: Ensure proper indentation in `global_seo_crew.yaml`. Use spaces, not tabs.

### Issue: JSON schema validation fails
**Solution**: Check that meta titles are < 60 chars and descriptions are 150-160 chars.

### Issue: Missing language data
**Solution**: Verify all 4 localization dictionaries in `global_seo_pipeline.py` include the target language.

### Issue: Directory creation fails
**Solution**: Ensure write permissions in `/workspace/` directory.

---

## 📝 Next Steps

### Phase 1: Generate HTML Content
Use the intermediate JSON data to generate full HTML pages:

```bash
# Example prompt for Qwen Coder
"Read workspace/es-ES/guias/seo-data-es-ES.json and generate 
a complete HTML pillar page following the PT-BR template structure 
from pt-br/novas-cameras-2026.html"
```

### Phase 2: Deploy to GitHub Pages
```bash
# Copy generated files to main site structure
cp -r workspace/*/guias/*.html /workspace/es-ES/guias/
cp -r workspace/*/guias/*.html /workspace/it-IT/guias/
# ... repeat for all languages

# Commit and push
git add .
git commit -m "Add 11 localized pillar pages for new cameras 2026"
git push origin main
```

### Phase 3: Monitor Performance
- Track rankings for primary keywords in each market
- Monitor organic traffic from each country
- A/B test meta descriptions for CTR optimization
- Update prices and availability quarterly

---

## 📞 Support

For issues or questions:
1. Check `pipeline-summary.json` for execution errors
2. Validate JSON outputs against `output_schema.json`
3. Review agent configurations in `global_seo_crew.yaml`
4. Inspect Python logs in console output

---

## 📄 License

This pipeline is part of the VideoCameraHoliday project. All rights reserved.

**Generated**: September 2026  
**Version**: 1.0.0  
**Author**: Dawid Millennium
