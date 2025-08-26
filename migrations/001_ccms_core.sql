-- 001_ccms_core.sql
-- CCMS Native LangChain Pipeline Database Schema
-- Supports multi-tenant, config-driven casino review generation

-- Tenants
CREATE TABLE IF NOT EXISTS public.tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text UNIQUE NOT NULL,
  name text NOT NULL,
  brand_voice jsonb NOT NULL DEFAULT '{}'::jsonb,
  locales text[] NOT NULL DEFAULT array[]::text[],
  feature_flags jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Defaults & overrides
CREATE TABLE IF NOT EXISTS public.global_defaults (
  chain text PRIMARY KEY,                 -- research|content|seo|media|compliance|publish
  config jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.tenant_defaults (
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  chain text NOT NULL,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (tenant_id, chain)
);

CREATE TABLE IF NOT EXISTS public.tenant_overrides (
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  casino_slug text NOT NULL,
  chain text NOT NULL,
  config jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (tenant_id, casino_slug, chain)
);

-- Research & clustering
CREATE TABLE IF NOT EXISTS public.research_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  casino_slug text NOT NULL,
  locale text NOT NULL,
  facts jsonb NOT NULL DEFAULT '{}'::jsonb,       -- normalized fields (license, bonus, payments…)
  sources jsonb NOT NULL DEFAULT '[]'::jsonb,     -- [{url, date, note}]
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_research_casino_locale ON public.research_articles(casino_slug, locale);

CREATE TABLE IF NOT EXISTS public.topic_clusters (
  cluster_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  casino_slug text NOT NULL,
  primary_kw text NOT NULL,
  secondary_kws text[] NOT NULL DEFAULT array[]::text[],
  serp_intent jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_topic_clusters_casino ON public.topic_clusters(casino_slug);

-- SEO rules, secondary keywords, authority links
CREATE TABLE IF NOT EXISTS public.tenant_seo_rules (
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  locale text NOT NULL,
  rules jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (tenant_id, locale)
);

CREATE TABLE IF NOT EXISTS public.secondary_keywords (
  casino_slug text NOT NULL,
  locale text NOT NULL,
  keywords text[] NOT NULL DEFAULT array[]::text[],
  PRIMARY KEY (casino_slug, locale)
);

CREATE TABLE IF NOT EXISTS public.authority_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  bucket text NOT NULL,                     -- rg | license | payments | etc.
  links jsonb NOT NULL DEFAULT '[]'::jsonb  -- [{label,url,rel}]
);
CREATE INDEX IF NOT EXISTS idx_authority_links_tenant_bucket ON public.authority_links(tenant_id, bucket);

-- Compliance & legal
CREATE TABLE IF NOT EXISTS public.legal_boilerplates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  region text NOT NULL,      -- UK | EU | ROW ...
  locale text NOT NULL,
  blocks jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_legal_boilerplates_region_locale ON public.legal_boilerplates(region, locale);

CREATE TABLE IF NOT EXISTS public.compliance_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  locale text NOT NULL,
  rules jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_locale ON public.compliance_rules(locale);

CREATE TABLE IF NOT EXISTS public.content_quality_scores (
  run_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  casino_slug text NOT NULL,
  scores jsonb NOT NULL DEFAULT '{}'::jsonb,
  blocking_issues jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cqs_tenant_casino ON public.content_quality_scores(tenant_id, casino_slug);

-- Affiliate / monetization
CREATE TABLE IF NOT EXISTS public.affiliate_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  casino_slug text NOT NULL,
  cta_label text NOT NULL,
  tracking_url text NOT NULL,
  nofollow boolean NOT NULL DEFAULT true,
  sponsored boolean NOT NULL DEFAULT true,
  compliance_notes text
);
CREATE UNIQUE INDEX IF NOT EXISTS uidx_affiliate_links ON public.affiliate_links(tenant_id, casino_slug);

CREATE TABLE IF NOT EXISTS public.comparison_specs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  "group" text NOT NULL,                    -- payments | bonus_terms | withdrawal_times
  columns jsonb NOT NULL DEFAULT '[]'::jsonb, -- ordered definitions
  rows jsonb NOT NULL DEFAULT '[]'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_comparison_specs_group ON public.comparison_specs("group");

-- Schema / structured data
CREATE TABLE IF NOT EXISTS public.schema_templates (
  type text PRIMARY KEY,                    -- Review | FAQPage | Breadcrumb | ItemList
  template jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.faq_suggestions (
  casino_slug text NOT NULL,
  locale text NOT NULL,
  faqs jsonb NOT NULL DEFAULT '[]'::jsonb,  -- [{q,a}]
  PRIMARY KEY (casino_slug, locale)
);

-- Media
CREATE TABLE IF NOT EXISTS public.media_presets (
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  locale text NOT NULL,
  presets jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (tenant_id, locale)
);

CREATE TABLE IF NOT EXISTS public.cdn_assets (
  run_id uuid NOT NULL,
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  files jsonb NOT NULL DEFAULT '[]'::jsonb,  -- [{name,path,width,height,hash}]
  PRIMARY KEY (run_id, tenant_id)
);

-- Observability & freshness
CREATE TABLE IF NOT EXISTS public.page_metrics (
  run_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
  casino_slug text NOT NULL,
  events jsonb NOT NULL DEFAULT '[]'::jsonb,     -- timings, retries, http codes
  serp_signals jsonb,                            -- optional CTR/pos/dwell
  published_url text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.freshness_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity text NOT NULL,                           -- bonus | rtp | payments
  check_interval_days int NOT NULL DEFAULT 14,
  selectors jsonb NOT NULL DEFAULT '{}'::jsonb,
  action text NOT NULL DEFAULT 'flag_review'      -- auto_update | flag_review
);

-- Insert initial data for CrashCasino tenant
INSERT INTO public.tenants (slug, name, brand_voice, locales, feature_flags) VALUES 
('crashcasino', 'CrashCasino.io', 
 '{"tone": "crypto-savvy, punchy", "style": "direct, no-nonsense", "disclaimers": "prominent"}',
 ARRAY['en-GB', 'en-US'],
 '{"use_faq_schema": true, "use_itemlist": true, "geo_proxy": true}'
) ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  brand_voice = EXCLUDED.brand_voice,
  locales = EXCLUDED.locales,
  feature_flags = EXCLUDED.feature_flags,
  updated_at = now();

-- Global defaults for all chains
INSERT INTO public.global_defaults (chain, config) VALUES 
('compliance', '{
  "retries": {"attempts": 3, "backoff": "exponential", "base_ms": 400},
  "fail_fast": true,
  "required_checks": ["license", "wagering", "age_disclaimer", "rg_links"]
}'),
('media', '{
  "screenshot": {"viewport": "1440x900", "wait_for": [".bonus-banner"], "timeout": 30000},
  "resize": {"variants": [{"w": 1280}, {"w": 800}, {"w": 400}]},
  "retries": {"attempts": 3, "backoff": "exponential", "base_ms": 500}
}'),
('seo', '{
  "title_max_length": 60,
  "meta_description_max_length": 158,
  "inject_secondary_keywords": true,
  "schema_types": ["Review", "FAQPage"]
}'),
('content', '{
  "target_word_count": 2500,
  "include_comparison_tables": true,
  "include_pros_cons": true
}'),
('research', '{
  "max_sources": 10,
  "fact_verification_threshold": 0.8
}'),
('publish', '{
  "default_status": "draft",
  "retries": {"attempts": 5, "backoff": "exponential", "base_ms": 1000}
}')
ON CONFLICT (chain) DO UPDATE SET config = EXCLUDED.config;

-- Schema templates for structured data
INSERT INTO public.schema_templates (type, template) VALUES 
('Review', '{
  "@context": "https://schema.org",
  "@type": "Review",
  "itemReviewed": {
    "@type": "Organization",
    "name": "{casino_name}"
  },
  "reviewBody": "{review_summary}",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "{rating}",
    "bestRating": "10"
  },
  "author": {
    "@type": "Person",
    "name": "{author_name}"
  },
  "datePublished": "{publish_date}",
  "publisher": {
    "@type": "Organization",
    "name": "{tenant_name}"
  }
}'),
('FAQPage', '{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": "{faq_list}"
}')
ON CONFLICT (type) DO UPDATE SET template = EXCLUDED.template;

-- Compliance rules for different locales
INSERT INTO public.compliance_rules (locale, rules) VALUES 
('en-GB', '{
  "required_age_disclaimer": "18+ Only. Gamble responsibly.",
  "rg_links": [
    {"label": "BeGambleAware", "url": "https://www.begambleaware.org"},
    {"label": "GamCare", "url": "https://www.gamcare.org.uk"}
  ],
  "license_requirements": {
    "Curacao": {
      "must_include_text": [
        "Licensed by Curaçao eGaming",
        "Curaçao license may not offer the same protections as UKGC/MGA"
      ],
      "prohibited_phrases": ["UK regulated", "EU equivalent licensing"]
    },
    "MGA": {
      "must_include_text": ["Licensed by Malta Gaming Authority (MGA)"],
      "prohibited_phrases": []
    }
  },
  "bonus_requirements": ["wagering", "min_deposit", "max_bet", "expiry", "game_weighting"],
  "prohibited_claims": [
    "guaranteed winnings",
    "risk-free gambling", 
    "sure bet",
    "100% safe"
  ]
}')
ON CONFLICT (locale) DO UPDATE SET rules = EXCLUDED.rules;