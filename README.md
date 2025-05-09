# Project Plan: JetBrains Plugin for On-Demand Cloud-Based LLM (CodeLlama) Integration

## Stage 0: Prerequisites
- **Plugin Language**: Kotlin (recommended by JetBrains)
- **Tools**: IntelliJ Platform SDK, Gradle, Plugin DevKit
- **Cloud Providers**: GCP / AWS (accessed via CLI or SDK)
- **External Infra Scripts**: Python or Bash
- **LLM**: `ollama` running CodeLlama:Python model on a GPU instance

---

## Stage 1 MVP scripts (python) to implement base functions
- create/delete VM with LLM
- start/stop VM
- create/delete account in cloud provider (GCP) service
- create/delete project/billing

## Stage 2: MVP Plugin on Java – Launch GPU Cloud Instance

### Features
- Plugin adds an action: "Launch LLM Instance"
- Triggers external script (e.g., Python or Bash) to start a GPU instance via `gcloud` or `aws`
- Displays a notification: "LLM instance launched"

### Technical Details
- Kotlin-based plugin using Gradle
- Executes external scripts via `ProcessBuilder`
- Simple UI (menu action or toolbar button)

---

## Stage 3: Auto-Configuration of JetBrains AI Assistant

### Features
- After instance launch, plugin fetches public IP + port
- Configures JetBrains AI Assistant to connect to the remote REST API (via Ollama)
- May require modification of `.ide.ai.settings.json` or use of JetBrains internal APIs

### Technical Details
- IP fetched via cloud SDK or CLI
- Connection settings updated programmatically (as allowed by JetBrains AI integration)

---

## Stage 4: Session Termination & Auto-Shutdown

### Features
- "Shutdown LLM" button
- Auto-shutdown after 10 minutes of inactivity
- Notifies the user when the instance is stopped

### Technical Details
- Kotlin-based inactivity timer
- Shutdown triggered via external script using `gcloud` or `aws`

---

## Stage 5: Dual Cloud Provider Support

### Features
- User selects GCP or AWS in configuration
- Plugin adapts scripts and credentials accordingly

### Technical Details
- Simple UI or config file for cloud selection
- Uses either CLI or SDK for instance management

---

## Stage 6: Deep JetBrains AI Assistant Integration

### Features
- Uses JetBrains AI SDK (when available) for deeper IDE integration
- Direct interaction with LLM for code explanation, refactoring, test generation

### Technical Details
- Use JetBrains plugin extension points
- Full pipeline handling: user input → LLM → output rendering

---

## Stage 7: UX Improvements and Robust Error Handling

- Loading indicators
- Cloud credential validation
- Retry logic for failed connections
- Instance status monitoring
- Live status icon for LLM connectivity

---

## Optional Enhancements

- Telegram or email notifications for instance lifecycle events
- Request/response logging
- Uptime and cost monitoring via cloud dashboards
