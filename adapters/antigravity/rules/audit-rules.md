<!-- audit-kit:start -->
# Code Audits (audit-kit)

- To run a code audit, follow `audit-kit/RUN.md`. Standard mode by default; Full mode when asked.
- Audit agents are strictly read-only: they write only inside `audit/`. Never edit project files during an audit.
- In Antigravity, launch auditors in parallel using `invoke_subagent` following `audit-kit/adapters/antigravity/subagents.md`.
- All audit output, code comments, commits, and documentation are in English, whatever language the chat uses.
<!-- audit-kit:end -->
