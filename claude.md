{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fnil\fcharset0 .SFNS-Semibold;\f1\fnil\fcharset0 .SFNS-Regular;\f2\fnil\fcharset0 HelveticaNeue-Bold;
\f3\fswiss\fcharset0 Helvetica;\f4\fnil\fcharset0 .AppleSystemUIFontMonospaced-Regular;\f5\froman\fcharset0 TimesNewRomanPSMT;
\f6\fmodern\fcharset0 Courier;\f7\fmodern\fcharset0 Courier-Oblique;\f8\fnil\fcharset0 .SFNS-RegularItalic;
}
{\colortbl;\red255\green255\blue255;\red14\green14\blue14;\red155\green162\blue177;\red197\green136\blue83;
\red136\green185\blue102;\red74\green80\blue93;}
{\*\expandedcolortbl;;\cssrgb\c6700\c6700\c6700;\cssrgb\c67059\c69804\c74902;\cssrgb\c81961\c60392\c40000;
\cssrgb\c59608\c76471\c47451;\cssrgb\c36078\c38824\c43922;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs44 \cf2 Claude Code Guardrails \'97 Universal RAG CMS (LangChain\uc0\u8209 Native)
\f1\b0\fs28 \cf2 \
\
\pard\tx860\tx1420\tx1980\tx2540\tx3100\tx3660\tx4220\tx4780\tx5340\tx5900\tx6460\tx7020\li300\sl324\slmult1\partightenfactor0

\f2\b \cf2 Scope
\f1\b0 : This file governs how Claude Code works in this repository: allowed tools, workflows, prompts, and development rules for our 
\f2\b LangChain\uc0\u8209 native
\f1\b0  multi\uc0\u8209 tenant casino CMS (Supabase + WordPress + DataForSEO + Firecrawl + n8n).\

\f2\b Applies automatically
\f1\b0  when you run Claude here or in child folders.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 0) Core Principles
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 LangChain\uc0\u8209 Native Only
\f1\b0 \cf2 : LCEL + (when needed) LangGraph. No ad\uc0\u8209 hoc HTTP inside chains; all I/O via 
\f4 /src/tools/*
\f1  adapters.\
	\'95	
\f2\b \cf2 Deterministic Contracts
\f1\b0 \cf2 : Every chain/agent returns a 
\f2\b \cf2 Pydantic v2
\f1\b0 \cf2  model; malformed output must auto\uc0\u8209 repair or fail fast.\
	\'95	
\f2\b \cf2 Agent\uc0\u8209 First, Bounded
\f1\b0 \cf2 : Agents are narrow, tool\uc0\u8209 aware, with LangGraph checkpointing.\
	\'95	
\f2\b \cf2 Multitenant by Design
\f1\b0 \cf2 : All runs parameterized by 
\f4 tenant_id
\f1  (voice, locale, compliance, storage).\
	\'95	
\f2\b \cf2 Auditability
\f1\b0 \cf2 : Traced in LangSmith; prompts, datasets, evals, regressions are versioned.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 1) Golden Rules (keep these short & enforceable)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx440\tx600\li600\fi-600\sl324\slmult1\sb240\partightenfactor0

\f5 \cf2 	1.	
\f2\b LCEL everywhere
\f1\b0  (
\f4 \cf2 |
\f1 \cf2  composition with 
\f4 \cf2 Runnable*
\f1 \cf2 , 
\f4 \cf2 ChatPromptTemplate
\f1 \cf2 , 
\f4 \cf2 RouterRunnable
\f1 \cf2 ).\

\f5 	2.	
\f2\b No custom orchestration
\f1\b0  in chains (no raw 
\f4 \cf2 asyncio.gather
\f1 \cf2 , no raw HTTP). External services only via 
\f4 \cf2 /src/tools/*
\f1 \cf2 .\

\f5 	3.	
\f2\b Schema\uc0\u8209 First
\f1\b0 : Inputs/outputs live in 
\f4 \cf2 /src/schemas
\f1 \cf2 . Changes require migration notes + tests.\

\f5 	4.	
\f2\b Prompt Hygiene
\f1\b0 : Prompts live in 
\f4 \cf2 /src/prompts/*
\f1 \cf2 ; load by path. No long inline prompts.\

\f5 	5.	
\f2\b Retrieval
\f1\b0 : Use 
\f4 \cf2 VectorStoreRetriever + MultiQueryRetriever (+ optional Reranker)
\f1 \cf2 . See 
\f4 \cf2 docs/retrieval-playbook.md
\f1 \cf2 .\

\f5 	6.	
\f2\b Adapters Only
\f1\b0 : WordPress, Supabase, DataForSEO, Firecrawl, Browserless/CF Browser Rendering \uc0\u8594  
\f4 \cf2 /src/tools/*
\f1 \cf2 .\

\f5 	7.	
\f2\b Tests required
\f1\b0  for every chain/agent (
\f4 \cf2 /tests
\f1 \cf2  + 
\f4 \cf2 /src/evals
\f1 \cf2 ). PRs without tests are rejected.\

\f5 	8.	
\f2\b Structured logs
\f1\b0 : stage + timings; no PII. Log keys: 
\f4 \cf2 tenant_id
\f1 \cf2 , 
\f4 \cf2 chain
\f1 \cf2 , 
\f4 \cf2 node
\f1 \cf2 , 
\f4 \cf2 duration_ms
\f1 \cf2 .\

\f5 	9.	
\f2\b Compliance Blocking
\f1\b0 : Publishing is gated by a QA/Compliance chain; no bypass in prod.\

\f5 	10.	
\f2\b Cost & Rate Limits
\f1\b0 : Batch embeddings/gens; retries w/ exponential backoff; respect quotas.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 2) Claude Code Setup & Locations
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 This file (CLAUDE.md)
\f1\b0 \cf2  is auto\uc0\u8209 loaded when you run Claude here.\
	\'95	You can also use:\
\pard\tqr\tx500\tx660\li660\fi-660\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Parent CLAUDE.md
\f1\b0 \cf2  (monorepo support)\
	\'95	
\f2\b \cf2 Child CLAUDE.md
\f1\b0 \cf2  (auto\uc0\u8209 pulled when you work in that directory)\
	\'95	
\f2\b \cf2 Global
\f1\b0 \cf2 : 
\f4 ~/.claude/CLAUDE.md
\f1  (applies to all sessions)\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Tip:
\f1\b0  Use 
\f4 \cf2 #
\f1 \cf2  inside Claude to append small instructions here as you work (commit those changes).\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 3) Tool Allowlist & Permissions
\f1\b0\fs28 \cf2 \
\
Claude is conservative by default. We explicitly allow the tools below.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 3.1 Session controls
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Use 
\f4 /permissions
\f1  in a session to 
\f2\b \cf2 Always allow
\f1\b0 \cf2 :\
\pard\tqr\tx500\tx660\li660\fi-660\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 Edit
\f1  (file writes)\
	\'95	
\f4 Bash(git *)
\f1  (git operations)\
	\'95	
\f4 Bash(pytest|ruff|mypy|npm|poetry|uv|make)
\f1  (safe dev commands)\
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	For one\uc0\u8209 off sessions, use 
\f4 --allowedTools
\f1  flags.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 3.2 Repo settings file (checked\uc0\u8209 in)
\f1\b0\fs28 \cf2 \
\
Create 
\f4 \cf2 .claude/settings.json
\f1 \cf2 :
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 \{\
  \cf4 "alwaysAllow"\cf3 : [\
    \cf5 "Edit"\cf3 ,\
    \cf5 "Bash(git *)"\cf3 ,\
    \cf5 "Bash(pytest *)"\cf3 ,\
    \cf5 "Bash(ruff *)"\cf3 ,\
    \cf5 "Bash(mypy *)"\cf3 ,\
    \cf5 "Bash(npm *)"\cf3 ,\
    \cf5 "Bash(poetry *)"\cf3 ,\
    \cf5 "Bash(uv *)"\cf3 ,\
    \cf5 "Bash(make *)"\cf3 \
  ],\
  \cf4 "deny"\cf3 : [\
    \cf5 "Bash(rm -rf /*)"\cf3 , \
    \cf5 "Bash(curl * | sh)"\cf3 \
  ]\
\}
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 3.3 GitHub CLI
\f1\b0\fs28 \cf2 \
\
Install 
\f2\b gh
\f1\b0  so Claude can create PRs, read issues, etc.\
If missing, Claude may fall back to API/MCP, but 
\f4 \cf2 gh
\f1 \cf2  is preferred.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 4) MCP & External Tools (shared config)
\f1\b0\fs28 \cf2 \
\
We centralize tool access via MCP and 
\f4 \cf2 /src/tools/*
\f1 \cf2  to stay 
\f2\b native
\f1\b0  and auditable.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 4.1 .mcp.json (checked\uc0\u8209 in)
\f1\b0\fs28 \cf2 \
\
Add MCP servers that everyone should have:
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 \{\
  \cf4 "clients"\cf3 : \{\
    \cf4 "puppeteer"\cf3 : \{\
      \cf4 "command"\cf3 : \cf5 "node"\cf3 ,\
      \cf4 "args"\cf3 : [\cf5 "mcp/puppeteer-server.js"\cf3 ],\
      \cf4 "env"\cf3 : \{\}\
    \},\
    \cf4 "sentry"\cf3 : \{\
      \cf4 "command"\cf3 : \cf5 "mcp-sentry"\cf3 ,\
      \cf4 "args"\cf3 : [],\
      \cf4 "env"\cf3 : \{\}\
    \}\
  \}\
\}
\f3\fs24 \cf0 \
\
\pard\tx860\tx1420\tx1980\tx2540\tx3100\tx3660\tx4220\tx4780\tx5340\tx5900\tx6460\tx7020\li300\sl324\slmult1\partightenfactor0

\f1\fs28 \cf2 Use 
\f4 --mcp-debug
\f1  when diagnosing MCP configuration.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 4.2 Repo adapters (used by chains)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 /src/tools/supabase_storage.py
\f1 \
	\'95	
\f4 /src/tools/wordpress.py
\f1 \
	\'95	
\f4 /src/tools/dataforseo.py
\f1  (discovery only for images)\
	\'95	
\f4 /src/tools/firecrawl.py
\f1  (scrape + screenshots)\
	\'95	
\f4 /src/tools/cf_browser.py
\f1  (Cloudflare Browser Rendering 
\f4 /screenshot
\f1 )\
	\'95	
\f4 /src/tools/browserless.py
\f1  (hosted Playwright/Chrome 
\f4 /screenshot
\f1 )\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Rule
\f1\b0 : Chains call these via 
\f4 \cf2 RunnableLambda
\f1 \cf2 /ToolNode only.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 5) Slash Commands (repeatable prompts)
\f1\b0\fs28 \cf2 \
\
Place markdown files in 
\f4 \cf2 .claude/commands/
\f1 \cf2  and they\'92ll appear under 
\f4 \cf2 /
\f1 \cf2 .\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Examples:
\f1\b0 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 .claude/commands/fix-github-issue.md
\f1 \
	\'95	
\f4 .claude/commands/generate-casino-review.md
\f1 \
	\'95	
\f4 .claude/commands/run-evals.md
\f1 \
\
You can use 
\f4 $ARGUMENTS
\f1  to pass params.
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 Please analyze and fix GitHub issue: $ARGUMENTS\
\
Steps:\
1) gh issue view $ARGUMENTS\
2) Identify code paths\
3) Write failing tests\
4) Implement fix\
5) Run tests & linters\
6) Commit + push + open PR
\f3\fs24 \cf0 \
\
\
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 6) Opinionated Workflows (what we expect Claude to do)
\f1\b0\fs28 \cf2 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 6.1 Explore \uc0\u8594  Plan \u8594  Code \u8594  Commit
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Explore
\f1\b0 \cf2 : \'93read\'94 relevant files; don\'92t write yet.\
	\'95	
\f2\b \cf2 Plan
\f1\b0 \cf2 : produce a short plan document (and commit it if helpful).\
	\'95	
\f2\b \cf2 Code
\f1\b0 \cf2 : implement with LCEL/LangGraph primitives only.\
	\'95	
\f2\b \cf2 Commit/PR
\f1\b0 \cf2 : include plan summary + test notes.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 6.2 TDD Loop
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Write tests first (no mocks of new behavior).\
	\'95	Confirm tests fail.\
	\'95	Implement to pass; iterate.\
	\'95	Commit tests and code separately.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 6.3 Write \uc0\u8594  Screenshot \u8594  Iterate
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Provide a visual target or mock.\
	\'95	Use 
\f2\b \cf2 Firecrawl/CF Browser/Browserless
\f1\b0 \cf2  to capture screenshots.\
	\'95	Iterate until match; then commit.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 6.4 Safe YOLO (dangerous)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 claude --dangerously-skip-permissions
\f1  
\f2\b \cf2 only inside
\f1\b0 \cf2  a throwaway container (no internet).\
	\'95	Allowed tasks: fix lint errors, boilerplate generation.\
	\'95	Not for production repos.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs30 \cf2 6.5 Codebase Q&A / Git Ops
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Encourage Claude to 
\f2\b \cf2 search git history
\f1\b0 \cf2 , write 
\f2\b \cf2 commit messages
\f1\b0 \cf2 , and handle 
\f2\b \cf2 rebases/conflicts
\f1\b0 \cf2 .\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 7) Headless Mode (CI & automation)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 claude -p "<prompt>" --output-format stream-json
\f1  for non\uc0\u8209 interactive workflows.\
	\'95	Use in:\
\pard\tqr\tx500\tx660\li660\fi-660\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Issue triage
\f1\b0 \cf2  (labeling)\
	\'95	
\f2\b \cf2 Subjective linting
\f1\b0 \cf2  (naming, comments)\
	\'95	
\f2\b \cf2 Pre\uc0\u8209 commit hooks
\f1\b0 \cf2  (docstring/style hints)\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Example
\f1\b0  (triage):
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 claude -p \cf5 "Label new issue: \cf4 $ISSUE_BODY\cf5 "\cf3  --allowedTools \cf5 "Bash(gh issue *)"
\f3\fs24 \cf0 \
\
\
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 8) Multi\uc0\u8209 Claude Patterns
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Dual Claude
\f1\b0 \cf2 : One writes code, another reviews/tests.\
	\'95	
\f2\b \cf2 Worktrees
\f1\b0 \cf2 : Use 
\f4 git worktree
\f1  for parallel tasks in separate folders.\
	\'95	
\f2\b \cf2 Headless harness
\f1\b0 \cf2 : Fan\uc0\u8209 out (migrations) or pipeline mode (JSON to next step).\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 9) Retrieval Playbook (short)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Default
\f1\b0 \cf2 : Supabase pgvector (dense) + BM25 \uc0\u8594  
\f4 EnsembleRetriever
\f1 .\
	\'95	
\f2\b \cf2 Expansion
\f1\b0 \cf2 : 
\f4 MultiQueryRetriever
\f1  (3\'965 rewrites).\
	\'95	
\f2\b \cf2 Metadata
\f1\b0 \cf2 : 
\f4 SelfQueryRetriever
\f1  for field\uc0\u8209 scoped lookups (licenses, RTP, payments).\
	\'95	
\f2\b \cf2 Rerank
\f1\b0 \cf2 : Add cross\uc0\u8209 encoder as a Runnable when needed.\
	\'95	
\f2\b \cf2 Chunking
\f1\b0 \cf2 : 
\f4 RecursiveCharacterTextSplitter
\f1  tuned per doc type (T&Cs vs reviews).\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 10) Imagery & Screenshot Policy (publishable outputs)
\f1\b0\fs28 \cf2 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Priority order
\f1\b0 \
\pard\tqr\tx260\tx420\li420\fi-420\sl324\slmult1\sb240\partightenfactor0

\f5 \cf2 	1.	
\f2\b First\uc0\u8209 party captures
\f1\b0 : Firecrawl (
\f4 \cf2 screenshot:true
\f1 \cf2 ) \uc0\u8594  CF Browser 
\f4 \cf2 /screenshot
\f1 \cf2  \uc0\u8594  Browserless \u8594  Playwright (login/selector flows).\

\f5 	2.	
\f2\b Official assets
\f1\b0 : Brand press kits with permission.\

\f5 	3.	
\f2\b DataForSEO
\f1\b0 : 
\f2\b Discovery only
\f1\b0  (SERP/Image URLs). 
\f2\b Never publish
\f1\b0  without rights.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Compliance guard (blocking)
\f1\b0 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Missing license/source; wrong brand; watermark; dims < 900\'d7600; 
\f4 method == dataforseo
\f1  for publish.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Supabase Storage
\f1\b0 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Path: 
\f4 images/\{tenant\}/\{brand\}/\{category\}/\{ISO8601\}.png
\f1 \
	\'95	Metadata JSON: 
\f4 source_url
\f1 , 
\f4 capture_ts
\f1 , 
\f4 method
\f1 , 
\f4 viewport
\f1 , 
\f4 jurisdiction
\f1 , 
\f4 license
\f1 , 
\f4 hash
\f1 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Screenshot Chain (LCEL)
\f3\b0\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 screenshot_chain = (\
  RunnablePassthrough()\
  | RunnableLambda(select_tool)  
\f7\i \cf6 # firecrawl | cf_browser | browserless | playwright | dataforseo
\f6\i0 \cf3 \
  | RouterRunnable(\{...\})\
  | RunnableLambda(image_compliance_guard)  
\f7\i \cf6 # must PASS for publishable
\f6\i0 \cf3 \
  | RunnableLambda(supabase_upload_image)\
)
\f3\fs24 \cf0 \
\
\
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 11) CI/CD & PR Template
\f1\b0\fs28 \cf2 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 CI runs on every PR
\f1\b0 :\
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 pytest
\f1  (unit + golden evals)\
	\'95	
\f4 mypy
\f1 , 
\f4 ruff
\f1 , 
\f4 black --check
\f1 \
	\'95	
\f2\b \cf2 Schema diff
\f1\b0 \cf2  for 
\f4 /src/schemas
\f1 \
	\'95	
\f2\b \cf2 LangSmith eval
\f1\b0 \cf2  gate (no regressions beyond threshold)\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 PR template
\f1\b0  
\f4 \cf2 .github/pull_request_template.md
\f1 \cf2 :
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 ### What changed?\
- [ ] Chain/agent touched\
- [ ] Schemas updated (with migration notes)\
- [ ] Prompts version bumped\
\
### Tests\
- [ ] Unit tests added\
- [ ] Golden eval updated\
- [ ] LangSmith eval link (no regression)\
\
### Compliance\
- [ ] Imagery guard PASS\
- [ ] Jurisdiction config reviewed
\f3\fs24 \cf0 \
\
\
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 12) Performance & Cost Guardrails
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Batch embeddings/generation; use LCEL 
\f4 .batch()
\f1  where safe.\
	\'95	Enable caching (in\uc0\u8209 memory/Redis via LCEL config).\
	\'95	Rate\uc0\u8209 limit + backoff with jitter; centralized in 
\f4 /src/tools/_rate.py
\f1 .\
	\'95	Per\uc0\u8209 tenant budgets for tokens & concurrency.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 13) Security & Secrets
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Secrets via env
\f1\b0 \cf2  only (
\f4 .env
\f1 , CI secrets).\
	\'95	Never log tokens, emails, IPs, DOBs.\
	\'95	
\f2\b \cf2 GDPR
\f1\b0 \cf2 : Right\uc0\u8209 to\u8209 erasure (delete vectors + blobs by 
\f4 subject_id
\f1 ).\
	\'95	
\f2\b \cf2 Provenance
\f1\b0 \cf2 : Store 
\f4 source_url
\f1 , timestamps, capture method for every artifact.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f4 \cf2 .env.example
\f1 \cf2  (excerpt)
\f3\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f6\fs28 \cf3 SUPABASE_URL=\
SUPABASE_SERVICE_ROLE=\
WORDPRESS_BASE_URL=\
WORDPRESS_APP_PW=\
FIRECRAWL_API_KEY=\
BROWSERLESS_TOKEN=\
CF_BROWSER_TOKEN=\
DATAFORSEO_LOGIN=\
DATAFORSEO_PASSWORD=\
USER_AGENT=\cf5 "Mozilla/5.0 ..."\cf3 \
TENANT_DEFAULT=crashcasino
\f3\fs24 \cf0 \
\
\
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 14) Agents & Chains (I/O contracts)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f2\b \cf2 Research Agent
\f1\b0 \cf2  \uc0\u8594  
\f4 ResearchPack
\f1  (licenses, payments, providers; sources attached)\
	\'95	
\f2\b \cf2 Review Agent
\f1\b0 \cf2  \uc0\u8594  
\f4 ReviewDoc
\f1  (\uc0\u8805  2,500 words; cites sources; image slots)\
	\'95	
\f2\b \cf2 SEO Agent
\f1\b0 \cf2  \uc0\u8594  
\f4 SEOPlan
\f1  (title/meta/schema/internal links)\
	\'95	
\f2\b \cf2 QA Agent
\f1\b0 \cf2  \uc0\u8594  
\f4 QAReport(pass|fail, reasons[])
\f1  (factuals/compliance/95\uc0\u8209 field completeness)\
	\'95	
\f2\b \cf2 Publishing Agent
\f1\b0 \cf2  \uc0\u8594  
\f4 PublishResult
\f1  (WP post id/URL, media IDs)\
\
All are 
\f2\b \cf2 LangGraph nodes
\f1\b0 \cf2  with checkpoints.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 15) Definition of Done (DoD)
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	\uc0\u9989  LCEL or LangGraph chain with typed I/O\
	\'95	\uc0\u9989  Unit tests + golden eval updated & passing\
	\'95	\uc0\u9989  No schema breaks (or documented migration)\
	\'95	\uc0\u9989  Prompts versioned in 
\f4 /src/prompts
\f1 \
	\'95	\uc0\u9989  LangSmith traces visible; eval \u8805  thresholds\
	\'95	\uc0\u9989  
\f2\b \cf2 Compliance guard PASS
\f1\b0 \cf2  (images, T&Cs, jurisdiction)\
	\'95	\uc0\u9989  Docs updated (
\f4 ARCHITECTURE.md
\f1  and, if relevant, 
\f4 docs/retrieval-playbook.md
\f1 )\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 16) Course\uc0\u8209 Correction & Hygiene
\f1\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Ask for a 
\f2\b \cf2 plan first
\f1\b0 \cf2 , then code.\
	\'95	Use 
\f2\b \cf2 Escape
\f1\b0 \cf2  to interrupt & redirect; 
\f2\b \cf2 /clear
\f1\b0 \cf2  between tasks to keep context tight.\
	\'95	Keep a 
\f2\b \cf2 scratchpad checklist
\f1\b0 \cf2  (Markdown/Issue) for big refactors/migrations.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f3\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f0\b\fs34 \cf2 17) Quick Commands (team memory)
\f1\b0\fs28 \cf2 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Bash
\f1\b0 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 npm run build
\f1  \'97 build frontends\
	\'95	
\f4 python -m pytest -q
\f1  \'97 tests\
	\'95	
\f4 ruff check . && mypy .
\f1  \'97 linters/types\
	\'95	
\f4 gh pr create -f
\f1  \'97 open PR\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\b \cf2 Nudges to Claude
\f1\b0 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f8\i \cf2 \'93think hard\'94
\f1\i0 \cf2  \uc0\u8594  deeper planning\
	\'95	
\f8\i \cf2 \'93don\'92t code yet; write tests first\'94
\f1\i0 \cf2  \uc0\u8594  TDD\
	\'95	
\f8\i \cf2 \'93read X, produce a plan, then stop\'94
\f1\i0 \cf2  \uc0\u8594  prevents premature edits\
}