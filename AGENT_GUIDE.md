# 🧠 Stock Agent AI - Developer Guide

## 🎯 Goal
Build a multi-agent stock analysis system using LangGraph.

---

## 🏗️ Architecture Principles

- Use LangGraph for orchestration
- Keep agents SMALL and SINGLE responsibility
- NEVER mix data fetching + reasoning
- Prefer deterministic logic over LLM when possible

---

## 🤖 Agents Rules

### Data Agent
- Only fetch + normalize data
- NO LLM usage

### Technical Agent
- Use pandas-ta
- DO NOT use LLM

### Sentiment Agent
- Use LLM
- Must be short prompt

### Decision Agent
- Combine all signals
- Output STRICT JSON

---

## ⚠️ Critical Constraints

- DO NOT compute RSI using LLM
- DO NOT call external API inside Decision Agent
- ALWAYS validate LLM output

---

## 🧩 Coding Rules

- Use TypedDict for state
- Avoid global variables
- Each agent returns partial state

---

## 🔥 Prompt Rules

- Keep prompts short
- Always define output schema
- Avoid hallucination by constraining format

---

## 🧪 Testing

- Test each agent independently
- Mock LLM when needed

---

## 🚀 Future Extensions

- Add backtesting engine
- Add scoring system
- Add memory agent
- Add multi-symbol batching

---

## 🧠 Notes for AI Coding (Codex)

When modifying code:
- Do NOT break graph structure
- Ensure state keys remain consistent
- Prefer adding new agent over modifying existing

---

## 📌 Example Flow

symbol → data → indicators + fundamentals + sentiment → decision → alert