
### 🧠 Concept Summary: Self-Improving Program (SIP)

**Core Idea:**
A lightweight, optimized version of OpenHands that self-improves through its own CI/CD loop, focused on **Python** and using **GitHub Issues + Actions** as the control interface.

---

### 📋 Diagram Flow

See: doc/img/idea_2.jpeg

A visual flow of the SIP lifecycle:

1. **Start** (Human interaction)
2. **Create Issue** → Issue is marked as "open"
3. **AI Works on It** (triggered by Issue)

   * Branch is created
   * AI generates PR
4. **PR** leads to:

   * **Auto Tests**

     * If fail → back to AI
     * If success → Merge to main
5. **End**

---

### 🧰 Design Principles

See: doc/img/idea_2.jpeg

* Inspired by OpenHands, but simplified for self-improvement.
* **Stack**: Pure Python
* **GitHub as Interface**:

  * Issues = Tasks
  * PR = Changes
  * GitHub Actions = Trigger Engine (CI)
* **Record Everything** (for later learning or feedback loops. especially AI conversations.)
* **Trigger Point = Issue creation**
* **One Dedicated Token** (cost-conscious — OpenRouter)
* **Build MVP, then let it run**

---

### 🛠️ Execution Mechanics

See: doc/img/idea_3.jpeg

* **Branch checked out**
* **Full codebase loaded into context**

#### ACTION: EDIT

```json
[
    {
        "path":"src/main.py",
        "content":"import os\n...."
    },
    {
        "path":"myfile.txt",
        "content": null
    }
]
```

Triggers Run compile + test

    * On success → push PR
    * On fail → close + retry

# ACTION: SUBMIT

```json
{
    "branch":"bugfix/issue_xyz_fix_bug_x",
    "pr":{"title":"title of the pr", "many":"morefields"},

}
```

First run compile+test. If fail, return to AI.

Otherwise commit, create the PR.

---

# CI

The CI is set up, so that if there is a PR, and the tests all pass, it will be automatically merged to main.

### 🔑 Key Innovations

* Minimal setup, no orchestration layer
* GitHub-native (no external interfaces)
* Event-driven improvement: Issues → Code → PR → Merge
* Cheap and reproducible: good for LLM sandboxing and proof of concept
* Designed for running **autonomously** long-term (MVP → hands off)
