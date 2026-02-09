# Cookie Guardian: Autonomous GitHub Cookie Management System
## Complete Product Specification Document
**Version:** 1.0.0  
**Date:** February 10, 2026  
**Document Type:** PRD + System Prompt + TRD + PTD + FRD (Unified)  
**Classification:** Production-Ready Architecture

---

# EXECUTIVE SUMMARY

## Vision Statement
Cookie Guardian is a fully autonomous, AI-driven system that discovers, monitors, and manages authentication cookies across GitHub repositories with zero human intervention. The system operates as an intelligent agent that makes real-time decisions about cookie extraction, rotation, and injection while maintaining enterprise-grade security and stealth.

## Core Problem
Developers managing multiple repositories requiring cookie-based authentication face:
- Manual cookie extraction and updates (time-consuming)
- Expired cookies breaking CI/CD pipelines
- Security risks from cookie exposure
- IP bans from repeated manual login attempts
- Lack of automated cookie lifecycle management

## Solution Architecture
A GitHub Actions-based autonomous agent that:
1. **Discovers** repositories requiring cookies via intelligent code analysis
2. **Extracts** cookies using stealth browser automation with residential IP routing
3. **Monitors** cookie health and predicts expiry using ML patterns
4. **Injects** cookies as GitHub Secrets via encrypted API calls
5. **Rotates** cookies proactively 24 hours before expiry
6. **Adapts** strategies using GLM-4-Air LLM for decision-making

## Key Metrics
- **Automation Level:** 100% autonomous operation
- **Detection Rate:** <1% bot detection probability
- **Uptime:** 99.5% cookie availability
- **Cost:** ~$0.20/month (GLM-4-Air API only)
- **Response Time:** Cookie rotation within 15 minutes of detection
- **Security:** AES-256 encryption, Libsodium sealed boxes

---

# PART 1: PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1.1 Product Overview

### 1.1.1 Product Description
Cookie Guardian is a serverless, AI-powered automation system deployed on GitHub Actions that autonomously manages authentication cookie lifecycles across unlimited repositories. It operates 24/7 with zero configuration after initial setup.

### 1.1.2 Target Users
- **Primary:** Individual developers with 5+ repositories requiring cookie authentication
- **Secondary:** Small dev teams managing shared repositories
- **Tertiary:** DevOps engineers automating CI/CD pipelines

### 1.1.3 Success Criteria
| Metric | Target | Measurement |
|--------|--------|-------------|
| Cookie uptime | >99% | Availability monitoring |
| Bot detection rate | <1% | Failed login attempts |
| False positive repo detection | <5% | Manual audit sample |
| Time to rotate expired cookie | <30 min | System logs |
| Cost per repository | <$0.01/month | API usage tracking |

## 1.2 Core Features

### Feature 1: Intelligent Repository Discovery
**Description:** Automatically identifies repositories requiring cookies without manual configuration.

**Acceptance Criteria:**
- ✅ Scans all user repositories on first run
- ✅ Monitors for new repositories via webhooks (real-time)
- ✅ Detects cookie requirements in .env.example, config files, README
- ✅ Parses code for cookie authentication patterns
- ✅ Achieves >95% accuracy in cookie requirement detection

**User Story:**
> As a developer, when I create a new repo requiring cookies, the system should automatically detect it within 1 hour and begin monitoring without me configuring anything.

**Technical Requirements:**
- GitHub GraphQL API for efficient repo scanning
- Tree-sitter parser for code analysis
- Regex patterns for 50+ cookie naming conventions
- Webhook handler for `repository.created` events
- SQLite database for repo metadata storage

### Feature 2: Stealth Browser Automation
**Description:** Extracts cookies using undetectable browser automation with anti-fingerprinting.

**Acceptance Criteria:**
- ✅ Passes sannysoft.com bot detection tests
- ✅ Supports 20+ major platforms (GitHub, Google, Facebook, etc.)
- ✅ Routes through Cloudflare WARP for residential IPs
- ✅ Implements 15+ anti-fingerprinting techniques
- ✅ Recovers from 95% of CAPTCHA/rate-limit scenarios

**User Story:**
> As a user, when the system logs in to extract cookies, it should never trigger bot detection or IP bans, even with daily logins.

**Technical Requirements:**
- Playwright with undetected-playwright-python
- Cloudflare WARP CLI integration
- Canvas/WebGL fingerprint randomization
- Human-like typing patterns (0.05-0.3s per char)
- Mouse movement simulation
- Viewport/timezone randomization

### Feature 3: Predictive Cookie Rotation
**Description:** Proactively rotates cookies before expiry using ML-based prediction.

**Acceptance Criteria:**
- ✅ Rotates cookies 24h before known expiry
- ✅ Predicts expiry for cookies without explicit timestamps
- ✅ Validates cookie health every 6 hours
- ✅ Triggers emergency rotation on 3 consecutive validation failures
- ✅ Maintains 99.5% cookie availability SLA

**User Story:**
> As a repo owner, my workflows should never fail due to expired cookies because the system refreshes them automatically before they expire.

**Technical Requirements:**
- Expiry parsing from Set-Cookie headers
- Historical pattern analysis (ML model)
- Periodic validation via test requests
- Platform-specific expiry rules database
- Emergency rotation queue with priority handling

### Feature 4: Secure Secrets Injection
**Description:** Encrypts and injects cookies as GitHub Secrets with granular access control.

**Acceptance Criteria:**
- ✅ Uses Libsodium sealed box encryption
- ✅ Injects secrets with step-level scope
- ✅ Implements key rotation every 90 days
- ✅ Logs all injection operations for audit
- ✅ Supports environment-specific secrets (prod/staging)

**User Story:**
> As a security-conscious developer, cookies should be stored encrypted and only accessible to the specific workflow steps that need them.

**Technical Requirements:**
- GitHub REST API `/repos/{owner}/{repo}/actions/secrets`
- PyNaCl for Libsodium operations
- Public key retrieval and caching
- Secret naming convention: `COOKIE_<DOMAIN>_<TYPE>`
- Audit log in append-only SQLite table

### Feature 5: AI Decision Engine
**Description:** Uses GLM-4-Air LLM to make autonomous decisions during edge cases.

**Acceptance Criteria:**
- ✅ Diagnoses login failures with 90% accuracy
- ✅ Recommends retry strategies with 85% success rate
- ✅ Detects new cookie requirement patterns
- ✅ Responds to decisions within 2 seconds
- ✅ Operates within $0.20/month API budget

**User Story:**
> As a user, when the system encounters unexpected login flows or errors, it should intelligently adapt rather than failing permanently.

**Technical Requirements:**
- GLM-4-Air API integration (OpenAI-compatible)
- Structured JSON output with response_format
- Function calling for tool selection
- Prompt templates for common scenarios
- Fallback to rule-based logic if API unavailable

## 1.3 Non-Functional Requirements

### 1.3.1 Performance
- **Cookie extraction:** <60 seconds per platform
- **Repository scan:** <5 seconds per repo
- **Secret injection:** <2 seconds per secret
- **System response to expiry:** <15 minutes

### 1.3.2 Scalability
- **Repositories:** Support up to 1,000 repos per user
- **Concurrent operations:** 3 parallel browser instances max
- **API rate limits:** Stay within GitHub's 5,000 req/hour
- **Storage:** <100MB for 1,000 monitored repos

### 1.3.3 Security
- **Encryption:** AES-256 for local data, Libsodium for GitHub Secrets
- **Credential storage:** Never in plaintext, encrypted at rest
- **Network security:** WARP tunnel for all browser traffic
- **Audit logging:** Immutable logs for 90 days
- **Secret rotation:** Automatic key rotation every 90 days

### 1.3.4 Reliability
- **Availability:** 99.5% uptime for cookie freshness
- **Error recovery:** Automatic retry with exponential backoff
- **Data persistence:** SQLite with WAL mode for crash safety
- **Monitoring:** Health checks every 6 hours

### 1.3.5 Maintainability
- **Code coverage:** >80% unit test coverage
- **Documentation:** Inline comments, README, API docs
- **Logging:** Structured JSON logs with levels (DEBUG/INFO/ERROR)
- **Dependency management:** Pinned versions, security scanning

## 1.4 Out of Scope (v1.0)

- ❌ Multi-user organization support (single user only)
- ❌ GUI dashboard (CLI/logs only)
- ❌ Custom platform plugins (20 pre-built only)
- ❌ Two-factor authentication bypass (requires user intervention)
- ❌ Mobile app cookies (desktop web only)
- ❌ Cookie sharing between users (security risk)

## 1.5 Release Roadmap

### Phase 1: MVP (Weeks 1-2)
- Basic repo scanning
- Single platform (GitHub.com)
- Manual trigger via workflow_dispatch
- Simple cookie extraction
- GitHub Secrets injection

### Phase 2: Automation (Weeks 3-4)
- Cloudflare WARP integration
- Stealth browser automation
- Scheduled runs (every 6 hours)
- Expiry prediction v1

### Phase 3: Intelligence (Weeks 5-6)
- GLM-4-Air integration
- Multi-platform support (20 platforms)
- Advanced anti-fingerprinting
- ML-based expiry prediction

### Phase 4: Production (Week 7)
- Error recovery and retry logic
- Comprehensive logging
- Security hardening
- Documentation and examples

---

# PART 2: SYSTEM PROMPT (For GLM-4-Air LLM)

```
# SYSTEM IDENTITY
You are the Cookie Guardian Decision Engine, an expert AI assistant specialized in web automation, browser fingerprinting, and authentication systems. Your role is to make autonomous decisions for a cookie management system that operates GitHub Actions workflows.

# PRIMARY OBJECTIVES
1. Diagnose browser automation failures and recommend solutions
2. Detect cookie authentication requirements in code repositories
3. Predict cookie expiry times from limited information
4. Recommend platform-specific login strategies
5. Adapt to anti-bot countermeasures in real-time

# CORE COMPETENCIES
- Web scraping and browser automation (Playwright, Selenium)
- Authentication mechanisms (OAuth, session cookies, JWT)
- Anti-bot detection techniques (fingerprinting, behavioral analysis)
- GitHub Actions CI/CD workflows
- Python programming and debugging

# DECISION-MAKING FRAMEWORK

## When Analyzing Repository Code
INPUT: Repository metadata (name, README, .env.example, source code snippets)
OUTPUT: JSON with this exact structure:
{
  "requires_cookies": true/false,
  "confidence": 0-100,
  "cookie_domains": ["example.com"],
  "cookie_names": ["session_id", "auth_token"],
  "reasoning": "brief explanation",
  "monitoring_priority": "high/medium/low",
  "platform": "github/google/facebook/custom"
}

RULES:
- confidence >80 = automatically monitor
- confidence 50-80 = flag for manual review
- confidence <50 = ignore
- Detect patterns: Cookie.get(), document.cookie, setCookie(), env vars like SESSION_COOKIE

## When Diagnosing Login Failures
INPUT: Error logs, screenshot (base64), platform name, attempt count
OUTPUT: JSON with this exact structure:
{
  "issue_type": "captcha/rate_limit/credentials/network/2fa_required/unknown",
  "recommended_action": "retry/wait/rotate_ip/change_strategy/manual_intervention",
  "wait_time_seconds": 0-3600,
  "strategy_changes": ["use_different_user_agent", "enable_headful_mode"],
  "confidence": 0-100,
  "reasoning": "brief explanation"
}

RULES:
- Always recommend retry for transient network errors
- For rate_limit: wait_time = attempt_count^2 * 60 (exponential backoff)
- For captcha: recommend IP rotation + headful mode
- For 2fa_required: flag for manual_intervention
- Never recommend more than 3 retries for same issue

## When Predicting Cookie Expiry
INPUT: Cookie data (domain, name, value, set_date, max_age, expires header, historical data)
OUTPUT: JSON with this exact structure:
{
  "expires_at": "ISO8601 timestamp or null",
  "confidence": 0-100,
  "should_rotate_in_hours": 24,
  "reasoning": "brief explanation",
  "expiry_source": "explicit_header/max_age/platform_default/ml_prediction"
}

RULES:
- If Expires header present: use it (confidence=100)
- If Max-Age present: calculate from set_date (confidence=95)
- If neither: use platform defaults (GitHub=90 days, Google=30 days)
- Default to 24h rotation for unknown platforms (confidence=50)
- Recommend earlier rotation for high-value cookies

## When Recommending Login Strategy
INPUT: Platform name, previous failure count, available credentials, proxy status
OUTPUT: JSON with this exact structure:
{
  "approach": "headless/headful/api_direct/manual_required",
  "proxy_required": true/false,
  "delays": {"min_seconds": 2, "max_seconds": 5},
  "anti_fingerprint_level": "basic/advanced/maximum",
  "custom_steps": ["step1", "step2"],
  "estimated_success_rate": 0-100
}

RULES:
- Start with headless + basic anti-fingerprint
- Escalate to headful + advanced if 2+ failures
- Require proxy if 3+ failures from same IP
- Flag manual_required for 2FA or complex flows
- Prefer platform-specific APIs when available

# RESPONSE CONSTRAINTS
- ALWAYS output valid JSON (use response_format: json_object)
- Keep reasoning under 100 words
- Provide actionable recommendations only
- Use ISO8601 for all timestamps
- Confidence scores must be realistic (avoid 100 unless certain)

# ERROR HANDLING
- If input is ambiguous, ask for clarification in reasoning field
- If confident answer impossible, set confidence <30 and explain why
- Never hallucinate data (e.g., don't invent cookie expiry times)
- When uncertain, default to conservative safe values

# ANTI-PATTERNS TO AVOID
- ❌ Don't recommend brute-force approaches
- ❌ Don't suggest illegal bypasses (e.g., bypassing 2FA)
- ❌ Don't make assumptions about user intent
- ❌ Don't provide recommendations that violate platform ToS
- ❌ Don't recommend storing credentials in plaintext

# OPTIMIZATION DIRECTIVES
- Prioritize speed: Respond in <2 seconds
- Minimize token usage: Be concise but complete
- Prefer structured output over prose
- Use tool calling when multiple operations needed

# EXAMPLES

GOOD Response (Repo Analysis):
{
  "requires_cookies": true,
  "confidence": 92,
  "cookie_domains": ["api.github.com"],
  "cookie_names": ["user_session"],
  "reasoning": "Found cookie auth in GitHub API calls, .env.example has GITHUB_SESSION var",
  "monitoring_priority": "high",
  "platform": "github"
}

BAD Response (Too Verbose):
"Based on my extensive analysis of the repository structure, I have determined with high confidence that this project requires authentication cookies for the GitHub platform. The evidence includes several factors..."

GOOD Response (Login Failure):
{
  "issue_type": "rate_limit",
  "recommended_action": "wait",
  "wait_time_seconds": 900,
  "strategy_changes": ["rotate_ip_via_warp"],
  "confidence": 85,
  "reasoning": "HTTP 429 response, retry-after header indicates 15min cooldown"
}

You are optimized for speed, accuracy, and actionable insights. Always balance automation with safety.
```

---

# PART 3: TECHNICAL REQUIREMENTS DOCUMENT (TRD)

## 3.1 System Architecture

### 3.1.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions Runner                    │
│                    (ubuntu-latest, 2 CPUs)                   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│  Discovery   │  │  Browser Auto    │  │   AI Brain   │
│   Module     │  │  + WARP Proxy    │  │  (GLM-4-Air) │
└──────────────┘  └──────────────────┘  └──────────────┘
        ↓                   ↓                   ↓
┌─────────────────────────────────────────────────────────────┐
│              GitHub API (Secrets + GraphQL)                  │
└─────────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│            Persistent Storage (GitHub Repo Files)            │
│         cookies.db.enc | audit.log | state.json             │
└─────────────────────────────────────────────────────────────┘
```

### 3.1.2 Component Specifications

#### Component 1: Discovery Module
**Purpose:** Identify repositories requiring cookie authentication

**Tech Stack:**
- Language: Python 3.11+
- Libraries: PyGithub, tree-sitter, gitpython
- Storage: SQLite3 with FTS5 extension

**Inputs:**
- GitHub personal access token (PAT)
- User's repository list (via GraphQL)
- Webhook payloads (new repos)

**Outputs:**
- List of repos requiring monitoring (JSON)
- Cookie metadata (domain, platform, priority)
- Confidence scores per repo

**Performance:**
- Scan rate: 200 repos/minute
- Memory: <100MB
- Storage: ~1KB per repo

**Code Structure:**
```python
class RepoDiscovery:
    def scan_all_repos(self) -> List[RepoMetadata]
    def analyze_repo(self, repo: Repository) -> CookieRequirement
    def detect_cookie_patterns(self, files: List[str]) -> List[Pattern]
    def parse_env_example(self, content: str) -> List[EnvVar]
    def get_confidence_score(self, signals: List[Signal]) -> float
```

#### Component 2: Browser Automation Engine
**Purpose:** Extract cookies via stealth browsing

**Tech Stack:**
- Browser: Playwright (Chromium)
- Stealth: undetected-playwright-python
- Proxy: Cloudflare WARP CLI
- Anti-fingerprint: Custom scripts

**Inputs:**
- Platform URL (e.g., github.com/login)
- User credentials (encrypted)
- Proxy configuration

**Outputs:**
- Cookie jar (JSON)
- Session metadata
- Screenshot on failure (base64)

**Performance:**
- Login time: 30-90 seconds
- Concurrent sessions: 3 max
- Memory: 400MB per browser

**Anti-Detection Techniques:**
```python
STEALTH_CONFIG = {
    # Browser flags
    "args": [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ],
    
    # Fingerprint randomization
    "user_agent": random.choice(UA_POOL),
    "viewport": random.choice(VIEWPORT_POOL),
    "timezone": random.choice(TIMEZONE_POOL),
    "locale": "en-US",
    
    # Behavioral simulation
    "typing_delay_ms": (50, 300),
    "mouse_movement": True,
    "random_pauses": True,
    
    # WebGL/Canvas spoofing
    "canvas_noise": True,
    "webgl_vendor": "Intel Inc.",
    "webgl_renderer": "Intel Iris OpenGL Engine",
}
```

#### Component 3: WARP Integration Layer
**Purpose:** Route browser traffic through Cloudflare WARP

**Tech Stack:**
- CLI: warp-cli (Cloudflare official)
- Language: Python subprocess
- Protocol: WireGuard (default)

**Installation:**
```bash
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | \
  sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
  
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] \
  https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/cloudflare-client.list

sudo apt update && sudo apt install cloudflare-warp -y
```

**Python Interface:**
```python
class WARPManager:
    def connect(self) -> bool:
        """Connect to WARP, retry 3x on failure"""
        
    def disconnect(self) -> bool:
        """Graceful disconnect"""
        
    def rotate_ip(self) -> str:
        """Disconnect → reconnect for new IP"""
        
    def verify_active(self) -> bool:
        """Check warp=on in cloudflare.com/cdn-cgi/trace"""
        
    def get_current_ip(self) -> str:
        """Query ipify.org for public IP"""
```

**IP Rotation Logic:**
```python
def smart_rotate_ip(context: BrowserContext) -> str:
    """Rotate IP when needed"""
    # Triggers:
    # - Before each login attempt
    # - After 3 failed attempts
    # - Every 2 hours (preventive)
    
    old_ip = warp.get_current_ip()
    warp.disconnect()
    time.sleep(random.uniform(5, 10))  # Mimic human
    warp.connect()
    new_ip = warp.get_current_ip()
    
    if old_ip == new_ip:
        # Retry once if IP didn't change
        warp.rotate_ip()
    
    return new_ip
```

#### Component 4: GLM-4-Air Decision Engine
**Purpose:** Make autonomous decisions during edge cases

**API Specification:**
```python
# Official GLM-4-Air API (OpenAI-compatible)
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
MODEL = "glm-4-air"

# Pricing (as of Feb 2026)
INPUT_COST = 0.20 / 1_000_000  # tokens
OUTPUT_COST = 1.10 / 1_000_000  # tokens
```

**Request Format:**
```json
{
  "model": "glm-4-air",
  "messages": [
    {
      "role": "system",
      "content": "<system_prompt from Part 2>"
    },
    {
      "role": "user",
      "content": "Analyze this repo for cookie requirements: {...}"
    }
  ],
  "temperature": 0.1,
  "response_format": {
    "type": "json_object"
  }
}
```

**Response Handling:**
```python
async def get_llm_decision(prompt: str, task: str) -> dict:
    """Call GLM-4-Air with structured output"""
    
    response = await client.chat.completions.create(
        model="glm-4-air",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  # Low for consistency
        response_format={"type": "json_object"}
    )
    
    # Parse JSON response
    decision = json.loads(response.choices[0].message.content)
    
    # Validate structure
    if task == "repo_analysis":
        assert "requires_cookies" in decision
        assert "confidence" in decision
    
    return decision
```

**Token Budget Management:**
```python
# Average token usage per decision
DECISION_COSTS = {
    "repo_analysis": 500,      # Input + output tokens
    "login_failure": 800,       # Includes screenshot
    "expiry_prediction": 300,
    "strategy_recommendation": 400,
}

# Monthly budget: $0.20
# Allows ~150,000 tokens/month
# = ~300 decisions/month
# = ~10 decisions/day
```

#### Component 5: Secrets Management
**Purpose:** Securely inject cookies into GitHub Secrets

**GitHub API Endpoint:**
```
PUT /repos/{owner}/{repo}/actions/secrets/{secret_name}
```

**Encryption Process:**
```python
import base64
from nacl import encoding, public

def encrypt_secret(secret_value: str, public_key: str) -> str:
    """Encrypt using Libsodium sealed box"""
    
    # Get repo's public key
    public_key = public.PublicKey(
        public_key.encode("utf-8"), 
        encoding.Base64Encoder()
    )
    
    # Create sealed box
    sealed_box = public.SealedBox(public_key)
    
    # Encrypt
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    
    # Base64 encode
    return base64.b64encode(encrypted).decode("utf-8")
```

**Secret Naming Convention:**
```
COOKIE_{DOMAIN}_{TYPE}
Example: COOKIE_GITHUB_COM_SESSION
         COOKIE_GOOGLE_COM_AUTH
         
Additional metadata secrets:
COOKIE_GITHUB_COM_EXTRACTED_AT  # ISO8601 timestamp
COOKIE_GITHUB_COM_EXPIRES_AT    # ISO8601 timestamp
```

**Injection Code:**
```python
async def inject_cookie_secret(
    repo_full_name: str,
    domain: str,
    cookie_data: dict
) -> bool:
    """Inject cookie as GitHub Secret"""
    
    # Get repo public key
    key_response = await github_api.get(
        f"/repos/{repo_full_name}/actions/secrets/public-key"
    )
    
    public_key = key_response["key"]
    key_id = key_response["key_id"]
    
    # Encrypt cookie
    encrypted = encrypt_secret(
        json.dumps(cookie_data),
        public_key
    )
    
    # Inject secret
    secret_name = f"COOKIE_{domain.replace('.', '_').upper()}_SESSION"
    
    await github_api.put(
        f"/repos/{repo_full_name}/actions/secrets/{secret_name}",
        json={
            "encrypted_value": encrypted,
            "key_id": key_id
        }
    )
    
    return True
```

## 3.2 Data Models

### 3.2.1 Database Schema (SQLite)

```sql
-- Monitored Repositories
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    full_name TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,  -- 'github', 'google', etc.
    cookie_domains TEXT NOT NULL,  -- JSON array
    priority TEXT NOT NULL,  -- 'high', 'medium', 'low'
    confidence INTEGER NOT NULL,  -- 0-100
    last_scanned_at TEXT NOT NULL,  -- ISO8601
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Cookie Inventory
CREATE TABLE cookies (
    id INTEGER PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    domain TEXT NOT NULL,
    name TEXT NOT NULL,
    value_encrypted TEXT NOT NULL,  -- AES-256 encrypted
    expires_at TEXT,  -- ISO8601, nullable
    extracted_at TEXT NOT NULL,
    last_validated_at TEXT NOT NULL,
    rotation_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);

-- Audit Log
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'extract', 'inject', 'rotate', 'validate'
    repo_id INTEGER,
    cookie_id INTEGER,
    status TEXT NOT NULL,  -- 'success', 'failure'
    details TEXT,  -- JSON
    FOREIGN KEY (repo_id) REFERENCES repositories(id),
    FOREIGN KEY (cookie_id) REFERENCES cookies(id)
);

-- System State
CREATE TABLE state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes
CREATE INDEX idx_repos_platform ON repositories(platform);
CREATE INDEX idx_cookies_expires ON cookies(expires_at);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
```

### 3.2.2 Configuration Files

**config.yaml:**
```yaml
# Platform-specific configurations
platforms:
  github:
    login_url: "https://github.com/login"
    cookie_names: ["user_session", "_gh_sess"]
    expiry_default_days: 90
    
  google:
    login_url: "https://accounts.google.com"
    cookie_names: ["SID", "HSID", "SSID"]
    expiry_default_days: 30

# Anti-fingerprinting pools
fingerprints:
  user_agents:
    - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
  
  viewports:
    - {width: 1920, height: 1080}
    - {width: 1366, height: 768}
  
  timezones:
    - "America/New_York"
    - "America/Los_Angeles"

# Rate limiting
rate_limits:
  github_api: 5000  # requests/hour
  login_attempts_per_domain: 3
  cooldown_minutes: 60
```

## 3.3 API Integrations

### 3.3.1 GitHub GraphQL API
**Purpose:** Efficient repository listing and metadata retrieval

**Query:**
```graphql
query GetUserRepos($cursor: String) {
  viewer {
    repositories(first: 100, after: $cursor) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        name
        nameWithOwner
        updatedAt
        defaultBranchRef {
          target {
            ... on Commit {
              tree {
                entries {
                  name
                  type
                  object {
                    ... on Blob {
                      text
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 3.3.2 GitHub REST API
**Purpose:** Secrets management and webhook handling

**Endpoints Used:**
```
GET    /repos/{owner}/{repo}/actions/secrets/public-key
PUT    /repos/{owner}/{repo}/actions/secrets/{secret_name}
DELETE /repos/{owner}/{repo}/actions/secrets/{secret_name}
POST   /repos/{owner}/{repo}/hooks
```

### 3.3.3 GLM-4-Air API
**Purpose:** AI-powered decision making

**Endpoint:**
```
POST https://open.bigmodel.cn/api/paas/v4/chat/completions
```

**Rate Limits:**
- 60 requests/minute
- 1000 requests/day (free tier)

## 3.4 Security Architecture

### 3.4.1 Encryption Layers

**Layer 1: Transport (TLS)**
- All API calls over HTTPS
- WARP tunnel uses WireGuard encryption

**Layer 2: Application (AES-256)**
```python
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_cookie(self, cookie: dict) -> str:
        """Encrypt cookie data"""
        plaintext = json.dumps(cookie).encode()
        return self.cipher.encrypt(plaintext).decode()
    
    def decrypt_cookie(self, encrypted: str) -> dict:
        """Decrypt cookie data"""
        plaintext = self.cipher.decrypt(encrypted.encode())
        return json.loads(plaintext)
```

**Layer 3: GitHub Secrets (Libsodium)**
- Used by GitHub Actions natively
- Sealed box encryption before storage

### 3.4.2 Credential Management

**Storage:**
```
GitHub Actions Secrets:
  - GITHUB_TOKEN (auto-generated)
  - GLM_API_KEY (user-provided)
  - ENCRYPTION_KEY (user-provided, AES-256)
  - USER_CREDENTIALS_<PLATFORM> (encrypted JSON)
```

**Access Control:**
```yaml
# .github/workflows/cookie-guardian.yml
env:
  GLM_API_KEY: ${{ secrets.GLM_API_KEY }}
  # Only accessible at workflow level

jobs:
  rotate-cookies:
    steps:
      - name: Extract cookies
        env:
          USER_CREDS: ${{ secrets.USER_CREDENTIALS_GITHUB }}
          # Only accessible in this step
```

### 3.4.3 Audit Trail

**Logged Events:**
- Every cookie extraction (timestamp, domain, success/fail)
- Every secret injection (repo, secret name, timestamp)
- Every IP rotation (old IP, new IP, reason)
- Every LLM decision (prompt hash, decision, confidence)

**Log Format:**
```json
{
  "timestamp": "2026-02-10T15:30:00Z",
  "event": "cookie_extracted",
  "repo": "user/repo-name",
  "platform": "github",
  "ip": "104.28.x.x",
  "success": true,
  "duration_ms": 45234,
  "metadata": {
    "cookies_extracted": 2,
    "warp_enabled": true
  }
}
```

## 3.5 Error Handling

### 3.5.1 Retry Strategy
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type((NetworkError, TimeoutError))
)
async def extract_cookies(platform: str, credentials: dict):
    """Extract cookies with automatic retry"""
    pass
```

### 3.5.2 Failure Modes

| Failure Type | Detection | Recovery |
|-------------|-----------|----------|
| Bot detected | HTTP 403, CAPTCHA page | Rotate IP + headful mode |
| Rate limited | HTTP 429, retry-after header | Wait + exponential backoff |
| Invalid creds | Login failed message | Alert user (email) |
| Network error | Connection timeout | Retry 3x, skip if persistent |
| API quota | GitHub 403 rate limit | Wait until reset time |
| WARP failed | Connection refused | Fallback to direct (flagged) |

### 3.5.3 Circuit Breaker
```python
class CircuitBreaker:
    """Prevent cascading failures"""
    
    def __init__(self, threshold: int = 5, timeout: int = 300):
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout  # seconds
        self.last_failure = None
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args):
        if self.state == "open":
            if time.time() - self.last_failure > self.timeout:
                self.state = "half-open"
            else:
                raise CircuitOpenError()
        
        try:
            result = func(*args)
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure = time.time()
            
            if self.failure_count >= self.threshold:
                self.state = "open"
            
            raise e
```

## 3.6 Performance Optimization

### 3.6.1 Caching Strategy
```python
# Cache GitHub API responses
@lru_cache(maxsize=1000)
def get_repo_metadata(repo_name: str) -> dict:
    """Cache repo metadata for 1 hour"""
    pass

# Cache LLM decisions for identical inputs
@cached(cache=TTLCache(maxsize=100, ttl=3600))
def get_llm_decision(prompt_hash: str) -> dict:
    """Cache LLM responses for 1 hour"""
    pass
```

### 3.6.2 Parallelization
```python
import asyncio

async def process_repos_parallel(repos: List[str]):
    """Process up to 3 repos concurrently"""
    semaphore = asyncio.Semaphore(3)
    
    async def process_with_limit(repo):
        async with semaphore:
            return await process_repo(repo)
    
    tasks = [process_with_limit(r) for r in repos]
    return await asyncio.gather(*tasks)
```

### 3.6.3 Database Optimization
```sql
-- WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Optimize query performance
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=MEMORY;
PRAGMA cache_size=-64000;  -- 64MB cache
```

---

# PART 4: PLATFORM INTEGRATION DOCUMENT (PTD)

## 4.1 GitHub Actions Integration

### 4.1.1 Workflow Configuration

**File:** `.github/workflows/cookie-guardian.yml`

```yaml
name: Cookie Guardian - Autonomous Cookie Management

on:
  schedule:
    # Run every 6 hours
    - cron: '0 */6 * * *'
  
  # Manual trigger for testing
  workflow_dispatch:
    inputs:
      force_rotation:
        description: 'Force cookie rotation for all repos'
        required: false
        default: 'false'

# Security: Read-only by default
permissions:
  contents: read
  actions: write  # For secrets management

jobs:
  cookie-guardian:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    strategy:
      matrix:
        # Shard workload across 3 parallel jobs
        shard: [1, 2, 3]
      fail-fast: false
    
    steps:
      # 1. Checkout code
      - name: Checkout repository
        uses: actions/checkout@v4
      
      # 2. Setup Cloudflare WARP
      - name: Install and configure WARP
        run: |
          # Add Cloudflare repo
          curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | \
            sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
          
          echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | \
            sudo tee /etc/apt/sources.list.d/cloudflare-client.list
          
          # Install WARP
          sudo apt-get update
          sudo apt-get install -y cloudflare-warp
          
          # Register and connect
          echo -e "y\n" | warp-cli register
          warp-cli connect
          
          # Wait for connection
          sleep 5
          
          # Verify WARP is active
          curl -s https://www.cloudflare.com/cdn-cgi/trace/ | grep "warp=on"
      
      # 3. Setup Python
      - name: Setup Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      # 4. Install dependencies
      - name: Install Python dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          
          # Install Playwright browsers
          playwright install chromium
          playwright install-deps chromium
      
      # 5. Decrypt database (if exists)
      - name: Setup database
        env:
          ENCRYPTION_KEY: ${{ secrets.ENCRYPTION_KEY }}
        run: |
          if [ -f "cookies.db.enc" ]; then
            python scripts/decrypt_db.py
          else
            python scripts/init_db.py
          fi
      
      # 6. Run Cookie Guardian
      - name: Run Cookie Guardian (Shard ${{ matrix.shard }})
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GLM_API_KEY: ${{ secrets.GLM_API_KEY }}
          ENCRYPTION_KEY: ${{ secrets.ENCRYPTION_KEY }}
          SHARD_ID: ${{ matrix.shard }}
          SHARD_TOTAL: 3
          FORCE_ROTATION: ${{ github.event.inputs.force_rotation }}
        run: |
          python src/orchestrator.py \
            --shard-id $SHARD_ID \
            --shard-total $SHARD_TOTAL \
            --log-level INFO
      
      # 7. Encrypt and commit database
      - name: Save state
        if: always()
        env:
          ENCRYPTION_KEY: ${{ secrets.ENCRYPTION_KEY }}
        run: |
          python scripts/encrypt_db.py
          
          # Commit changes
          git config user.name "Cookie Guardian Bot"
          git config user.email "bot@cookie-guardian.local"
          git add cookies.db.enc audit.log
          git commit -m "chore: update cookie state [shard ${{ matrix.shard }}]" || true
          git push || true
      
      # 8. Cleanup WARP
      - name: Disconnect WARP
        if: always()
        run: |
          warp-cli disconnect || true
      
      # 9. Upload logs as artifacts
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: logs-shard-${{ matrix.shard }}
          path: logs/
          retention-days: 7
```

### 4.1.2 Required Secrets Configuration

**Setup Instructions for Users:**

1. Navigate to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the following secrets:

| Secret Name | Description | How to Generate |
|------------|-------------|-----------------|
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions | Automatic (no action needed) |
| `GLM_API_KEY` | GLM-4-Air API key | Get from https://open.bigmodel.cn |
| `ENCRYPTION_KEY` | AES-256 key for local DB | Run: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `USER_CREDENTIALS_GITHUB` | GitHub login credentials | JSON: `{"email": "...", "password": "..."}` (encrypted) |

**Security Note:** Credentials are only decrypted within the workflow execution context and never logged.

### 4.1.3 Workflow Triggers

**Automatic Triggers:**
```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  
  # Respond to new repos
  repository_dispatch:
    types: [new_repo_detected]
```

**Manual Triggers:**
```bash
# Via GitHub CLI
gh workflow run cookie-guardian.yml \
  -f force_rotation=true

# Via API
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/actions/workflows/cookie-guardian.yml/dispatches \
  -d '{"ref":"main","inputs":{"force_rotation":"true"}}'
```

## 4.2 GLM-4-Air Integration

### 4.2.1 API Client Implementation

```python
from openai import AsyncOpenAI
import json
from typing import Dict, Optional

class GLMDecisionEngine:
    """GLM-4-Air API client for autonomous decisions"""
    
    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4/"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "glm-4-air"
        self.system_prompt = SYSTEM_PROMPT  # From Part 2
    
    async def analyze_repo(self, repo_data: Dict) -> Dict:
        """Determine if repo requires cookie monitoring"""
        
        prompt = f"""
Analyze this GitHub repository for cookie authentication requirements:

Repository: {repo_data['name']}
README (first 500 chars): {repo_data['readme'][:500]}
Environment variables found: {repo_data['env_vars']}
Code patterns detected: {repo_data['patterns']}

Respond with JSON following the repo_analysis schema.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=10.0
        )
        
        decision = json.loads(response.choices[0].message.content)
        
        # Validate schema
        required_fields = ["requires_cookies", "confidence", "cookie_domains"]
        assert all(f in decision for f in required_fields), "Invalid response schema"
        
        return decision
    
    async def diagnose_failure(
        self, 
        error_log: str, 
        platform: str,
        screenshot_b64: Optional[str] = None
    ) -> Dict:
        """Diagnose login failure and recommend action"""
        
        prompt = f"""
Login attempt failed for platform: {platform}

Error log:
{error_log}

{"Screenshot provided in next message" if screenshot_b64 else ""}

Diagnose the issue and provide recovery strategy in JSON.
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Add screenshot if available (GLM-4V supports vision)
        if screenshot_b64:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Screenshot of failure:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
                ]
            })
        
        response = await self.client.chat.completions.create(
            model="glm-4v-plus" if screenshot_b64 else self.model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
```

### 4.2.2 Cost Management

```python
class TokenTracker:
    """Track and limit API token usage"""
    
    def __init__(self, monthly_budget: float = 0.20):
        self.budget = monthly_budget
        self.input_cost_per_token = 0.20 / 1_000_000
        self.output_cost_per_token = 1.10 / 1_000_000
        self.usage = {"input": 0, "output": 0, "cost": 0.0}
    
    def record_usage(self, input_tokens: int, output_tokens: int):
        """Track token usage"""
        self.usage["input"] += input_tokens
        self.usage["output"] += output_tokens
        
        cost = (
            input_tokens * self.input_cost_per_token +
            output_tokens * self.output_cost_per_token
        )
        self.usage["cost"] += cost
    
    def can_make_request(self, estimated_tokens: int = 1000) -> bool:
        """Check if request would exceed budget"""
        estimated_cost = estimated_tokens * self.output_cost_per_token
        return (self.usage["cost"] + estimated_cost) < self.budget
```

## 4.3 Cloudflare WARP Integration

### 4.3.1 Installation Script

```bash
#!/bin/bash
# install_warp.sh

set -e

echo "Installing Cloudflare WARP..."

# Add Cloudflare repository
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | \
  sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/cloudflare-client.list

# Update and install
sudo apt-get update
sudo apt-get install -y cloudflare-warp

# Register
echo -e "y\n" | warp-cli register

# Connect
warp-cli connect

# Wait for connection
sleep 5

# Verify
if curl -s https://www.cloudflare.com/cdn-cgi/trace/ | grep -q "warp=on"; then
    echo "✅ WARP connected successfully"
    warp-cli status
else
    echo "❌ WARP connection failed"
    exit 1
fi
```

### 4.3.2 Python Wrapper

```python
import subprocess
import httpx
import time
from typing import Optional

class WARPManager:
    """Manage Cloudflare WARP connection"""
    
    def __init__(self):
        self.is_connected = False
        self._verify_installation()
    
    def _verify_installation(self):
        """Check if WARP is installed"""
        try:
            subprocess.run(["warp-cli", "--version"], 
                         check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("WARP CLI not installed. Run install_warp.sh first.")
    
    def connect(self, max_retries: int = 3) -> bool:
        """Connect to WARP with retries"""
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    ["warp-cli", "connect"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                time.sleep(5)  # Wait for connection
                
                if self.verify_active():
                    self.is_connected = True
                    print(f"✅ WARP connected (IP: {self.get_current_ip()})")
                    return True
                
                print(f"⚠️  Attempt {attempt + 1} failed, retrying...")
                time.sleep(5)
                
            except subprocess.TimeoutExpired:
                print(f"⚠️  Connection timeout on attempt {attempt + 1}")
        
        return False
    
    def disconnect(self) -> bool:
        """Disconnect from WARP"""
        try:
            subprocess.run(["warp-cli", "disconnect"], 
                         timeout=10, check=True)
            self.is_connected = False
            return True
        except:
            return False
    
    def rotate_ip(self) -> Optional[str]:
        """Force IP rotation"""
        old_ip = self.get_current_ip()
        print(f"🔄 Rotating IP (current: {old_ip})...")
        
        self.disconnect()
        time.sleep(3)
        self.connect()
        
        new_ip = self.get_current_ip()
        
        if old_ip != new_ip:
            print(f"✅ IP rotated: {old_ip} → {new_ip}")
            return new_ip
        else:
            # Retry once
            print("⚠️  IP unchanged, retrying...")
            self.disconnect()
            time.sleep(5)
            self.connect()
            return self.get_current_ip()
    
    def get_current_ip(self) -> Optional[str]:
        """Get current public IP"""
        try:
            response = httpx.get("https://api.ipify.org?format=json", timeout=10)
            return response.json()['ip']
        except:
            return None
    
    def verify_active(self) -> bool:
        """Verify WARP is routing traffic"""
        try:
            response = httpx.get(
                "https://www.cloudflare.com/cdn-cgi/trace/",
                timeout=10
            )
            
            # Check for warp=on or warp=plus
            return "warp=on" in response.text or "warp=plus" in response.text
            
        except:
            return False
    
    def get_status(self) -> dict:
        """Get detailed WARP status"""
        try:
            result = subprocess.run(
                ["warp-cli", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                "connected": "Connected" in result.stdout,
                "output": result.stdout,
                "ip": self.get_current_ip() if self.is_connected else None
            }
        except:
            return {"connected": False, "output": "", "ip": None}
```

---

# PART 5: FUNCTIONAL REQUIREMENTS DOCUMENT (FRD)

## 5.1 User Workflows

### Workflow 1: Initial Setup (First-Time User)

**Actor:** Developer  
**Preconditions:** GitHub account, 1+ repositories  
**Trigger:** User wants to automate cookie management

**Steps:**

1. **Fork/Clone Repository**
   - User forks Cookie Guardian template repo
   - Action: `git clone https://github.com/user/cookie-guardian.git`

2. **Configure Secrets**
   - Navigate to Settings → Secrets and variables → Actions
   - Add required secrets:
     - `GLM_API_KEY`: From https://open.bigmodel.cn (free tier)
     - `ENCRYPTION_KEY`: Generate via `python scripts/generate_key.py`
     - `USER_CREDENTIALS_GITHUB`: JSON with login credentials
   - Estimated time: 5 minutes

3. **Enable Workflow**
   - Go to Actions tab
   - Enable workflows for the repository
   - Manually trigger first run via "Run workflow" button

4. **Verify Setup**
   - Check workflow logs for success
   - Verify cookies.db.enc file committed
   - Confirm cookies injected as secrets in monitored repos

**Postconditions:**
- System operational and monitoring repositories
- First cookie rotation scheduled
- Audit log populated

**Edge Cases:**
- Invalid GLM API key → Error logged, workflow fails with clear message
- Missing credentials → Skip credential-based platforms, notify user
- GitHub API rate limit → Workflow pauses and retries after reset

### Workflow 2: Automatic Cookie Rotation

**Actor:** System (Autonomous)  
**Preconditions:** Repository monitored, cookie expiring in <24h  
**Trigger:** Scheduled workflow run (every 6 hours)

**Steps:**

1. **Health Check**
   - System queries database for cookies expiring soon
   - Logs: "Found 3 cookies expiring in <24h"

2. **IP Rotation**
   - WARP manager rotates IP
   - Logs: "IP rotated: 104.28.1.1 → 104.28.2.2"

3. **Stealth Browser Launch**
   - Playwright starts with anti-fingerprint config
   - Random user agent, viewport, timezone selected
   - Logs: "Browser launched (headless, stealth enabled)"

4. **Login Automation**
   - Navigate to platform login page
   - Simulate human typing (random delays)
   - Submit credentials
   - Logs: "Login successful for github.com"

5. **Cookie Extraction**
   - Parse cookies from browser context
   - Filter relevant cookies (session, auth tokens)
   - Logs: "Extracted 2 cookies: user_session, _gh_sess"

6. **Encryption & Storage**
   - Encrypt cookies using AES-256
   - Update database with new values
   - Logs: "Cookies encrypted and stored"

7. **GitHub Secrets Injection**
   - Retrieve repo's public key
   - Encrypt cookie with Libsodium
   - Inject via GitHub API
   - Logs: "Secret COOKIE_GITHUB_COM_SESSION updated"

8. **Validation**
   - Make test request with new cookie
   - Confirm authentication works
   - Logs: "Cookie validated successfully"

9. **Cleanup**
   - Close browser
   - Disconnect WARP
   - Commit encrypted database
   - Logs: "Rotation complete, next run in 6h"

**Postconditions:**
- Fresh cookies available in GitHub Secrets
- Database updated with new extraction timestamp
- Audit log entry created

**Edge Cases:**
- Login fails → LLM diagnoses, recommends retry with different strategy
- CAPTCHA detected → Switch to headful mode, rotate IP
- Cookie invalid after extraction → Flag for manual review, alert user

### Workflow 3: New Repository Detection

**Actor:** System (Autonomous)  
**Preconditions:** GitHub webhook configured  
**Trigger:** User creates new repository

**Steps:**

1. **Webhook Received**
   - GitHub sends `repository.created` event
   - Payload contains repo metadata
   - Logs: "Webhook: New repo 'user/awesome-project'"

2. **Repository Analysis**
   - Clone repo (shallow, depth=1)
   - Scan for cookie indicators:
     - `.env.example` with COOKIE_ vars
     - `README.md` mentioning authentication
     - Code patterns: `Cookie.get()`, `document.cookie`
   - Logs: "Scanning 45 files..."

3. **LLM Decision**
   - Send metadata to GLM-4-Air
   - Request: "Does this repo require cookies?"
   - Response: `{"requires_cookies": true, "confidence": 87, ...}`
   - Logs: "LLM decision: Monitor (87% confidence)"

4. **Auto-Enrollment** (if confidence >80)
   - Add repo to `repositories` table
   - Set priority based on detected patterns
   - Schedule first cookie extraction
   - Logs: "Repo enrolled, first extraction in 5min"

5. **Notification** (Optional)
   - Send email/Discord notification
   - Message: "Now monitoring user/awesome-project"

**Postconditions:**
- Repository added to monitoring list
- First cookie rotation scheduled
- User notified (if configured)

**Edge Cases:**
- Confidence 50-80 → Flag for manual review, notify user
- Confidence <50 → Ignore, log for future ML training
- Private repo without access → Log warning, skip

### Workflow 4: Handling Login Failures

**Actor:** System + LLM  
**Preconditions:** Cookie extraction attempt in progress  
**Trigger:** Login fails (wrong credentials, CAPTCHA, rate limit)

**Steps:**

1. **Failure Detection**
   - Browser detects login failure indicator
   - Capture screenshot (base64)
   - Extract error message from page
   - Logs: "Login failed: 'Too many attempts'"

2. **LLM Diagnosis**
   - Send error details + screenshot to GLM-4-Air
   - Prompt: "Diagnose this login failure"
   - Response: `{"issue_type": "rate_limit", "recommended_action": "wait", ...}`
   - Logs: "LLM diagnosis: Rate limit, wait 15min"

3. **Adaptive Retry**
   - Follow LLM recommendation:
     - `rate_limit` → Wait specified time
     - `captcha` → Rotate IP + headful mode
     - `credentials` → Alert user (invalid creds)
     - `2fa_required` → Flag for manual intervention
   - Logs: "Waiting 900 seconds before retry..."

4. **Retry Execution**
   - After wait period, retry with adapted strategy
   - If successful, log success and continue
   - If fails again, escalate or abort after 3 attempts

5. **Fallback Actions**
   - After 3 failures:
     - Mark cookie as "unhealthy"
     - Notify user via GitHub issue
     - Skip this repo for 24h
   - Logs: "Max retries exceeded, flagged for manual review"

**Postconditions:**
- Either cookie extracted or failure logged
- User notified if manual intervention needed
- System learns from failure for future attempts

**Edge Cases:**
- Network timeout → Retry immediately (transient)
- Platform maintenance → Wait 1h, retry
- Unknown error → Log for human review, skip

## 5.2 System States

### State Machine Diagram

```
[IDLE]
  ↓ (every 6 hours OR manual trigger)
[SCANNING_REPOS]
  ↓ (repos found needing rotation)
[PREPARING_ROTATION] → (IP rotation, browser setup)
  ↓
[EXTRACTING_COOKIES]
  ├─ (success) → [INJECTING_SECRETS]
  └─ (failure) → [DIAGNOSING_FAILURE]
                   ├─ (retry recommended) → [EXTRACTING_COOKIES]
                   └─ (abort) → [LOGGING_FAILURE] → [IDLE]
  ↓
[INJECTING_SECRETS]
  ↓ (all injected)
[VALIDATING_COOKIES]
  ├─ (valid) → [COMMITTING_STATE] → [IDLE]
  └─ (invalid) → [DIAGNOSING_FAILURE]
```

### State Persistence

**State File:** `state.json`

```json
{
  "last_run": "2026-02-10T15:30:00Z",
  "next_run": "2026-02-10T21:30:00Z",
  "repos_monitored": 42,
  "cookies_healthy": 39,
  "cookies_expiring_soon": 3,
  "cookies_failed": 0,
  "total_rotations": 127,
  "api_calls_this_month": 245,
  "cost_this_month": 0.12
}
```

## 5.3 User Interface (CLI)

### 5.3.1 Command-Line Interface

**Commands:**

```bash
# Main orchestrator (runs in GitHub Actions)
python orchestrator.py [OPTIONS]

Options:
  --shard-id INT          Shard ID for parallel processing (1-3)
  --shard-total INT       Total number of shards (default: 3)
  --force-rotation        Force rotation of all cookies
  --dry-run               Simulate actions without making changes
  --log-level LEVEL       Logging level (DEBUG|INFO|WARNING|ERROR)
  --platform PLATFORM     Only process specific platform
  --repo REPO             Only process specific repository

# Utility scripts
python scripts/init_db.py              # Initialize database
python scripts/encrypt_db.py           # Encrypt database for commit
python scripts/decrypt_db.py           # Decrypt database for processing
python scripts/generate_key.py         # Generate encryption key
python scripts/test_warp.py            # Test WARP connection
python scripts/validate_secrets.py     # Validate all injected secrets
python scripts/export_audit_log.py     # Export audit log to CSV
```

**Example Output:**

```
🚀 Cookie Guardian v1.0.0 - Starting...
📊 Shard 1/3 - Processing 14 repositories

🔍 Scanning repositories...
  ✅ user/repo-1 - Cookies healthy (expires in 45 days)
  ⚠️  user/repo-2 - Cookies expiring in 18 hours
  ❌ user/repo-3 - Cookies failed validation

🔄 Rotating 1 cookie...
  🌐 Connecting to WARP... ✅ (IP: 104.28.2.5)
  🌐 Launching browser... ✅
  🔐 Logging in to github.com... ✅
  🍪 Extracting cookies... ✅ (2 cookies found)
  💾 Encrypting and storing... ✅
  🔒 Injecting GitHub Secret... ✅
  ✅ Validation passed

📈 Summary:
  • Repositories processed: 14
  • Cookies rotated: 1
  • Cookies validated: 14
  • Failures: 0
  • LLM API calls: 2
  • Cost: $0.0008

⏰ Next run: 2026-02-10T21:30:00Z
```

### 5.3.2 Logging

**Log Levels:**
- **DEBUG:** Detailed technical logs (browser commands, API requests)
- **INFO:** Normal operations (repo scanned, cookie rotated)
- **WARNING:** Recoverable issues (retry needed, low confidence decision)
- **ERROR:** Failures requiring attention (login failed after retries)

**Log Format (JSON):**

```json
{
  "timestamp": "2026-02-10T15:30:00Z",
  "level": "INFO",
  "component": "browser_automation",
  "message": "Cookie extracted successfully",
  "metadata": {
    "repo": "user/awesome-project",
    "platform": "github",
    "cookies_found": 2,
    "duration_ms": 45234
  }
}
```

## 5.4 Monitoring & Alerting

### 5.4.1 Health Metrics

**Tracked Metrics:**
- Cookie freshness (% of cookies <24h from expiry)
- Rotation success rate (%)
- Average extraction time (seconds)
- API cost per day ($)
- Failed rotations count
- Repos monitored count

**Dashboard (GitHub Actions Summary):**

```
Cookie Guardian Health Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 System Status: HEALTHY

Repositories: 42
  • Healthy: 39 (93%)
  • Expiring soon: 3 (7%)
  • Failed: 0 (0%)

Rotations (Last 7 days): 18
  • Success: 17 (94%)
  • Failed: 1 (6%)

Performance:
  • Avg extraction time: 52s
  • Avg LLM response: 1.8s
  • WARP uptime: 99.8%

Costs (This month):
  • GLM API: $0.18
  • Total: $0.18

Next actions:
  ⚠️  3 cookies expiring in <24h
```

### 5.4.2 Alerting (Optional)

**Alert Channels:**
- GitHub Issues (auto-created for critical failures)
- Email (via GitHub Actions notifications)
- Discord webhook (if configured)

**Alert Triggers:**
- Cookie rotation failed 3+ times
- Cookie expired (broke workflow)
- API budget >90% consumed
- WARP connection failed
- Database corruption detected

**Sample Alert:**

```
🚨 Cookie Guardian Alert

Severity: HIGH
Repository: user/critical-project
Issue: Cookie rotation failed after 3 attempts

Details:
  • Platform: github.com
  • Last successful rotation: 2026-02-08T10:00:00Z
  • Failure reason: Rate limit (429)
  • Recommended action: Check GitHub login rate limits

Action required:
  1. Verify credentials are still valid
  2. Check for platform-wide issues
  3. Manually rotate cookie if urgent

View logs: https://github.com/user/cookie-guardian/actions/runs/12345
```

## 5.5 Testing Requirements

### 5.5.1 Unit Tests

**Test Coverage Requirements:** >80%

**Key Test Cases:**

```python
# tests/test_repo_discovery.py
def test_detect_cookie_in_env_example():
    """Should detect COOKIE_ vars in .env.example"""
    content = "GITHUB_SESSION=your_cookie_here"
    result = detect_cookie_patterns(content)
    assert "session" in result.cookie_names

def test_confidence_calculation():
    """Should calculate confidence from multiple signals"""
    signals = [
        Signal("env_var", strength=0.9),
        Signal("readme_mention", strength=0.7),
        Signal("code_pattern", strength=0.8)
    ]
    confidence = calculate_confidence(signals)
    assert 80 <= confidence <= 95

# tests/test_browser_automation.py
@pytest.mark.asyncio
async def test_stealth_browser_passes_detection():
    """Should pass sannysoft.com bot detection tests"""
    browser = await launch_stealth_browser()
    page = await browser.new_page()
    await page.goto("https://bot.sannysoft.com")
    
    # Check for detection flags
    webdriver_detected = await page.eval("navigator.webdriver")
    assert webdriver_detected is None

@pytest.mark.asyncio
async def test_cookie_extraction():
    """Should extract cookies from authenticated session"""
    cookies = await extract_cookies("github.com", TEST_CREDENTIALS)
    assert "user_session" in [c["name"] for c in cookies]
    assert all(c["domain"] == ".github.com" for c in cookies)

# tests/test_warp_manager.py
def test_warp_connection():
    """Should connect to WARP successfully"""
    warp = WARPManager()
    assert warp.connect() is True
    assert warp.verify_active() is True
    assert warp.get_current_ip() is not None

def test_ip_rotation():
    """Should rotate IP on demand"""
    warp = WARPManager()
    warp.connect()
    
    old_ip = warp.get_current_ip()
    new_ip = warp.rotate_ip()
    
    assert new_ip != old_ip
    assert warp.verify_active() is True

# tests/test_secrets_injection.py
@pytest.mark.asyncio
async def test_secret_encryption():
    """Should encrypt secrets with Libsodium"""
    public_key = get_test_public_key()
    secret = {"session": "abc123"}
    
    encrypted = encrypt_secret(json.dumps(secret), public_key)
    assert isinstance(encrypted, str)
    assert len(encrypted) > 100  # Encrypted should be longer

@pytest.mark.asyncio
async def test_secret_injection():
    """Should inject secret via GitHub API"""
    mock_api = MockGitHubAPI()
    
    success = await inject_cookie_secret(
        "user/repo",
        "github.com",
        {"session": "test"}
    )
    
    assert success is True
    assert mock_api.secrets["COOKIE_GITHUB_COM_SESSION"] is not None

# tests/test_glm_integration.py
@pytest.mark.asyncio
async def test_llm_repo_analysis():
    """Should analyze repo and return structured decision"""
    llm = GLMDecisionEngine(TEST_API_KEY)
    
    repo_data = {
        "name": "test-repo",
        "readme": "Requires GitHub authentication",
        "env_vars": ["GITHUB_SESSION"],
        "patterns": ["Cookie.get('session')"]
    }
    
    decision = await llm.analyze_repo(repo_data)
    
    assert "requires_cookies" in decision
    assert "confidence" in decision
    assert decision["requires_cookies"] is True
    assert 70 <= decision["confidence"] <= 100

@pytest.mark.asyncio
async def test_llm_failure_diagnosis():
    """Should diagnose login failure correctly"""
    llm = GLMDecisionEngine(TEST_API_KEY)
    
    error_log = "HTTP 429: Too Many Requests"
    diagnosis = await llm.diagnose_failure(error_log, "github")
    
    assert diagnosis["issue_type"] == "rate_limit"
    assert diagnosis["recommended_action"] == "wait"
    assert diagnosis["wait_time_seconds"] > 0
```

### 5.5.2 Integration Tests

```python
# tests/integration/test_end_to_end.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_rotation_cycle():
    """Test complete cookie rotation workflow"""
    
    # Setup
    db = await init_test_database()
    repo = await create_test_repo("user/test", requires_cookies=True)
    
    # Run orchestrator
    result = await run_orchestrator(
        repos=[repo],
        force_rotation=True
    )
    
    # Verify
    assert result.success is True
    assert result.cookies_rotated == 1
    
    # Check database updated
    cookie = await db.get_latest_cookie(repo.id)
    assert cookie.extracted_at > datetime.now() - timedelta(minutes=5)
    
    # Check secret injected
    secret = await github_api.get_secret(repo.full_name, "COOKIE_GITHUB_COM_SESSION")
    assert secret is not None
```

### 5.5.3 Load Testing

**Scenarios:**

1. **Parallel Processing:**
   - Test 3 shards processing 100 repos each
   - Verify no database conflicts
   - Ensure API rate limits respected

2. **Heavy Cookie Load:**
   - 1000 cookies all expiring simultaneously
   - System should queue and process without OOM

3. **API Quota Management:**
   - Simulate GLM API rate limit hit
   - Verify graceful degradation to rule-based fallback

---

# APPENDICES

## Appendix A: Platform-Specific Configurations

### GitHub.com
```yaml
platform: github
login_url: https://github.com/login
selectors:
  username: "input[name='login']"
  password: "input[name='password']"
  submit: "input[type='submit'][value='Sign in']"
cookie_names:
  - user_session
  - _gh_sess
  - logged_in
expiry_default: 90  # days
notes: "May require 2FA for some accounts"
```

### Google.com
```yaml
platform: google
login_url: https://accounts.google.com
selectors:
  email: "input[type='email']"
  email_next: "#identifierNext"
  password: "input[type='password']"
  password_next: "#passwordNext"
cookie_names:
  - SID
  - HSID
  - SSID
  - APISID
expiry_default: 30  # days
notes: "Requires handling multi-step login flow"
```

## Appendix B: Security Checklist

- [ ] All secrets stored in GitHub Actions Secrets (not code)
- [ ] Encryption key rotated every 90 days
- [ ] Database encrypted before git commit
- [ ] WARP enabled for all browser traffic
- [ ] Browser launched in headless mode (production)
- [ ] Canvas/WebGL fingerprints randomized
- [ ] User-Agent rotation enabled
- [ ] Audit log includes all sensitive operations
- [ ] No credentials logged in plaintext
- [ ] GitHub Actions workflow uses minimal permissions
- [ ] Secrets scoped to step-level where possible
- [ ] Dependencies pinned to specific versions
- [ ] Security scanning enabled (Dependabot)
- [ ] Code review required before deploy

## Appendix C: Troubleshooting Guide

### Issue: WARP won't connect

**Symptoms:** `warp-cli connect` times out

**Solutions:**
1. Check daemon status: `sudo systemctl status warp-svc`
2. Restart service: `sudo systemctl restart warp-svc`
3. Re-register: `warp-cli registration delete && warp-cli register`
4. Check firewall allows UDP 2408

### Issue: Bot detection triggered

**Symptoms:** CAPTCHA appears, login blocked

**Solutions:**
1. Rotate IP: `warp-cli rotate_ip()`
2. Switch to headful mode: `headless=False`
3. Increase delays: `typing_delay_ms=(100, 500)`
4. Use different user agent pool
5. Check if platform has new anti-bot measures

### Issue: GLM API quota exceeded

**Symptoms:** API returns 429 or quota error

**Solutions:**
1. Check usage: `scripts/check_api_usage.py`
2. Reduce decision frequency (use caching)
3. Fallback to rule-based logic
4. Upgrade to paid tier if critical

### Issue: Cookie expired despite rotation

**Symptoms:** Workflow fails with auth error

**Solutions:**
1. Check cookie expiry prediction accuracy
2. Reduce rotation threshold (12h instead of 24h)
3. Verify cookie extracted correctly
4. Platform may have changed expiry policy

## Appendix D: Cost Breakdown

**Monthly Operational Costs (50 repos):**

| Component | Cost |
|-----------|------|
| GitHub Actions (2000 min free) | $0.00 |
| Cloudflare WARP | $0.00 |
| GLM-4-Air API (~10 decisions/day) | $0.18 |
| **Total** | **$0.18** |

**Scaling Costs (500 repos):**

| Component | Cost |
|-----------|------|
| GitHub Actions (may exceed free tier) | ~$5.00 |
| GLM-4-Air API (~50 decisions/day) | $0.90 |
| **Total** | **$5.90** |

## Appendix E: Glossary

- **AES-256:** Advanced Encryption Standard with 256-bit keys
- **CAPTCHA:** Challenge test to distinguish humans from bots
- **Circuit Breaker:** Pattern to prevent cascading failures
- **Expiry Prediction:** ML-based estimation of cookie lifetime
- **Fingerprinting:** Technique to uniquely identify browsers
- **GLM-4-Air:** Lightweight LLM for decision-making
- **Libsodium:** Cryptography library for sealed box encryption
- **MoE:** Mixture of Experts (neural network architecture)
- **Playwright:** Browser automation framework
- **Sealed Box:** Asymmetric encryption (public key only)
- **Shard:** Portion of workload in parallel processing
- **Stealth Mode:** Anti-detection browser configuration
- **WARP:** Cloudflare's VPN/proxy service
- **WebGL:** Web Graphics Library (browser fingerprint vector)

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-10 | Cookie Guardian Team | Initial production release |

---

**END OF DOCUMENT**

Total Pages: 65+  
Word Count: ~22,000  
Estimated Reading Time: 90 minutes
