# AGENT.md

# Website Intelligence Service — AI Coding Agent Rules

## Project Goal

The objective is to build **Version 1 (MVP)** of a Website Intelligence Service.

The service accepts a website URL, crawls only the important public pages, extracts structured business information without using any LLM, and returns a compact JSON response.

This project is **not** responsible for:

* n8n
* CRM
* Email Automation
* Databases
* AI Lead Scoring
* LLM Integration
* Vector Databases

Those systems will consume this API later.

The only responsibility of this project is:

> **Website URL → Structured JSON**

---

# Development Philosophy

Always optimize for:

* Simplicity
* Readability
* Maintainability
* Production readiness

Avoid unnecessary abstractions.

Do not build for future features unless explicitly requested.

Keep the codebase as small as possible while remaining clean.

---

# Current Scope (V1 Only)

The goal is **NOT** to build the complete platform.

The goal is to have a working MVP with:

* FastAPI backend
* Crawl4AI integration
* Structured extraction
* Simple frontend
* JSON response

Nothing more.

If something is not required for V1, do not implement it.

---

# MVP Features

The MVP should include only:

* URL input
* Crawl homepage
* Detect important pages
* Crawl selected pages
* Extract structured information
* Return normalized JSON
* Display JSON in frontend
* Display extracted fields in frontend

No authentication.

No database.

No Docker orchestration beyond what is needed to run locally.

No Redis.

No queues.

No background workers.

No caching.

No AI.

No deployment automation.

---

# Frontend

A minimal frontend is required.

Purpose:

* Enter website URL
* Submit request
* Display loading state
* Show extracted information
* Show raw JSON

The frontend is only for manual review.

UI quality is not important.

Functionality is.

---

# Architecture Rules

Always separate responsibilities.

Example:

FastAPI

↓

Crawler

↓

Extractors

↓

Merger

↓

Response

Each module should have one responsibility.

Never mix crawling with extraction.

Never mix extraction with API routes.

Never put business logic inside FastAPI endpoints.

---

# Coding Rules

Always use:

* Python 3.11
* Type hints
* Pydantic models
* Async functions where appropriate
* Structured logging
* Small reusable functions

Avoid:

* Large files
* Large classes
* Duplicate logic
* Magic numbers
* Global mutable state

Keep functions focused.

Aim for functions under ~50 lines where practical.

---

# File Organization

Prefer many small modules over one large file.

Each extractor should live in its own file.

Each module should have a single responsibility.

---

# Error Handling

Never silently ignore errors.

Catch expected failures.

Return meaningful error messages.

Log exceptions with sufficient context.

Do not crash the application because one page fails.

Continue processing where possible.

---

# Performance Rules

Do not crawl unnecessary pages.

Maximum pages:

10

Default concurrency:

5

Timeout:

15 seconds

Stop crawling when enough useful pages have been collected.

---

# Git Rules

The agent has permission to commit changes.

After completing any meaningful feature, bug fix, or refactor:

1. Review changed files.
2. Write a clear commit message.
3. Commit changes to Git.

Do **not** push to remote automatically unless explicitly instructed.

Commit messages should follow this style:

```
feat: add homepage crawler

fix: improve email extraction

refactor: simplify page selector

docs: update project memory
```

---

# Project Memory Rules

A file named:

```
project_memory.md
```

must always be maintained.

This file is the project's long-term memory.

After **every Git commit**, update `project_memory.md`.

It should contain concise, cumulative knowledge so future work does **not** require reading the entire codebase.

---

## project_memory.md Structure

Always maintain these sections:

```
# Project Overview

# Current Architecture

# Completed Features

# Pending Features

# API Endpoints

# Folder Structure

# Important Design Decisions

# Known Issues

# Future Ideas

# Git History Summary
```

Keep it current.

Do not duplicate source code.

Summarize decisions and implementation details.

---

# Refactoring Rules

Only refactor when:

* It reduces complexity.
* It improves readability.
* It removes duplication.
* It fixes a real problem.

Do not refactor simply for style preferences.

Avoid large rewrites during feature work.

---

# Dependencies

Before adding a dependency, verify:

* It solves a real problem.
* The standard library cannot solve it.
* The dependency is maintained.
* It is reasonably lightweight.

Avoid dependency bloat.

---

# Testing

For every new feature:

* Verify it manually.
* Confirm the API response.
* Confirm the frontend renders correctly.
* Confirm no existing functionality breaks.

Prefer small, focused unit tests for core logic when practical.

---

# Documentation

Whenever a public function or module has non-obvious behavior, document:

* Purpose
* Inputs
* Outputs
* Edge cases

Avoid redundant comments.

Code should be self-explanatory whenever possible.

---

# Communication Style

When implementing work:

* Think before coding.
* Explain major architectural decisions briefly.
* Raise concerns if a requested change conflicts with existing architecture.
* Ask for clarification instead of making assumptions when requirements are ambiguous.

---

# Out of Scope for V1

Do not implement any of the following unless explicitly requested:

* Authentication
* User accounts
* Database
* Redis
* Celery
* Kafka
* RabbitMQ
* LLM integration
* AI lead scoring
* Batch processing
* Job queues
* Multi-tenant support
* Cloud deployment automation
* Monitoring dashboards
* Rate limiting
* Analytics
* Billing
* Webhooks

---

# Definition of Done

A task is complete only when:

* The feature works end-to-end.
* Code follows the architecture rules.
* No obvious bugs remain.
* `project_memory.md` has been updated.
* Changes have been committed to Git.
* The application still runs successfully.
* The frontend can demonstrate the new functionality (when applicable).

The priority is to deliver a clean, working MVP as quickly as possible. Build only what is necessary for Version 1, validate it, and iterate from there.
