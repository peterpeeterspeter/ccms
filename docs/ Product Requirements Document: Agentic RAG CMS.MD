{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fnil\fcharset0 .SFNS-Semibold;\f2\fnil\fcharset0 .SFNS-Regular;
\f3\fnil\fcharset0 HelveticaNeue-Bold;\f4\fnil\fcharset0 .AppleSystemUIFontMonospaced-Regular;\f5\froman\fcharset0 TimesNewRomanPSMT;
\f6\fnil\fcharset0 .SFNS-Bold;}
{\colortbl;\red255\green255\blue255;\red14\green14\blue14;}
{\*\expandedcolortbl;;\cssrgb\c6700\c6700\c6700;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs34 \cf2 Product Requirements Document: Agentic RAG CMS (Affiliate Website Network)
\f2\b0\fs28 \cf2 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 1. Overview & Purpose
\f2\b0\fs28 \cf2 \
\
Build a modular, agentic RAG-powered CMS optimized for 
\f3\b affiliate content sites
\f2\b0  (e.g., casino reviews). It must:\
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Research, archive, and vectorize affiliate fields (95\uc0\u8209 point intel) into Supabase.\
	\'95	Retrieve and blend textual + visual content (screenshots, images).\
	\'95	Support 
\f3\b \cf2 multi-tenant branding
\f2\b0 \cf2  and voice per site.\
	\'95	Generate 
\f3\b \cf2 world-class, narrative-style content
\f2\b0 \cf2 \'97reviews, articles, updates\'97kept fresh.\
	\'95	Handle 
\f3\b \cf2 affiliate compliance
\f2\b0 \cf2  workflows and guardrails.\
	\'95	Use native components only: 
\f3\b \cf2 LangChain
\f2\b0 \cf2 , 
\f3\b \cf2 LangGraph
\f2\b0 \cf2 , 
\f3\b \cf2 LangSmith
\f2\b0 \cf2 . No custom orchestration or HTTP hacking.\
	\'95	Publish to WordPress via native tool adapter.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 2. Key Components & Architecture
\f2\b0\fs28 \cf2 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 A. Research & Ingestion Agent
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	A LangGraph workflow node (Planner \uc0\u8594  Retrieve \u8594  Loader):\
\pard\tqr\tx500\tx660\li660\fi-660\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Use LCEL chains to load web content (
\f4 WebBaseLoader
\f2 ), chunk (RecursiveCharacterTextSplitter), and index into Supabase vector store.\
	\'95	Store structured metadata for affiliate compliance.\
	\'95	Retriever supports 
\f3\b \cf2 MultiQueryRetriever
\f2\b0 \cf2  for enhanced recall.     \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 B. Multi-Tenant Config
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	All operations parameterized by 
\f4 tenant_id
\f2 , 
\f4 voice
\f2 , 
\f4 locale
\f2 .\
	\'95	Metadata filtering in retrievers (e.g., 
\f4 \{"tenant_id":"siteA","lang":"nl"\}
\f2 ).\
	\'95	LangGraph state holds tenant context; chain nodes pick prompts and brand assets accordingly.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 C. Visual Content Integration
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	LangGraph node picks visual capture via 
\f4 /src/tools/firecrawl
\f2 , 
\f4 /cf_browser
\f2 , or 
\f4 /browserless
\f2 .\
	\'95	Enforce compliance (license presence, watermark rules, size thresholds) via a RunnableLambda in LCEL.   \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 D. Content Generation Agent
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Use LCEL chain with:\
\pard\tqr\tx500\tx660\li660\fi-660\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f4 \{context\}
\f2 , 
\f4 \{visuals\}
\f2 , 
\f4 \{affiliate_meta\}
\f2  retrieval.\
	\'95	Prompt templates loaded from 
\f4 /src/prompts/review_narrative_\{locale\}.txt
\f2 .\
	\'95	Output via Pydantic 
\f4 ReviewDoc
\f2  schema (structured, enforce integrity).\
	\'95	QA chain check: affiliate compliance, missing facts, style. Block publish if QA fails.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 E. Workflow Orchestration with LangGraph
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Define nodes for:\
\pard\tqr\tx660\tx820\li820\fi-820\sl324\slmult1\sb240\partightenfactor0

\f5 \cf2 	1.	Ingest content\
	2.	Candidate retrieval\
	3.	Visual capture\
	4.	Narrative generation\
	5.	QA review\
	6.	Publish\
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Edges define flow with conditional transitions (e.g., human-in-the-loop on QA fail).  
\f2 \cf2    \
	\'95	State persisted across runs; traceable in LangSmith.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 F. Observability & Eval with LangSmith
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Instrument every chain and LangGraph node.\
	\'95	Collect prompt inputs/outputs, retrieval contexts, error traces.\
	\'95	Set up evals for factual accuracy, brand tone, affiliate compliance.\
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs26 \cf2 G. Publishing Agent
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Stateless LCEL agent calls WordPress via 
\f4 /src/tools/wordpress.py
\f2 .\
	\'95	Accepts structured input from 
\f4 ReviewDoc
\f2 , includes media (visuals), taxonomies.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 3. Flows & Sequence
\f2\b0\fs28 \cf2 \
\pard\tqr\tx260\tx420\li420\fi-420\sl324\slmult1\sb240\partightenfactor0

\f5 \cf2 	1.	
\f3\b Setup tenant config
\f2\b0  (colors, tone, locale).\

\f5 	2.	
\f3\b LangGraph Ingest Workflow
\f2\b0  \uc0\u8594  fetch, parse, chunk, vectorize.\

\f5 	3.	
\f3\b LangGraph Content Workflow
\f2\b0 :\
\pard\tqr\tx500\tx660\li660\fi-660\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Retrieve \{context\} + visuals \uc0\u8594  Generate article \u8594  QA \u8594  Publish.\
\pard\tqr\tx260\tx420\li420\fi-420\sl324\slmult1\sb240\partightenfactor0

\f5 \cf2 	4.	
\f3\b Human override
\f2\b0  if QA fails \uc0\u8594  hands back into workflow.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 4. PRD Summary Table
\f0\b0\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f6\b\fs26 \cf2 Feature
\f0\b0\fs24 \cf0 	
\f6\b\fs26 \cf2 Description
\f0\b0\fs24 \cf0 	
\f6\b\fs26 \cf2 LangChain/Graph Tooling
\f0\b0\fs24 \cf0 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs26 \cf2 Content Ingestion
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Load, split, embed, store structured fields
\f0\fs24 \cf0 	
\f2\fs26 \cf2 WebBaseLoader, RCTSplitter, SupabaseVectorStore
\f0\fs24 \cf0 \

\f2\fs26 \cf2 Visual Capture
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Screenshots/images scraping & compliance
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Firecrawl/CF/Browserless + RunnableLambda
\f0\fs24 \cf0 \

\f2\fs26 \cf2 Multi-tenant Handling
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Brand/locale-specific prompts & filtering
\f0\fs24 \cf0 	
\f2\fs26 \cf2 LCEL state + LangGraph stateful nodes
\f0\fs24 \cf0 \

\f2\fs26 \cf2 Retrieval & Generation
\f0\fs24 \cf0 	
\f2\fs26 \cf2 MQR to retrieve; narrative prompt \uc0\u8594  ReviewDoc
\f0\fs24 \cf0 	
\f2\fs26 \cf2 MultiQueryRetriever, LCEL chain, Pydantic
\f0\fs24 \cf0 \

\f2\fs26 \cf2 QA & Compliance
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Check content & affiliate metadata; fail gating
\f0\fs24 \cf0 	
\f2\fs26 \cf2 LCEL QA chain with StrOutputParser/schema
\f0\fs24 \cf0 \

\f2\fs26 \cf2 Publishing
\f0\fs24 \cf0 	
\f2\fs26 \cf2 WordPress via native adapter
\f0\fs24 \cf0 	
\f2\fs26 \cf2 WordPressPublishingTool
\f0\fs24 \cf0 \

\f2\fs26 \cf2 Workflow Orchestration
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Define nodes & edges, support human fallback
\f0\fs24 \cf0 	
\f2\fs26 \cf2 LangGraph with state persistence
\f0\fs24 \cf0 \

\f2\fs26 \cf2 Observability & Testing
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Tracing, evals, regression detection
\f0\fs24 \cf0 	
\f2\fs26 \cf2 LangSmith integration
\f0\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0
\cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 5. Implementation Timeline
\f0\b0\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f6\b\fs26 \cf2 Phase
\f0\b0\fs24 \cf0 	
\f6\b\fs26 \cf2 Tasks
\f0\b0\fs24 \cf0 	
\f6\b\fs26 \cf2 Timeline
\f0\b0\fs24 \cf0 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs26 \cf2 1) Ingestion
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Research node + Supabase pipeline
\f0\fs24 \cf0 	
\f2\fs26 \cf2 1\'962 weeks
\f0\fs24 \cf0 \

\f2\fs26 \cf2 2) Content
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Retrieval + narrative chain + ReviewDoc schema
\f0\fs24 \cf0 	
\f2\fs26 \cf2 2\'963 weeks
\f0\fs24 \cf0 \

\f2\fs26 \cf2 3) QA & visual
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Visual nodes + compliance chain + QA gating
\f0\fs24 \cf0 	
\f2\fs26 \cf2 1\'962 weeks
\f0\fs24 \cf0 \

\f2\fs26 \cf2 4) Workflow
\f0\fs24 \cf0 	
\f2\fs26 \cf2 LangGraph build + state + publish node
\f0\fs24 \cf0 	
\f2\fs26 \cf2 2 weeks
\f0\fs24 \cf0 \

\f2\fs26 \cf2 5) Observability
\f0\fs24 \cf0 	
\f2\fs26 \cf2 LangSmith tracing, eval dashboards
\f0\fs24 \cf0 	
\f2\fs26 \cf2 1 week
\f0\fs24 \cf0 \

\f2\fs26 \cf2 6) Testing
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Tenant E2E tests, compliance tests, visual tests
\f0\fs24 \cf0 	
\f2\fs26 \cf2 Ongoing
\f0\fs24 \cf0 \
\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0
\cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 6. Tech Stack & Constraints
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	
\f3\b \cf2 Allowed
\f2\b0 \cf2 : LangChain, LangGraph, LangSmith, Supabase, WordPress.\
	\'95	
\f3\b \cf2 Forbidden
\f2\b0 \cf2 : Custom wrappers, raw HTTP/requests, orchestration code outside LCEL/Graph constructs.\
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs28 \cf2 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f1\b\fs30 \cf2 References
\f2\b0\fs28 \cf2 \
\pard\tqr\tx100\tx260\li260\fi-260\sl324\slmult1\sb240\partightenfactor0
\cf2 	\'95	Agentic RAG design with LangGraph \'97 agents that decide when to retrieve or not        \
	\'95	Declarative orchestration, human-in-the-loop, persistence in LangGraph  \
	\'95	RAG pipelines using LangSmith for observability  \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \
\uc0\u11835 \
\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600\tx6160\tx6720\sl324\slmult1\pardirnatural\partightenfactor0

\f2\fs28 \cf2 \
Let me know if you\'92d like this formatted as a GitHub PR, markdown slide deck, or a shared doc for your team.}