# Decisions

Why this project is built the way it is, oldest first. One entry per decision that changes a
contract, a dependency, a data format or the architecture; IDs are consecutive and never reused.

### ADR-001: Store the gender rule as a language-independent token
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The selected gender rule was saved as its localized display label, so changing the UI language could leave saved data that no longer matched the current options.
- **Decision**: Persist `Any`, `Mixed` or `Single Gender`; translate only at render time and normalize legacy localized labels when loading.
- **Consequences**: New saves are language-independent, old files remain readable, and the selectbox no longer stores display text.

### ADR-002: Keep UI and security helpers in pure modules
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The Streamlit entry point mixes pure presentation logic, password checks and UI orchestration, which made the former two impossible to test without the full UI dependency set.
- **Decision**: Move language labels, calendar markup, password hashing and constant-time comparison into `ui_helpers.py` and `security.py`.
- **Consequences**: These helpers are unit-testable with the standard library, while `main.py` keeps only orchestration and Streamlit-specific code.

### ADR-003: Escape iCalendar text and time-box font downloads
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: Personnel names were interpolated into iCalendar properties without escaping, so commas, semicolons or newlines could corrupt or inject events; PDF font downloads had no timeout and could leave partial files.
- **Decision**: Escape every iCalendar text value and download each font once through a 10-second timeout into a temporary file before replacing the target.
- **Consequences**: Exported calendars stay well-formed for any name, and PDF generation fails over to built-in fonts instead of hanging on a slow network.

<!-- Entry format:
### ADR-NNN: <decision in one line>
- **Date**: YYYY-MM-DD
- **Status**: Accepted
- **Context**: <what forced the decision>
- **Decision**: <what was decided>
- **Consequences**: <what follows, including what it costs>
-->

## Licensing migration (agpl-final)

- New versions use the Aegean License 1.1 (AL-1.1); versions up to and including `agpl-final` remain under GNU AGPL-3.0.
- Rights holder: AegeanWorks; commercial use under ACL-1.0.
- Counsel review of the 1.1 texts remains pending.
