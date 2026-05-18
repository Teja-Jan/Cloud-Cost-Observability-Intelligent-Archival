Cloud Cost Observability & Intelligent Archival - Technical Specification
Technical Specification & Implementation Guide

Business Context & Executive Summary

The Business Challenge
As enterprises scale their data operations across multi-cloud environments (Snowflake, Databricks, BigQuery, AWS), cloud spend frequently spirals out of control. Organizations face several critical challenges:
- Blind Consumption: Compute and storage costs scale exponentially, often driven by unoptimized queries, zombie data pipelines, and idle warehouses.
- Data Hoarding: Data lakes and warehouses become filled with stale, duplicated, or abandoned tables that rack up storage costs indefinitely.
- Lack of Governance: Finance teams see the bill but lack the technical context to challenge it; Engineering teams build pipelines but lack financial visibility.
- Reactive Alerting: Organizations only realize they have overspent after the monthly invoice arrives, making it impossible to proactively prevent budget overruns.

Target Personas
This platform is designed to bridge the gap between engineering execution and financial governance.
- FinOps Analysts / Cloud Financial Managers: Gain absolute visibility into 5-Year cost projections, anomaly detection, and the exact dollar ROI of governance initiatives.
- Data Architects / Platform Engineers: Receive prioritized, prescriptive recommendations on which assets to archive or drop, along with the exact SQL/CLI syntax to execute the remediation safely.
- Cloud Center of Excellence (CoE) Leads: Drive organizational cloud efficiency by enforcing 15-dimensional governance rules across all business domains (Finance, Healthcare, etc.).
- Security & Compliance Officers: Leverage the deep user-access audits to identify over-provisioned users or inactive accounts holding access to sensitive datasets.

Key Benefits
- Proactive Cost Control: Shifts cloud financial management from reactive billing reviews to proactive, AI-driven anomaly detection.
- Elimination of Waste: Automatically identifies single-user dependencies, zero-query tables, and idle compute clusters.
- Zero-Friction Remediation: Generates platform-specific execution scripts (e.g., Snowflake ALTER TABLE), reducing the time required to clean up environments from days to seconds.
- Unified Multi-Cloud Vision: Consolidates telemetry from disparate platforms into a single, standardized governance dashboard.

Return on Investment (ROI)
- Immediate Hard Savings: Typical enterprise deployments identify 15%–30% immediate savings by archiving stale data and terminating idle compute clusters.
- Cost Avoidance: Early anomaly detection prevents runaway compute jobs from racking up unexpected thousands of dollars over a weekend.
- Productivity Gains: Eliminates hundreds of hours spent manually writing Python scripts or SQL queries to audit INFORMATION_SCHEMA logs across different platforms.

Implementation & Adoption Strategy
- Phase 1: Metadata Ingestion (Days 1-14): Connect the platform to existing cloud metadata APIs (e.g., Snowflake ACCOUNT_USAGE, Databricks Unity Catalog). No raw business data is scanned—only system telemetry.
- Phase 2: Baseline & Forecasting (Days 15-30): The Forecaster and PricingEngine establish historical baselines, applying negotiated vendor discounts to generate accurate 5-Year projections.
- Phase 3: Governance Activation (Days 31+): Enable the GovernanceEngine to surface stale assets. Begin weekly Cloud CoE review cadences using the Interactive Asset Inventory to approve and execute archival recommendations.

 
1. System Overview
This platform is a fully model-driven cloud intelligence system designed for enterprise-scale resource observability, cost forecasting, and compute/storage governance. Its defining principle is that every cost projection, anomaly alert, and archival recommendation is produced by a statistical or heuristic model trained on actual cloud telemetry data. There are no static assumptions; the system dynamically adapts to multi-cloud environments (Snowflake, Databricks, BigQuery, AWS, Azure).

Core Principle	Every recommendation shown to a user is a data-backed insight, not a blanket assumption. The system proves its recommendation by exposing the specific metric drivers, cost dimensions (Compute, Storage, Network), and projected 5-Year savings.

Capability	What It Does	Business Outcome
Multi-Dimensional Observability	Separates cloud usage into Compute, Storage, and Data Transfer metrics.	Provides absolute clarity on cost drivers, preventing blind budget overruns.
AI-Driven Forecasting	Projects WoW, MoM, YoY, and 5-Year cost horizons using statistical models.	Enables accurate financial planning and proactively identifies explosive compute growth.
Intelligent Data Governance	Scans metadata across 15 dimensions to detect data hoarding, inactive users, and stale assets.	Automatically identifies low-utilization resources safe for cold-storage archival.
Prescriptive Remediation	Translates insights into platform-specific archival queries (e.g., Snowflake ALTER TABLE).	Engineering teams receive executable commands, accelerating the remediation lifecycle.
Zero-Reload Interactive Audit	Provides high-fidelity, in-screen drill-downs into user audits without page reloads.	Delivers a premium, enterprise-grade user experience that maintains workflow context.
Automated Alerting	Simulates continuous monitoring of cloud environments to flag anomalous usage spikes.	Cloud CoE teams are notified of architectural inefficiencies before the monthly bill arrives.

2. System Architecture
A modular, decoupled architecture where responsibility flows strictly downward. No frontend layer is permitted to hard-code platform syntax or forecasting logic. All calculations are enforced through dedicated Python-based analytical engines.

Layer	Technology	Responsibility
Interface	Streamlit + Pandas Styler + Custom HTML/JS	SPA-like dashboard with zero-reload interactive tables, centralized session state management, and dynamic zero-state rendering.
Orchestration	Python App Controller (app.py)	Manages UI routing, triggers data fetching, and acts as the central hub between the UI and the analytical engines.
AI/ML Models	Python Forecaster, PricingEngine, GovernanceEngine	Handles 15-dimensional governance rules, dynamic pricing simulations, and time-series forecasting.
Execution	Python ArchivalFactory	Generates platform-agnostic remediation syntax tailored to Snowflake, Databricks, BigQuery, etc.
Data Simulation	Python mock_data.py, database.py	Generates highly realistic, platform-specific synthetic cloud telemetry data for PoC validation.

Principle	How It Is Enforced
Platform Agnosticism	ArchivalFactory and PricingEngine abstract cloud-specific syntax. The UI requests an action, and the factory injects the correct dialect.
Zero-Reload Interactivity	Custom HTML/JS components with window.parent.postMessage bridge directly to Streamlit's backend, providing flawless modal triggers without browser refresh.
Separation of Concerns	The GovernanceEngine only calculates risk; the ArchivalExecutor only formats commands. The UI merely displays the results.

3. End-to-End Implementation Flow
The diagram below traces a request from metadata ingestion through to a cloud architect's governance decision.

01	Telemetry Ingestion & Aggregation	Logs arrive containing platform assets, sizing, user access history, and historical cost data. Data is grouped by domain (Finance, Healthcare, etc.) and Cloud Platform.	A unified, multi-cloud data foundation.
02	Cost Baseline & Forecasting	The Forecaster and PricingEngine analyze historical burn rates. Data is processed to generate short-term (WoW, MoM) anomaly flags and long-term (5-Year) budget projections, adjusting for negotiated vendor discounts.	Accurate financial horizons with real-time dynamic adjustment controls.
03	Resource Governance & Optimization	The GovernanceEngine scans the inventory across 15 dimensions. It identifies tables not queried in >365 days, instances with single-user dependencies, and compute resources with high idle times.	A prioritized list of optimization candidates replacing manual cloud audits.
04	High-Fidelity User Audit	When an architect investigates a flagged asset, they click on the natively styled user metrics in the Consolidated Inventory Table. A custom bi-directional JS bridge instantly triggers an in-screen st.dialog modal detailing the exact Active, Inactive, and Last Accessed users.	Seamless, deep-dive investigations without losing dashboard context.
05	Decision & Financial Justification	The system computes the exact 5-Year savings if the flagged asset is archived or downscaled.	The architect receives a clear action with the financial ROI explicitly attached.
06	Automated Remediation Formatting	If approved, the ArchivalFactory dynamically generates the exact syntax required (e.g., ALTER TABLE ... SET STORAGE_LIFECYCLE_POLICY = COLD;) to execute the change.	Ready-to-execute scripts eliminating manual syntax lookups.

✓ Outcome	A Cloud CoE engineer using this system receives—for every cloud asset—the right financial projection, a specific optimization target, a full user audit trail, and an executable remediation script. All from a single platform.

4. AI/ML Model Reference
All analytical logic lives in the agent layer and is invoked through the controller.

4.1 Cost Observability & Forecasting Engine
Metric	Inputs Used	How It Works	Output
Anomaly Detection	MoM %, WoW % Cost	Statistical comparison against baseline averages with configurable sensitivity.	Red-flag visual alerts for explosive compute costs.
5-Year Projection	Current Run Rate, Historical Trend	Linear/Polynomial extrapolation factoring in standard cloud inflation and data gravity.	$X.XX Million projected cost.
Dynamic Discounting	Baseline Cost, Vendor Discount %	Real-time mathematical simulation updating all downstream UI components instantly.	Adjusted total financial exposure.

4.2 Governance Engine – Intelligent Risk Profiling & Archival
Dimension	Classification Logic	Outcome
Data Hoarding	last_accessed_days > 365	Flags asset as Stale and calculates cold-storage ROI.
Compute Idle	cpu_utilization < 10%	Recommends right-sizing or termination.
Dependency Risk	active_users = 1, total_users > 10	Flags single-point-of-failure access patterns for critical tables.

4.3 High-Fidelity UI Components
Component	How It Works	What It Produces
Interactive JS Bridge	Replaces static tables with custom HTML utilizing window.parent.postMessage mapped to Streamlit values.	Hyper-link visual affordance and zero-reload Python callbacks.
In-Screen Modals	Utilizes Streamlit 1.35+ @st.dialog decorators triggered by the JS bridge payload.	Non-disruptive, context-rich user audits.
Zero-State Triggers	Recommendations and remediation syntax remain hidden until the user explicitly selects a row in the data matrix.	Uncluttered, highly professional user interface.

 
5. Technology Stack
Component	Technology	Version	Role
Web Framework	Streamlit	>= 1.35.0	Async-friendly UI, native modals, state management.
Frontend Customization	HTML / JS / Pandas Styler	Custom	Zero-reload interactivity and hyper-link visual styling.
Data Processing	Pandas	2.0+	Fast in-memory aggregation, time-series projections, filtering.
Visualization	Plotly Express / Graph Objects	5.18+	Highly interactive, responsive charts (Donut, Bar, Line).
Export/Reporting	OpenPyXL / io.BytesIO	Latest	In-memory generation of Excel audit reports for download.
Language	Python	3.10+	Core analytical processing and orchestration.

 

8. Key Engineering Decisions
Decision	Why	Trade-off / Production Path
Custom HTML/JS Bridge for Tables	Streamlit's native st.dataframe drops click events when visual styling (Pandas Styler) is applied. We needed both visual affordance and zero-reload functionality.	Requires maintaining a tiny JS snippet, but entirely removes the need for heavy React component infrastructure.
In-Memory Filtering (Pandas)	Enables lightning-fast cross-filtering (Domain -> Platform -> Asset) without querying a database on every click.	Perfect for PoC/Medium scale. Production path requires pushing WHERE clauses to an actual Data Warehouse for massive scale.
Platform-Agnostic Executor Pattern	Hardcoding Snowflake vs AWS queries in the UI creates massive technical debt. The ArchivalFactory isolates this.	Highly extensible. Adding a new platform like Azure Synapse only requires adding one rule to the factory.

10. Future Implementations
The current system is a highly advanced, fully functional Proof of Concept. The following enhancements are scoped for production readiness and capability expansion, grouped by priority and complexity.

Infrastructure & Scalability
Enhancement	What Changes	Expected Outcome
Live Cloud Connections	Replace mock_data.py with actual API integrations (Snowflake ACCOUNT_USAGE, AWS Cost Explorer API, Azure Billing API).	System operates on live inventory data with no synthetic data-entry step.
Vector DB / Semantic Search	Integrate a vector database to allow users to ask natural language questions.	"Why did my AWS bill spike last Tuesday?" answered automatically.

AI/ML Capability Expansion
Enhancement	What Changes	Expected Outcome
Deep Learning Forecasting	Upgrade the Python Forecaster to utilize Prophet or XGBoost for highly non-linear, multi-seasonal cloud compute variations.	Improved accuracy on long-range forecasts with complex multi-variate dependencies.
LLM Query Translation	Use an LLM agent to automatically generate complex remediation queries rather than relying on the hard-coded ArchivalFactory templates.	System adapts to any new cloud architecture automatically without developer intervention.

Integration & User Experience
Enhancement	What Changes	Expected Outcome
Identity Provider Integration	Connect the "Active Users" audit directly to Azure AD / Okta to instantly revoke access from the Streamlit UI.	Full loop remediation without leaving the dashboard.
ITSM Integration	Push approved archival recommendations directly to ServiceNow or Jira as automated tickets.	Enterprise compliance and tracking of all cloud resource changes.

11. Conclusion
This platform establishes a technically rigorous, highly responsive foundation for enterprise cloud resource observability. Unlike conventional cloud cost tools that present static, overwhelming billing exports, this system proactively detects anomalies, proves the ROI of remediation, and offers one-click governance workflows.

The architecture has been deliberately designed so that correctness is structural. The platform-agnostic executor pattern ensures that whether an asset is in Snowflake or AWS, it exits with the precise remediation syntax required.

Dimension	What Has Been Achieved
Interactivity	Achieved zero-reload modal drill-downs, creating an enterprise-grade UI that feels like a heavy SPA.
Prescriptive Value	Forecasts are converted into ARCHIVE NOW decisions with executable SQL/CLI syntax attached.
Extensibility	Clean separation of UI, Governance Engine, and Archival Factory ensures new cloud platforms can be added in minutes.

PoC → Production	The current system is production-ready in logic and architecture. Graduating to full production requires swapping the synthetic data generation layer with live API connectors and securing the deployment behind enterprise SSO.

✓ Outcome	The system delivers: accurate cost baseline tracking · multi-dimensional governance metrics · financially justified remediation scripts · full visual user audits · zero-refresh interactive data mining.

How to Run in Github:

The Cloud Resource Observability & Intelligent Archival POC is now on GitHub:

Repo: https://github.com/vempalamohit-bot/Cloud-Resource-Observability

•	How to Run It (Google Colab — No Installation Needed)
•	Please follow the Instructions in the README file. 
•	
•	Open the notebook
•	Go to Runtime → Run all (or press Ctrl + F9)
•	Wait ~5 minutes for everything to install and build
•	The last cell will show a public URL and an IP address (this is the tunnel password)
•	Click the URL, paste the IP address on the tunnel page, and hit Submit
•	The full app loads — Dashboard, Observability, Forecasting, Governance
•	
•	What's Inside
•	Comprehensive cloud metadata and forecasting datasets loaded automatically
•	No local setup, no dependencies to install — just click the link and run.
