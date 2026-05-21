## ADDED Requirements

### Requirement: Frontend Instruction Execution

The Agent response SHALL include an `instructions` array that drives Pinia store actions and map interactions. Each instruction has `action` and parameters.

#### Scenario: Route result triggers map highlight
- **WHEN** Agent returns route planning results
- **THEN** `instructions` includes `{ "action": "highlightRoutes", "routeIds": ["plan-1", "plan-2"] }`
- **AND** the frontend executes `mapStore.setHighlightedRoutes(routeIds)`
- **AND** the map shows the routes with train-type-colored dashed flowing lines

#### Scenario: Station query triggers map focus
- **WHEN** Agent returns station query results
- **THEN** `instructions` includes `{ "action": "flyToStation", "stationId": "..." }`
- **AND** `{ "action": "openPanel", "panel": "station" }`
- **AND** the map animates to center on the station with appropriate zoom

### Requirement: Train Route Map Animation

When displaying a train route on the map, the system SHALL render a dashed flowing line in the train-type color with a signal-scanning pulse effect.

#### Scenario: Single train route animation
- **WHEN** a train route is highlighted on the map
- **THEN** line is rendered with alternating dash (8px solid, 6px gap) in train-type color (high-speed red, bullet orange, conventional blue)
- **AND** the dash pattern flows along the travel direction at speed proportional to train type
- **AND** a luminous pulse sweeps from origin to destination every 1.5 seconds
- **AND** intermediate stations are marked with small colored dots; origin/terminal stations have larger dots with pulsing glow

#### Scenario: Multiple train routes shown simultaneously
- **WHEN** multiple train routes are highlighted
- **THEN** each route uses its own train-type color independently
- **AND** animations do not interfere across routes

#### Scenario: Many routes (simplified display)
- **WHEN** more than 3 routes are shown
- **THEN** routes are rendered as simple colored lines with transfer station nodes
- **AND** detailed dash-flowing animation is disabled to maintain performance

### Requirement: Isochrone Map Visualization

When displaying isochrone results, the system SHALL highlight the origin station prominently and show reachable route segments with subdued styling.

#### Scenario: Isochrone result display
- **WHEN** isochrone results are returned
- **THEN** origin station node is enlarged with pulsing glow
- **AND** reachable route segments are highlighted (without animation)
- **AND** map viewport adjusts to fit all reachable segments

### Requirement: City Search Map Integration

When searching for a city, the system SHALL highlight all stations within that city on the map.

#### Scenario: City search
- **WHEN** user searches for a city (e.g., "北京")
- **THEN** the map centers on the city's station cluster
- **AND** all stations in that city are highlighted with expanded circles
- **AND** a `HyperlinkText` link to each station is shown in the reply

### Requirement: Replace Frontend Mock with API Calls

The `useAgentChat.ts` composable SHALL replace all mock logic with real HTTP POST calls to `/api/agent/chat`.

#### Scenario: Agent chat sends real request
- **WHEN** user sends a message through the Agent panel
- **THEN** `useAgentChat.sendMessage()` posts to `/api/agent/chat`
- **AND** the response `text` is displayed as an Agent message bubble
- **AND** `instructions` are dispatched to corresponding Pinia stores
- **AND** `suggestions` are rendered as quick suggestion chips

#### Scenario: Loading state during request
- **WHEN** agent request is in flight
- **THEN** the typing indicator (3 bouncing dots) is shown
- **AND** the text input is disabled
