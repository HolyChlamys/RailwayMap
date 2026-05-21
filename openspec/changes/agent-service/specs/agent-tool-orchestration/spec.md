## ADDED Requirements

### Requirement: Tool Calling via Java Backend API

The Agent SHALL call Java backend REST APIs via HTTP for: station search, station detail, train route, transfer search, isochrone, and station timetable. Each tool is wrapped as an async Python function with a consistent `dict` return type.

#### Scenario: Parallel tool execution
- **WHEN** user query requires both station info and route planning
- **THEN** Agent issues HTTP calls in parallel using `asyncio.gather`
- **AND** individual tool failures do not block other tools

#### Scenario: Tool call failure is reported
- **WHEN** a Java API returns 4xx or 5xx
- **THEN** the error is recorded in `tool_results[i].error`
- **AND** the Agent reply informs the user which specific information is unavailable

### Requirement: Constraint Extraction and Formatting

The LLM SHALL extract T/N/S/D four-dimensional constraints from natural language and output structured JSON.

#### Scenario: Full constraint extraction
- **WHEN** user says "放假回家，中途在武汉停，每段不超过4小时，只坐高铁"
- **THEN** extracted JSON includes: `via: "武汉"`, `dMax: 240` (minutes), `trainTypes: ["G"]`
- **AND** missing required fields (`from`, `to`) are marked in `missing` array

#### Scenario: Fuzzy constraint quantification
- **WHEN** user says "不要太累，每段别太久"
- **THEN** LLM quantifies fuzzy constraint to `dMax: 240` (default 4 hours)
- **AND** reply acknowledges the interpretation: "我理解为每段不超过4小时"

### Requirement: Constraint Relaxation

When no routes match user constraints, the Agent SHALL relax constraints in priority order: remove transfer station → loosen D_max → increase N_max → loosen T window. Maximum 3 relaxation rounds.

#### Scenario: No results triggers relaxation
- **WHEN** `search_transfer` returns empty for original constraints
- **THEN** Agent removes the `via` constraint and retries
- **AND** if results found, reply explains: "按你的条件没找到经停武汉的路线。去掉武汉中转后有3条方案"

#### Scenario: All relaxation rounds exhausted
- **WHEN** all 3 relaxation rounds return empty
- **THEN** Agent replies: "抱歉，即使放宽条件也没找到可用路线"
- **AND** suggests the user try different origin/destination

### Requirement: Constraint Conflict Detection

The Agent SHALL detect logically conflicting constraints before calling the search API.

#### Scenario: Segment duration exceeds D_max
- **WHEN** user specifies via station whose natural segment exceeds D_max
- **THEN** Agent warns: "北京到武汉的最短行程需要4.5小时，但你要求每段不超过4小时。建议放宽时间限制"
- **AND** does not call the search API

### Requirement: Isochrone Search with Direction Guidance

The Agent SHALL call the isochrone API and present results grouped by direction, then guide the user to select a direction or transition to route planning.

#### Scenario: Isochrone exploration
- **WHEN** user asks "武汉出发4小时内能去哪"
- **THEN** Agent calls `POST /api/isochrone` with stationId and hours
- **AND** reply groups results by direction: "往东（合肥方向）24站，往南（长沙方向）33站，往北（郑州方向）40站，往西（重庆方向）22站。你想去哪个方向？"
