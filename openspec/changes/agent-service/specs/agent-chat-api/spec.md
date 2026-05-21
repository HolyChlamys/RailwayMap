## ADDED Requirements

### Requirement: Agent Chat API

The system SHALL provide a REST endpoint `POST /api/agent/chat` that accepts a user message and returns a natural language reply with structured frontend instructions.

#### Scenario: User sends a route planning query
- **WHEN** user sends `{ "session_id": "abc", "message": "北京到广州，中途停武汉" }`
- **THEN** the response contains `text` (natural language reply), `instructions` (array of frontend actions), and `suggestions` (array of follow-up prompts)
- **AND** HTTP status is 200

#### Scenario: Multi-turn conversation preserves context
- **WHEN** user sends two consecutive messages in the same session
- **THEN** the second request's LLM prompt includes the first message's intent and constraints
- **AND** session state is preserved for at least 30 minutes

### Requirement: LLM Intent Classification

The Agent SHALL classify user input into one of: `route_planning`, `isochrone`, `station_query`, `train_query`, `timetable_query`, or `clarify`, using the LLM with a structured JSON output constraint.

#### Scenario: Ambiguous input triggers clarify intent
- **WHEN** user sends "我想出去玩" without origin, destination, or time constraint
- **THEN** intent is classified as `clarify`
- **AND** the reply asks clarifying questions about missing information

#### Scenario: Clear route query triggers route planning intent
- **WHEN** user sends "从北京西到广州南，G字头，换乘不超过1次"
- **THEN** intent is `route_planning`
- **AND** constraints include `from: "北京西"`, `to: "广州南"`, `trainTypes: ["G"]`, `maxTransfers: 1`

### Requirement: Station Name Disambiguation

When the LLM extracts a station name that may be ambiguous, the Agent SHALL call the station search API and ask the user to choose among candidates.

#### Scenario: Ambiguous station name
- **WHEN** user mentions "南京" as a station
- **THEN** Agent calls `GET /api/stations/search?q=南京`
- **AND** if multiple results, reply lists them: "南京有多个车站：南京站、南京南站。你指的是？"

### Requirement: Multi-turn Conversation State

The Agent SHALL maintain a state dictionary per session including: message history, extracted constraints, tool call results, and relaxation history.

#### Scenario: State persists across turns
- **WHEN** user first asks "北京到广州" then follows up with "只看高铁"
- **THEN** the second request's state includes the original `from: "北京"` and `to: "广州"` constraints
- **AND** the filter "只看高铁" is applied on top of existing constraints
