# Google OR-Tools Agent Skill (`google-ortools`)

[![Agent Skills Standard](https://img.shields.io/badge/Agent_Skills-skills.sh-black)](https://skills.sh)
[![OR-Tools](https://img.shields.io/badge/Google_OR--Tools-v9.10%E2%80%93v9.15+-4285F4)](https://developers.google.com/optimization)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](./LICENSE)

Comprehensive **AI Agent Skill** for [Google OR-Tools (`developers.google.com/optimization`)](https://developers.google.com/optimization), compatible with **[skills.sh](https://skills.sh)** (`npx skills`), **Google Antigravity**, **Claude Code**, **Cursor**, **GitHub Copilot**, **Windsurf**, and **OpenAI Codex**.

> **[🇹🇷 Türkçe Kurulum ve Yayınlama Rehberi aşağıdadır](#türkçe-rehber--kurulum-ve-skillssh-yayınlama)**

---

## English Guide

### Why This Skill?

Out of the box, LLMs frequently hallucinate outdated OR-Tools v7/v8 SWIG APIs (such as `ortools.graph.pywrapgraph` or `pywrapknapsack_solver`), mix up `Node` vs. internal `Index` in Vehicle Routing, pass floats into integer-only `cp_model`, or use Python booleans (`if`, `and`, `or`, `max`) directly on decision variables.

This skill equips AI coding agents with:
1. **Solver Selection Matrix**: Automatic routing between **CP-SAT** (`cp_model`), **MPSolver** (`pywraplp` with `GLOP`, `PDLP`, `SCIP`, `HIGHS`, `CBC`), **MathOpt** (`ortools.math_opt`), **Vehicle Routing** (`pywrapcp`), **Graph/Network Flows** (`max_flow`, `min_cost_flow`, `linear_sum_assignment`), and **Knapsack** (`knapsack_solver`).
2. **Modern OR-Tools v9.10–v9.15+ Guardrails**: Enforces PEP 8 `snake_case` methods in `cp_model` and modern pybind11 graph/knapsack modules.
3. **Progressive Disclosure Reference Library**: 8 deep-dive reference guides loaded on-demand only when relevant to the user's task.
4. **Verified Runnable Templates & Diagnostic CLI**: 4 end-to-end Python reference scripts and an environment/solver diagnostic tool.

### Quick Installation via `skills.sh` (`npx skills`)

```bash
# Install all skills from this repository into your project
npx skills add yucel-yilmaz/google-ortools-skills

# Install specifically the google-ortools skill
npx skills add yucel-yilmaz/google-ortools-skills --skill google-ortools

# Install globally across all projects on your machine
npx skills add yucel-yilmaz/google-ortools-skills --skill google-ortools -g
```

### Repository Structure

```text
.
├── .agents/
│   └── skills.json                                   # Auto-discovery config for Google Antigravity
├── skills/
│   └── google-ortools/
│       ├── SKILL.md                                  # Main Agent Skill entry point & guardrails
│       ├── references/
│       │   ├── solver-selection-and-architecture.md  # Decision tree: CP-SAT vs LP/MILP vs MathOpt vs VRP vs Graph
│       │   ├── cp-sat-guide.md                       # Complete CP-SAT (cp_model) modeling patterns
│       │   ├── linear-mip-mathopt.md                 # LP, MILP (pywraplp) & modern MathOpt (QP/MIQP/Warm-start)
│       │   ├── vehicle-routing.md                    # TSP, CVRP, VRPTW, Pickup & Delivery, Dropped visits
│       │   ├── scheduling-patterns.md                # Shift Rostering, Job-Shop (JSP), Flexible JSP, RCPSP
│       │   ├── network-flows-and-packing.md          # MaxFlow, MinCostFlow, Assignment, Knapsack, 2D Bin Packing
│       │   ├── debugging-and-performance.md          # Unsat core assumptions, slack relaxation, scaling, tuning
│       │   └── multi-language-cheatsheet.md          # Side-by-side Python, C++, Java, and C# (.NET) API mapping
│       ├── examples/
│       │   ├── cpsat_scheduling_jobshop.py           # Job-Shop Scheduling (CP-SAT)
│       │   ├── lp_mip_production_planning.py         # Continuous LP Duals (GLOP) + MILP (MathOpt)
│       │   ├── vrp_time_windows_capacity.py          # CVRPTW with Disjunctions & Guided Local Search
│       │   └── network_flow_and_knapsack.py          # Min-Cost Flow, Linear Assignment & Knapsack
│       └── scripts/
│           └── diagnose_env_and_model.py             # Environment & solver backend diagnostic script
├── package.json
├── LICENSE
└── README.md
```

---

## Türkçe Rehber — Kurulum ve `skills.sh` Yayınlama

Bu depo, [Google OR-Tools (`developers.google.com/optimization`)](https://developers.google.com/optimization) kütüphanesini **Antigravity**, **Cursor**, **Claude Code**, **Windsurf**, **GitHub Copilot** ve **Codex** gibi AI kodlama araçlarında en güncel API (v9.10–v9.15+) standartlarıyla kullanabilmeniz ve **[skills.sh](https://skills.sh)** üzerinde yayınlayabilmeniz için hazırlanmıştır.

### 1. `skills.sh` Üzerinde Nasıl Yayınlanır?

`skills.sh` (Vercel Labs `npx skills` ekosistemi) paket kaydı olarak doğrudan **GitHub** depolarını kullanır. Yayınlamak için:

1. GitHub'da **Public** bir depo oluşturun (`yucel-yilmaz/google-ortools-skills`).
2. Bu klasördeki dosyaları GitHub deponuza gönderin:
   ```bash
   git init
   git add .
   git commit -m "feat: add google-ortools agent skill"
   git branch -M main
   git remote add origin https://github.com/yucel-yilmaz/google-ortools-skills.git
   git push -u origin main
   ```
3. Deponuz yayına girdiğinde `npx skills` CLI aracı `skills/google-ortools/SKILL.md` dosyasını otomatik olarak tanır ve `skills.sh` dizininde listelenebilir hale gelir.

### 2. AI Araçlarına Kurulum (`npx skills add`)

Yayınladıktan sonra herhangi bir projede veya global olarak tek komutla kurabilirsiniz:

```bash
# Projeye kurulum (Claude Code, Cursor, Antigravity, Copilot vb. otomatik algılanır)
npx skills add yucel-yilmaz/google-ortools-skills

# Sadece google-ortools skill'ini seçerek kurulum
npx skills add yucel-yilmaz/google-ortools-skills --skill google-ortools

# Bilgisayar genelinde (Global) tüm projeler için kurulum
npx skills add yucel-yilmaz/google-ortools-skills -g

# Yerel klasörden test/kurulum yapmak için:
npx skills add .
```

> **Google Antigravity Notu:** Depo kök dizinindeki [`.agents/skills.json`](./.agents/skills.json) dosyası sayesinde bu klasörü Antigravity ile açtığınızda `google-ortools` skill'i ek hiçbir komuta gerek kalmadan otomatik olarak yüklenir.

### 3. Doğrulama ve Örnekleri Çalıştırma

Ortamınızdaki OR-Tools sürümünü ve aktif çözücü motorlarını (`CP-SAT`, `GLOP`, `PDLP`, `SCIP`, `HIGHS`, `CBC`) test etmek için:

```bash
python skills/google-ortools/scripts/diagnose_env_and_model.py
```

Hazır referans örnekleri çalıştırmak için:

```bash
python skills/google-ortools/examples/cpsat_scheduling_jobshop.py
python skills/google-ortools/examples/lp_mip_production_planning.py
python skills/google-ortools/examples/vrp_time_windows_capacity.py
python skills/google-ortools/examples/network_flow_and_knapsack.py
```
