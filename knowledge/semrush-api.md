# SEMRush API Documentation

> Reference documentation for SEMRush API integration.
> Source: https://developer.semrush.com/api/
> Last updated: 2025-12-30

## Overview

SEMRush provides API access to SEO and competitive intelligence data across three main categories:

| Category | Description | Version |
|----------|-------------|---------|
| **Analytics API** | SEO/PPC competitive intelligence, keywords, domains | v3 |
| **Trends API** | Website traffic and market intelligence | v3/v4 |
| **Projects API** | Rank tracking and site audits | v3/v4 |

### Data Coverage

- 27+ billion keywords indexed
- 808 million domains analyzed
- 43 trillion backlinks tracked
- 142 geographic databases
- Historical data since 2012 (US database)

---

## Authentication

### API Key

- **Method**: Query parameter authentication
- **Parameter**: `key`
- **Location**: Account > Subscription info > API units
- **Security**: Never expose publicly - compromised keys risk account access

### Example Request

```
https://api.semrush.com/?type=domain_organic&key=YOUR_API_KEY&domain=example.com&database=us
```

---

## Base URLs

| API | Base URL |
|-----|----------|
| Analytics (Domain/Keyword) | `https://api.semrush.com/` |
| Backlinks | `https://api.semrush.com/analytics/v1/` |

---

## Response Format

- **Format**: CSV (all Analytics API v3 endpoints)
- **Columns**: Customizable via `export_columns` parameter
- **Max Filters**: 25 per request

---

## Rate Limits & Error Codes

### Rate Limit Errors

| Code | Description |
|------|-------------|
| 429 | Too Many Requests - reduce request rate |
| 131 | Request limit for specific report reached |
| 132 | API unit balance exhausted |
| 134 | Total API request limit reached |

### Common Error Codes

| Code | Description |
|------|-------------|
| 40-46 | Missing mandatory parameters |
| 50 | No data found |
| 110-136 | Authentication, access, subscription issues |
| 402 | Invalid API key |
| 605-613 | Parameter validation errors |

---

## API Units (Costs)

Requests consume API units based on report type and results returned:

| Report Type | Cost per Line |
|-------------|---------------|
| Domain Organic Keywords | 10 units |
| Keyword Overview | 10 units |
| Organic Results | 10 units |
| Broad Match Keywords | 20 units |
| Paid Search Keywords | 20 units |
| Domain PLA Keywords | 30 units |
| Related Keywords | 40 units |
| Backlinks (most endpoints) | 40 units |
| Competitors Reports | 40 units |
| Keyword Difficulty | 50 units |
| PLA Copies | 60 units |
| Ads History | 100 units |
| Authority Score Profile | 100 units |

---

## Common Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | string | **Required.** API key |
| `type` | string | **Required.** Report type |
| `domain` | string | Target domain (for domain reports) |
| `phrase` | string | Target keyword (for keyword reports) |
| `database` | string | Regional database code (e.g., `us`, `uk`, `de`) |
| `export_columns` | string | Comma-separated column codes |
| `display_limit` | integer | Max results (varies by endpoint) |
| `display_offset` | integer | Pagination offset |
| `display_sort` | string | Sort column and direction |
| `display_filter` | string | URL-encoded filter expression |
| `display_date` | string | Historical date (format: `YYYYMM15`) |
| `export_escape` | integer | Wrap columns in quotes (1 = yes) |
| `export_decode` | integer | URL decode output (0 or 1) |

---

## Domain Reports

### Domain Organic Search Keywords

Get organic keywords a domain ranks for.

```
GET https://api.semrush.com/
  ?type=domain_organic
  &key=API_KEY
  &domain=example.com
  &database=us
```

**Parameters:**
- `display_limit`: Max 4,000,000
- `display_date`: Format `YYYYMM15` or `YYYYMMDD`
- `display_positions`: `new`, `lost`, `rise`, `fall`

**Response Columns:**
| Code | Description |
|------|-------------|
| Ph | Keyword |
| Po | Position |
| Pp | Previous Position |
| Pd | Position Difference |
| Nq | Search Volume |
| Cp | CPC |
| Ur | URL |
| Tr | Traffic (%) |
| Tc | Traffic Cost (%) |
| Co | Competition |
| Nr | Number of Results |
| Td | Trends |
| Kd | Keyword Difficulty |

### Domain Paid Search Keywords

```
GET https://api.semrush.com/
  ?type=domain_adwords
  &key=API_KEY
  &domain=example.com
  &database=us
```

**Cost:** 20 units/line

### Organic Competitors

```
GET https://api.semrush.com/
  ?type=domain_organic_organic
  &key=API_KEY
  &domain=example.com
  &database=us
```

**Response Columns:**
| Code | Description |
|------|-------------|
| Dn | Domain |
| Cr | Competitor Relevance |
| Np | Common Keywords |
| Or | Organic Keywords |
| Ot | Organic Traffic |
| Oc | Organic Cost |

### Domain vs. Domain Comparison

```
GET https://api.semrush.com/
  ?type=domain_domains
  &key=API_KEY
  &domains=*|or|domain1.com|*|or|domain2.com
  &database=us
```

**Cost:** 80 units/line

**Domain Operators:**
- `*|or|` - Include domain
- `+|or|` - All keywords from domain
- `-|or|` - Exclude domain

### Domain Organic Pages

```
GET https://api.semrush.com/
  ?type=domain_organic_unique
  &key=API_KEY
  &domain=example.com
  &database=us
```

**Response Columns:** Ur (URL), Pc (Keywords), Tg (Traffic), Tr (Traffic %)

---

## Keyword Reports

### Keyword Overview (All Databases)

```
GET https://api.semrush.com/
  ?type=phrase_all
  &key=API_KEY
  &phrase=seo
```

**Cost:** 10 units/line

**Response Columns:**
| Code | Description |
|------|-------------|
| Dt | Date |
| Db | Database |
| Ph | Keyword |
| Nq | Search Volume |
| Cp | CPC |
| Co | Competition |
| Nr | Number of Results |
| In | Intent |
| Kd | Keyword Difficulty |

### Keyword Overview (Single Database)

```
GET https://api.semrush.com/
  ?type=phrase_this
  &key=API_KEY
  &phrase=seo
  &database=us
```

### Batch Keyword Overview

Query up to 100 keywords at once (semicolon-separated):

```
GET https://api.semrush.com/
  ?type=phrase_these
  &key=API_KEY
  &phrase=keyword1;keyword2;keyword3
  &database=us
```

### Keyword Organic Results

```
GET https://api.semrush.com/
  ?type=phrase_organic
  &key=API_KEY
  &phrase=seo
  &database=us
```

**Parameters:**
- `display_limit`: Max 100,000
- `positions_type`: `organic` or `all`

### Related Keywords

```
GET https://api.semrush.com/
  ?type=phrase_related
  &key=API_KEY
  &phrase=seo
  &database=us
```

**Cost:** 40 units/line

### Keyword Questions

Returns question-format keywords:

```
GET https://api.semrush.com/
  ?type=phrase_questions
  &key=API_KEY
  &phrase=seo
  &database=us
```

**Cost:** 40 units/line

### Keyword Difficulty

Query 1-100 keywords (semicolon-separated):

```
GET https://api.semrush.com/
  ?type=phrase_kdi
  &key=API_KEY
  &phrase=keyword1;keyword2
  &database=us
```

**Cost:** 50 units/line

---

## Backlinks API

**Base URL:** `https://api.semrush.com/analytics/v1/`

### Target Types

| Value | Description |
|-------|-------------|
| `root_domain` | Entire domain (example.com) |
| `domain` | Specific subdomain (www.example.com) |
| `url` | Specific page URL |

### Backlinks Overview

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks_overview
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
```

**Cost:** 40 units/request

**Response Columns:**
| Code | Description |
|------|-------------|
| ascore | Authority Score |
| total | Total Backlinks |
| domains_num | Referring Domains |
| urls_num | Referring URLs |
| ips_num | Referring IPs |
| follows_num | Follow Links |
| nofollows_num | Nofollow Links |
| sponsored_num | Sponsored Links |
| ugc_num | UGC Links |
| texts_num | Text Links |
| images_num | Image Links |

### Backlinks List

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
  &display_limit=100
```

**Cost:** 40 units/line
**Max Limit:** 1,000,000 (default: 10,000)

**Filter Options:** `type`, `zone`, `ip`, `refdomain`, `anchor`, `newlink`, `lostlink`

**Response Columns:**
| Code | Description |
|------|-------------|
| page_ascore | Page Authority Score |
| source_url | Linking Page URL |
| target_url | Target URL |
| anchor | Anchor Text |
| first_seen | First Seen Date |
| last_seen | Last Seen Date |
| nofollow | Nofollow Flag |

### Referring Domains

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks_refdomains
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
```

**Response Columns:** domain_ascore, domain, backlinks_num, first_seen, last_seen, country

### Anchors

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks_anchors
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
```

**Response Columns:** anchor, domains_num, backlinks_num, first_seen, last_seen

### Backlink Competitors

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks_competitors
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
```

**Response Columns:** score, neighbour, similarity, common_refdomains, domains_num, backlinks_num

### Authority Score Profile

Distribution of referring domains by Authority Score:

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks_ascore_profile
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
```

**Cost:** 100 units/request

### Historical Backlinks

```
GET https://api.semrush.com/analytics/v1/
  ?type=backlinks_historical
  &key=API_KEY
  &target=example.com
  &target_type=root_domain
```

**Note:** Only works with `root_domain` target type.

**Response Columns:** date (Unix timestamp), backlinks_num, domains_num, score

---

## Regional Databases

| Code | Region |
|------|--------|
| us | United States |
| uk | United Kingdom |
| ca | Canada |
| au | Australia |
| de | Germany |
| fr | France |
| es | Spain |
| it | Italy |
| br | Brazil |
| jp | Japan |
| in | India |

**Mobile databases:** Prefix with `mobile-` (e.g., `mobile-us`)
**Extended databases:** Suffix with `-ext` (e.g., `us-ext`)

Full list: 142 regional databases available.

---

## SERP Features

SEMRush tracks 43+ SERP feature types:

| Code | Feature |
|------|---------|
| 0 | Featured Snippet |
| 1 | Reviews |
| 2 | Site Links |
| 3 | Image Pack |
| 4 | Video |
| 5 | Local Pack |
| 6 | Knowledge Panel |
| 7 | Top Stories |
| 8 | Twitter/X |
| 9 | People Also Ask |
| 10 | Shopping Results |
| ... | Additional features (see API docs) |

---

## Keyword Intent Types

| Intent | Description |
|--------|-------------|
| Commercial | Researching products/services |
| Informational | Seeking information |
| Navigational | Looking for specific site |
| Transactional | Ready to purchase |

---

## Integration Notes for PBS Wisconsin

### Relevant Use Cases

1. **Keyword Research**: Find high-volume keywords related to PBS content topics
2. **Competitor Analysis**: Analyze what keywords competing media sites rank for
3. **Content Optimization**: Get keyword difficulty and search volume for target phrases
4. **SEO Monitoring**: Track organic position changes over time

### Recommended Endpoints

For editorial SEO optimization:

| Endpoint | Use Case |
|----------|----------|
| `phrase_this` | Get metrics for target keywords |
| `phrase_these` | Batch analyze multiple keywords |
| `phrase_related` | Find related keyword opportunities |
| `phrase_questions` | Find question-based content ideas |
| `phrase_kdi` | Assess keyword difficulty |
| `domain_organic` | Audit current organic performance |

### API Unit Budget Considerations

- Keyword overview: 10 units/keyword
- Related keywords: 40 units/line
- Keyword difficulty: 50 units/keyword

Budget accordingly based on monthly API unit allocation.

---

## References

- [SEMRush API Documentation](https://developer.semrush.com/api/)
- [Analytics API v3](https://developer.semrush.com/api/v3/analytics/)
- [Backlinks API](https://developer.semrush.com/api/v3/analytics/backlinks/)
- [Projects API](https://developer.semrush.com/api/v3/projects/)
