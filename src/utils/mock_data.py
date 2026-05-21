"""
Realistic Enterprise Mock Data Generator
-----------------------------------------
Generates deterministic, enterprise-grade cloud asset and usage data.
All names, schemas, and metrics are modelled after real-world Fortune 500
data warehouse patterns across Healthcare, Finance, Insurance, Supply Chain,
and Automotive domains.

No external Faker dependency — fully reproducible with a fixed random seed.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

random.seed(42)
np.random.seed(42)

PLATFORMS = [
    "Snowflake", "Databricks", "BigQuery", "AWS", "Azure",
    "Google Cloud Platform", "Oracle Cloud Infrastructure", "IBM Cloud"
]

DOMAINS = ["Healthcare", "Finance", "Insurance", "Supply Chain", "Automotive"]

# ─── Realistic enterprise naming dictionaries ──────────────────────────────

DOMAIN_DB_SCHEMAS = {
    "Healthcare": {
        "databases": ["ehr_prod_db", "claims_warehouse", "hl7_integration_db", "patient_360_db"],
        "schemas": {
            "ehr_prod_db":        ["clinical_records", "lab_results", "pharmacy", "billing", "audit_log"],
            "claims_warehouse":   ["adjudication", "member_eligibility", "provider_network", "fraud_analytics"],
            "hl7_integration_db": ["inbound_feeds", "outbound_acks", "message_archive"],
            "patient_360_db":     ["demographics", "care_plans", "appointments", "referrals"],
        }
    },
    "Finance": {
        "databases": ["gl_prod_db", "trading_warehouse", "risk_analytics_db", "customer_360_db"],
        "schemas": {
            "gl_prod_db":         ["journal_entries", "accounts_payable", "accounts_receivable", "fixed_assets", "consolidation"],
            "trading_warehouse":  ["equities", "fixed_income", "derivatives", "settlements", "positions"],
            "risk_analytics_db":  ["credit_risk", "market_risk", "liquidity_risk", "stress_testing"],
            "customer_360_db":    ["retail_banking", "wealth_mgmt", "loan_origination", "kyc_aml"],
        }
    },
    "Insurance": {
        "databases": ["policy_prod_db", "claims_db", "underwriting_db", "actuarial_db"],
        "schemas": {
            "policy_prod_db":     ["personal_lines", "commercial_lines", "life_annuities", "renewals"],
            "claims_db":          ["first_notice_loss", "claims_adjudication", "subrogation", "fraud_detection"],
            "underwriting_db":    ["risk_scoring", "pricing_models", "applications", "bind_history"],
            "actuarial_db":       ["loss_development", "reserve_estimates", "catastrophe_models", "experience_studies"],
        }
    },
    "Supply Chain": {
        "databases": ["scm_prod_db", "inventory_db", "logistics_db", "supplier_db"],
        "schemas": {
            "scm_prod_db":    ["purchase_orders", "demand_forecasting", "production_planning", "bill_of_materials"],
            "inventory_db":   ["warehouse_stock", "cycle_counts", "abc_analysis", "safety_stock"],
            "logistics_db":   ["shipment_tracking", "carrier_performance", "route_optimization", "last_mile"],
            "supplier_db":    ["vendor_master", "contract_management", "risk_assessment", "scorecards"],
        }
    },
    "Automotive": {
        "databases": ["vehicle_prod_db", "telematics_db", "dealer_network_db", "warranty_db"],
        "schemas": {
            "vehicle_prod_db":   ["vin_registry", "production_orders", "quality_control", "recall_management"],
            "telematics_db":     ["gps_events", "engine_diagnostics", "driver_behavior", "adas_logs"],
            "dealer_network_db": ["inventory_feed", "sales_transactions", "service_appointments", "crm_leads"],
            "warranty_db":       ["claims_history", "parts_catalog", "labor_codes", "supplier_defects"],
        }
    },
}

# Realistic table name templates per schema
TABLE_TEMPLATES = {
    "clinical_records":    ["patient_encounters", "diagnosis_codes", "procedure_log", "vital_signs_history", "discharge_summary", "admission_records"],
    "lab_results":         ["specimen_orders", "lab_results_detail", "reference_ranges", "critical_alerts", "pending_orders"],
    "pharmacy":            ["medication_orders", "dispensing_log", "drug_interactions", "formulary_master", "refill_requests"],
    "billing":             ["claim_submissions", "eob_records", "remittance_advice", "denial_tracking", "revenue_cycle"],
    "audit_log":           ["user_access_log", "data_change_history", "login_events", "failed_auth_attempts"],
    "adjudication":        ["claim_decisions", "auto_adjudication_rules", "manual_review_queue", "payment_batches"],
    "member_eligibility":  ["member_roster", "coverage_periods", "benefit_elections", "cobra_tracking"],
    "provider_network":    ["provider_directory", "contract_rates", "credentialing_status", "performance_metrics"],
    "fraud_analytics":     ["anomaly_scores", "flagged_claims", "investigation_cases", "recovery_tracking"],
    "inbound_feeds":       ["hl7_messages_raw", "feed_manifest", "parsing_errors", "adt_events"],
    "outbound_acks":       ["ack_queue", "nack_log", "transmission_history"],
    "message_archive":     ["archived_hl7_2015", "archived_hl7_2016", "archived_hl7_2017", "archived_hl7_2018", "archived_hl7_2019"],
    "demographics":        ["patient_master", "address_history", "contact_preferences", "consent_records"],
    "care_plans":          ["active_care_plans", "completed_care_plans", "goal_tracking", "care_team_assignments"],
    "appointments":        ["scheduled_visits", "cancelled_visits", "no_show_log", "waitlist"],
    "referrals":           ["referral_requests", "specialist_assignments", "referral_outcomes"],
    "journal_entries":     ["daily_je", "adjusting_entries", "accruals", "reversals", "intercompany_je"],
    "accounts_payable":    ["vendor_invoices", "payment_runs", "aged_payables", "three_way_match"],
    "accounts_receivable": ["customer_invoices", "cash_receipts", "aged_receivables", "dunning_log"],
    "fixed_assets":        ["asset_register", "depreciation_schedule", "disposal_log", "capex_projects"],
    "consolidation":       ["entity_hierarchy", "eliminations", "currency_translation", "intercompany_balances"],
    "equities":            ["equity_positions", "trade_blotter", "corporate_actions", "pricing_feed"],
    "fixed_income":        ["bond_positions", "coupon_schedule", "duration_analytics", "yield_curve"],
    "derivatives":         ["options_positions", "futures_contracts", "swap_valuations", "margin_calls"],
    "settlements":         ["settlement_instructions", "nostro_reconciliation", "failed_trades", "settlement_confirmations"],
    "positions":           ["daily_positions", "intraday_positions", "position_history_2019", "position_history_2020"],
    "credit_risk":         ["pd_models", "lgd_estimates", "ead_calculations", "ecl_staging"],
    "market_risk":         ["var_calculations", "pnl_attribution", "sensitivity_reports", "backtesting_results"],
    "liquidity_risk":      ["lcr_reporting", "nsfr_metrics", "cash_flow_projections", "stress_scenarios"],
    "stress_testing":      ["scenario_definitions", "stress_results", "regulatory_submissions", "model_validation"],
    "retail_banking":      ["current_accounts", "savings_accounts", "transaction_history", "product_holdings"],
    "wealth_mgmt":         ["portfolio_holdings", "client_mandates", "rebalancing_log", "performance_attribution"],
    "loan_origination":    ["applications", "credit_decisions", "loan_master", "disbursement_schedule"],
    "kyc_aml":             ["customer_due_diligence", "pep_screening", "sanctions_check", "sar_filings"],
    "personal_lines":      ["auto_policies", "home_policies", "umbrella_policies", "endorsements"],
    "commercial_lines":    ["gl_policies", "property_policies", "excess_surplus", "binders"],
    "life_annuities":      ["life_policies", "annuity_contracts", "beneficiary_records", "surrender_log"],
    "renewals":            ["renewal_offers", "non_renewal_notices", "lapse_history", "reinstatements"],
    "first_notice_loss":   ["fnol_submissions", "incident_reports", "initial_reserves", "assignment_queue"],
    "claims_adjudication": ["adjudication_decisions", "payment_history", "reserve_movements", "litigation_tracking"],
    "subrogation":         ["subrogation_cases", "recovery_amounts", "third_party_liability"],
    "fraud_detection":     ["fraud_scores", "rule_engine_output", "analyst_decisions", "model_feedback"],
    "risk_scoring":        ["applicant_scores", "pricing_factors", "decline_reasons", "model_versions"],
    "pricing_models":      ["rate_tables", "discount_schedules", "competitive_pricing", "rate_change_history"],
    "applications":        ["new_business_apps", "endorsement_requests", "cancellation_requests"],
    "bind_history":        ["bound_policies_2021", "bound_policies_2022", "bound_policies_2023", "bound_policies_2024"],
    "loss_development":    ["development_triangles", "tail_factors", "selected_ultimates"],
    "reserve_estimates":   ["booked_reserves", "ibnr_estimates", "case_reserves", "actuarial_adjustments"],
    "catastrophe_models":  ["event_catalog", "exposure_data", "modeled_losses", "return_period_analysis"],
    "experience_studies":  ["mortality_experience", "morbidity_experience", "lapse_experience", "premium_experience"],
    "purchase_orders":     ["po_header", "po_line_items", "po_approval_log", "goods_receipt"],
    "demand_forecasting":  ["demand_signals", "forecast_accuracy", "statistical_forecasts", "consensus_forecasts"],
    "production_planning": ["mrp_runs", "work_orders", "capacity_requirements", "production_schedule"],
    "bill_of_materials":   ["bom_header", "bom_components", "engineering_changes", "bom_archive_2020"],
    "warehouse_stock":     ["stock_on_hand", "stock_movements", "lot_tracking", "serialized_inventory"],
    "cycle_counts":        ["count_plans", "count_results", "variance_analysis", "recount_requests"],
    "abc_analysis":        ["abc_classification", "velocity_analysis", "slow_moving_report"],
    "safety_stock":        ["safety_stock_parameters", "reorder_points", "service_level_targets"],
    "shipment_tracking":   ["shipment_headers", "tracking_events", "delivery_confirmations", "exception_log"],
    "carrier_performance": ["carrier_scorecards", "on_time_delivery", "damage_claims", "rate_audit"],
    "route_optimization":  ["optimized_routes", "route_performance", "fuel_consumption", "co2_emissions"],
    "last_mile":           ["delivery_attempts", "pod_records", "customer_feedback", "returns"],
    "vendor_master":       ["supplier_profiles", "bank_details", "certifications", "diversity_classifications"],
    "contract_management": ["active_contracts", "expiring_contracts", "contract_amendments", "sow_documents"],
    "risk_assessment":     ["supplier_risk_scores", "financial_health", "geo_risk", "cyber_risk"],
    "scorecards":          ["quarterly_scorecards", "kpi_definitions", "target_vs_actual"],
    "vin_registry":        ["vehicle_master", "vin_decode_cache", "recall_associations", "ownership_history"],
    "production_orders":   ["shop_orders", "routing_steps", "component_pickings", "completion_confirmations"],
    "quality_control":     ["inspection_results", "defect_log", "corrective_actions", "supplier_quality"],
    "recall_management":   ["recall_campaigns", "affected_vins", "remedy_completions", "dealer_notifications"],
    "gps_events":          ["raw_gps_telemetry", "trip_summaries", "geofence_events", "historical_gps_2021", "historical_gps_2022"],
    "engine_diagnostics":  ["dtc_events", "obd_readings", "predictive_alerts", "maintenance_triggers"],
    "driver_behavior":     ["harsh_braking_events", "speeding_events", "idling_log", "driver_scores"],
    "adas_logs":           ["lane_departure_events", "automatic_braking_log", "parking_assist_events"],
    "inventory_feed":      ["vehicle_stock", "aged_inventory", "price_changes", "incentive_programs"],
    "sales_transactions":  ["vehicle_sales", "finance_deals", "trade_in_valuations", "delivery_log"],
    "service_appointments": ["scheduled_services", "completed_services", "technician_log", "parts_used"],
    "crm_leads":           ["conquest_leads", "loyalty_leads", "lead_disposition", "campaign_responses"],
    "claims_history":      ["warranty_claims", "goodwill_claims", "extended_warranty", "claim_payments"],
    "parts_catalog":       ["oem_parts", "supersession_history", "parts_pricing", "obsolete_parts"],
    "labor_codes":         ["flat_rate_labor", "dealer_markup_matrix", "apprentice_adjustments"],
    "supplier_defects":    ["field_quality_reports", "ppap_submissions", "8d_reports", "scrap_returns"],
}

OBJECT_TYPES = {
    "Table": 0.50,
    "View": 0.20,
    "Materialized View": 0.15,
    "Stored Procedure": 0.05,
    "Flat File": 0.10,
}

FORMATS = {
    "Table":             ["Native", "Delta", "Iceberg"],
    "View":              ["Native"],
    "Materialized View": ["Delta", "Iceberg", "Native"],
    "Stored Procedure":  ["Native"],
    "Flat File":         ["Parquet", "CSV", "ORC", "Avro"],
}

REPORT_DEPS = [
    "Executive Finance Dashboard", "Monthly P&L Report", "Regulatory Capital Report",
    "Daily Claims Summary", "Underwriting Scorecard", "Demand Planning Dashboard",
    "Vehicle Sales KPI Report", "Patient Outcome Analytics", "Fraud Detection Alert Feed",
    "Supplier Risk Scoreboard", "Treasury Liquidity Report", "Credit Portfolio Monitor",
]

SERVICE_ACCOUNTS = [
    "svc_etl_prod", "svc_reporting_ro", "svc_ml_pipeline", "svc_audit_extract",
    "svc_dbt_transform", "svc_airflow_orchestrator", "svc_tableau_connector", "svc_powerbi_gateway",
]

USERS = [
    "j.smith@company.com", "a.patel@company.com", "m.chen@company.com", "r.williams@company.com",
    "s.johnson@company.com", "t.garcia@company.com", "l.brown@company.com", "k.davis@company.com",
    "n.wilson@company.com", "p.martinez@company.com", "d.anderson@company.com", "c.taylor@company.com",
    "f.thomas@company.com", "e.jackson@company.com", "b.white@company.com", "g.harris@company.com",
]

ARCHIVAL_JUSTIFICATIONS = {
    "safe": [
        "No active users in the last {days} days. Zero downstream report dependencies confirmed. Service account access was decommissioned on {date}. Safe to archive.",
        "Last accessed {days} days ago by {user} for an ad-hoc query. No recurring scheduled jobs reference this asset. Archival will release {gb:.1f} GB of storage.",
        "This asset was superseded by {alt_table} in {year}. All downstream pipelines have been migrated. Confirmed zero impact on active reports.",
        "Deprecated as part of the {project} consolidation initiative. No active service accounts reference this table. Storage release: {gb:.1f} GB.",
    ],
    "caution": [
        "Last accessed {days} days ago. One report ({report}) references this view, but that report is scheduled quarterly. Recommend steward sign-off before archival.",
        "This asset has {users} users with granted access, though none have queried it in {days} days. Access rights should be reviewed before archival.",
        "A service account ({svc_account}) has historical access but no recent query logs. Verify with the {team} team before proceeding.",
        "Annual batch job may reference this table during {month} reporting cycle. Verify job schedule before archival to avoid disruption.",
    ],
}

# Platform-specific instance names (multi-DB per platform)
PLATFORM_INSTANCES = {
    "Snowflake":                  ["PROD_ACCOUNT", "DEV_ACCOUNT"],
    "Databricks":                 ["PROD_WORKSPACE", "ANALYTICS_WORKSPACE"],
    "BigQuery":                   ["prod-project", "analytics-project"],
    "AWS":                        ["us-east-1-prod", "us-west-2-dr"],
    "Azure":                      ["eastus-prod", "westeurope-dr"],
    "Google Cloud Platform":      ["gcp-prod-env", "gcp-analytics-env"],
    "Oracle Cloud Infrastructure":["oci-prod-region", "oci-dr-region"],
    "IBM Cloud":                  ["ibm-prod-account", "ibm-dev-account"],
}


def _weighted_choice(choices: dict):
    """Choose a key from a dict weighted by its float values."""
    keys = list(choices.keys())
    weights = list(choices.values())
    return random.choices(keys, weights=weights, k=1)[0]


def _random_date(start_days_ago: int, end_days_ago: int = 0) -> datetime:
    delta = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=delta)


def _generate_justification(row: dict) -> str:
    days = row["days_inactive"]
    gb = row["size_gb"]
    user = random.choice(USERS)
    svc = random.choice(SERVICE_ACCOUNTS)
    report = random.choice(REPORT_DEPS)
    year = random.randint(2020, 2023)
    month = random.choice(["March", "June", "September", "December"])
    team = random.choice(["Finance", "Operations", "IT", "Data Engineering"])
    project = random.choice(["Data Lake Modernisation", "Cloud Migration", "Platform Consolidation"])
    alt_table = f"{row['table_name']}_v2"

    if row.get("downstream_deps", 0) == 0 and days > 180:
        template = random.choice(ARCHIVAL_JUSTIFICATIONS["safe"])
    else:
        template = random.choice(ARCHIVAL_JUSTIFICATIONS["caution"])

    return template.format(
        days=days, user=user, gb=gb, date=_random_date(500, 180).strftime("%Y-%m-%d"),
        alt_table=alt_table, year=year, report=report, users=row.get("users_with_access", 5),
        svc_account=svc, team=team, project=project, month=month
    )


def ensure_mock_data():
    os.makedirs("data/raw", exist_ok=True)

    # ── 1. Cloud Usage History ──────────────────────────────────────────────
    usage_path = "data/raw/cloud_usage_history.csv"
    if not os.path.exists(usage_path):
        records = []
        start_date = datetime.now() - timedelta(days=365 * 2)  # 2 years history

        platform_base = {
            "Snowflake":                   (350, 45000, 80, 1600),
            "Databricks":                  (280, 38000, 65, 1200),
            "BigQuery":                    (420, 55000, 95, 1900),
            "AWS":                         (310, 42000, 75, 1400),
            "Azure":                       (290, 40000, 70, 1300),
            "Google Cloud Platform":       (380, 50000, 85, 1750),
            "Oracle Cloud Infrastructure": (240, 30000, 55, 1100),
            "IBM Cloud":                   (220, 28000, 50, 1000),
        }

        for plat, (base_c, base_s, base_t, base_m) in platform_base.items():
            growth_rate = random.uniform(0.15, 0.40)  # 15-40% annual growth
            for d in range(0, 730, 7):
                curr_date = start_date + timedelta(days=d)
                growth = 1.0 + (d / 730.0) * growth_rate
                noise_c = np.random.normal(1.0, 0.05)
                noise_s = np.random.normal(1.0, 0.02)
                noise_t = np.random.normal(1.0, 0.08)
                noise_m = np.random.normal(1.0, 0.04)
                records.append({
                    "usage_date":       curr_date.strftime("%Y-%m-%d"),
                    "platform":         plat,
                    "compute_units":    max(10, base_c * growth * noise_c),
                    "storage_gb":       max(100, base_s * growth * noise_s),
                    "data_transfer_gb": max(5, base_t * growth * noise_t),
                    "memory_usage_gb":  max(50, base_m * growth * noise_m),
                })
        pd.DataFrame(records).to_csv(usage_path, index=False)

    # ── 2. Platform Assets ──────────────────────────────────────────────────
    assets_path = "data/raw/platform_assets.csv"
    if not os.path.exists(assets_path):
        records = []
        now = datetime.now()

        for plat in PLATFORMS:
            for domain in DOMAINS:
                domain_cfg = DOMAIN_DB_SCHEMAS[domain]
                plat_instance = random.choice(PLATFORM_INSTANCES[plat])

                for db_name in domain_cfg["databases"]:
                    schemas = domain_cfg["schemas"].get(db_name, ["default"])
                    for schema_name in schemas:
                        table_pool = TABLE_TEMPLATES.get(schema_name, [f"table_{i}" for i in range(8)])
                        # Add some extras to vary table count
                        extra = [f"{schema_name}_staging", f"{schema_name}_archive_{random.randint(2019,2023)}", f"{schema_name}_backup"]
                        full_pool = table_pool + extra

                        for tbl_name in full_pool:
                            obj_type = _weighted_choice(OBJECT_TYPES)
                            fmt = random.choice(FORMATS[obj_type])
                            is_active = random.choices([True, False], weights=[0.62, 0.38])[0]
                            days_inactive = 0 if is_active else random.randint(45, 730)
                            size_gb = round(abs(np.random.lognormal(mean=2.5, sigma=1.8)), 2)
                            memory_gb = round(size_gb * random.uniform(0.05, 0.25), 2)
                            compute_monthly = round(size_gb * random.uniform(0.8, 3.5), 2)
                            cost_per_month = round((size_gb * 0.023) + (compute_monthly * 3.0) + random.uniform(5, 50), 2)
                            five_year_savings = round(cost_per_month * 12 * 5 * random.uniform(0.6, 0.95), 2) if not is_active else 0.0
                            storage_release = size_gb if not is_active else 0.0
                            memory_release = memory_gb if not is_active else 0.0
                            users_with_access = random.randint(2, 45)
                            active_users = random.randint(0, users_with_access) if is_active else random.randint(0, 3)
                            downstream = random.randint(0, 8)
                            upstream = random.randint(0, 5)
                            num_reports = random.randint(0, 4)
                            reports = random.sample(REPORT_DEPS, min(num_reports, len(REPORT_DEPS)))
                            svc_accounts_used = random.sample(SERVICE_ACCOUNTS, random.randint(0, 3))
                            last_user = random.choice(USERS)
                            last_access = _random_date(days_inactive + 10, days_inactive) if not is_active else _random_date(30, 0)
                            access_granted = _random_date(2000, days_inactive + 30)

                            impact_options = [
                                "Used in Executive Dashboard", "Feeds Daily ML Pipeline",
                                "Regulatory Compliance Report", "No active dependencies identified",
                                "Ad-hoc Analytics Query", "Deprecated API Source",
                                "Superseded by newer model", "Quarterly Batch Reference"
                            ]
                            impact_reason = random.choice(impact_options)

                            row = {
                                "platform":             plat,
                                "platform_instance":    plat_instance,
                                "domain":               domain,
                                "database":             db_name,
                                "schema":               schema_name,
                                "table_name":           tbl_name,
                                "object_type":          obj_type,
                                "format":               fmt,
                                "size_gb":              size_gb,
                                "memory_usage_gb":      memory_gb,
                                "compute_monthly":      compute_monthly,
                                "cost_per_month":       cost_per_month,
                                "is_active":            is_active,
                                "days_inactive":        days_inactive,
                                "five_year_savings":    five_year_savings,
                                "storage_release_gb":   storage_release,
                                "memory_release_gb":    memory_release,
                                "users_with_access":    users_with_access,
                                "active_users":         active_users,
                                "last_accessed_by":     last_user,
                                "last_access_date":     last_access.strftime("%Y-%m-%d"),
                                "access_granted_date":  access_granted.strftime("%Y-%m-%d"),
                                "service_accounts":     ", ".join(svc_accounts_used) if svc_accounts_used else "None",
                                "upstream_deps":        upstream,
                                "downstream_deps":      downstream,
                                "report_dependencies":  "; ".join(reports) if reports else "None",
                                "impact_reason":        impact_reason,
                            }
                            row["archival_justification"] = _generate_justification(row) if not is_active else "Asset is active — not a candidate for archival."
                            records.append(row)

        pd.DataFrame(records).to_csv(assets_path, index=False)
        print(f"[mock_data] Generated {len(records):,} platform asset records.")


if __name__ == "__main__":
    ensure_mock_data()
