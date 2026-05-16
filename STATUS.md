# Hermes Project Status

## Version: V0.4-pre (Controlled Autonomous Runtime Kernel)

Hermes is a Local-first, Chat-first Controlled Autonomous Agent Runtime Kernel.

### Current Capabilities
- **Autonomous Loop**: Multi-step observe-plan-execute loop with observation feedback and iteration capping.
- **Governance Layer**: Integrated `GovernanceManager` providing real enforcement in `SafeExecutor`.
- **Management Decision Layer**: Functional pipeline (Executive -> Strategy -> Operator -> Auditor) with structured `DecisionPacket` and `ManagedTaskPlan`.
- **Diagnostic Panel**: Management Chain UI (L1-L4) in Dashboard for real-time governance visibility and pass/fail diagnostics.
- **Controlled Writing**: Support for `write_proposal` (patch) and `shell_proposal` with governance gates in `SafeExecutor`.
- **Testing**: 143+ unit and behavioral tests verifying safety boundaries and autonomous logic.

### Technology Stack
- **Backend**: Python 3.12, custom HTTP Runtime.
- **Frontend**: Vanilla JS / CSS Dashboard with real-time trace polling.
- **LLM**: Primary support for Ollama (Qwen2.5/Qwen3), with Mock fallback for development.

### Roadmap to V0.5: Product-grade Governance Experience
1. **Approval Flow Productization**: Full API/UI for patch and shell approval lifecycle.
2. **Scoped Governance Grants**: Transition from global permissions to task-scoped, timed authorization.
3. **Trace Schema Standardization**: Formalizing audit logs for professional-grade observability.
4. **Provider Health**: Explicit Ollama health monitoring and error reporting (no silent fallbacks).
5. **Documentation**: Comprehensive README, Install Guide, and Governance behavior specs.

---
*Last Updated: 2026-05-16*
