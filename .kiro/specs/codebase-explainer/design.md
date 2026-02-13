# Design Document: AI-Powered Codebase Explainer

## Overview

The AI-Powered Codebase Explainer is a web-based application that analyzes public GitHub repositories and generates beginner-friendly explanations. The system uses a multi-stage pipeline: repository fetching, static analysis, AI-powered explanation generation, and presentation.

### Key Design Decisions

1. **Shallow Clone Strategy**: Use shallow git clones (depth=1) to minimize download time and storage
2. **Sampling for Large Repos**: Analyze a representative sample of files rather than entire large codebases
3. **Local AI Models**: Use Ollama or similar for running open-source LLMs locally (Llama 3, Mistral, CodeLlama)
4. **Static Analysis First**: Perform deterministic analysis before AI generation to reduce AI token usage
5. **Progressive Enhancement**: Display static analysis results immediately, then enhance with AI explanations
6. **File-based Caching**: Cache analysis results as JSON files to avoid re-analyzing repositories

### Technology Stack

- **Backend**: Python with FastAPI (async support, easy integration with AI libraries)
- **Frontend**: React with TypeScript (component-based UI, type safety)
- **Repository Access**: GitPython library for cloning and traversing repositories
- **Static Analysis**: Tree-sitter for parsing multiple languages, ast module for Python
- **AI Integration**: Ollama Python client for local LLM inference
- **Caching**: File-based JSON storage with repository URL hash as key

## Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    (React Frontend + API Client)        │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  - Request validation                   │
│  - Progress tracking                    │
│  - Response formatting                  │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       Analysis Orchestrator             │
│  - Pipeline coordination                │
│  - Cache management                     │
│  - Error recovery                       │
└─────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌──────────────┐    ┌──────────────────┐
│   Static     │    │   AI Generation  │
│   Analysis   │───▶│     Layer        │
│   Layer      │    │                  │
└──────────────┘    └──────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│      Repository Access Layer            │
│  - GitHub API client                    │
│  - Git clone operations                 │
│  - File system traversal                │
└─────────────────────────────────────────┘
```

### Data Flow

1. User submits GitHub URL via web interface
2. API validates URL and checks cache
3. If not cached, orchestrator initiates analysis pipeline:
   - Repository cloning (shallow)
   - Structure parsing
   - File importance ranking
   - Dependency extraction
   - Architecture detection
   - Flow analysis
4. Static analysis results returned to frontend immediately
5. AI enhancement runs asynchronously, streaming updates to frontend
6. Final results cached for future requests

## Components and Interfaces

### 1. Repository Fetcher

**Responsibility**: Clone and access GitHub repositories

**Interface**:
```python
class RepositoryFetcher:
    def fetch_repository(url: str, target_dir: Path) -> Repository:
        """
        Clone repository to local directory.
        Returns Repository object with metadata.
        Raises: InvalidURLError, AccessDeniedError, NetworkError
        """
        
    def validate_github_url(url: str) -> bool:
        """
        Validate GitHub URL format.
        Returns True if valid, False otherwise.
        """
        
    def get_repository_metadata(url: str) -> RepositoryMetadata:
        """
        Fetch metadata via GitHub API without cloning.
        Returns: stars, forks, language, description, etc.
        """
```

**Implementation Notes**:
- Use GitPython with `git clone --depth 1` for shallow clones
- Extract owner/repo from URL using regex: `github\.com/([^/]+)/([^/]+)`
- Use GitHub REST API for metadata (no authentication required for public repos)
- Clone to temporary directory with cleanup on completion

### 2. Structure Analyzer

**Responsibility**: Parse repository directory structure and identify file types

**Interface**:
```python
class StructureAnalyzer:
    def analyze_structure(repo_path: Path) -> DirectoryTree:
        """
        Build directory tree representation.
        Returns hierarchical structure with file metadata.
        """
        
    def identify_file_types(repo_path: Path) -> Dict[FileType, List[Path]]:
        """
        Categorize files by type (source, config, docs, tests).
        Returns mapping of file types to file paths.
        """
        
    def find_entry_points(repo_path: Path, language: str) -> List[Path]:
        """
        Identify likely entry point files based on language conventions.
        Returns list of entry point file paths.
        """
```

**Implementation Notes**:
- Ignore common directories: `.git`, `node_modules`, `venv`, `__pycache__`, `target`, `build`
- Detect language from file extensions and configuration files
- Entry point patterns by language:
  - Python: `main.py`, `__main__.py`, `app.py`, `manage.py`
  - JavaScript/TypeScript: `index.js`, `main.js`, `app.js`, `server.js`
  - Java: files with `public static void main`
  - Go: `main.go`
  - Rust: `main.rs`

### 3. File Importance Ranker

**Responsibility**: Rank files by importance for focused analysis

**Interface**:
```python
class FileImportanceRanker:
    def rank_files(repo_path: Path, file_list: List[Path]) -> List[RankedFile]:
        """
        Rank files by importance score.
        Returns sorted list with importance scores.
        """
        
    def calculate_centrality(file_path: Path, repo_path: Path) -> float:
        """
        Calculate how central a file is based on imports/references.
        Returns centrality score (0.0 to 1.0).
        """
```

**Ranking Criteria** (weighted sum):
- **Import count** (40%): Number of times file is imported by others
- **File size** (20%): Larger files often contain core logic (cap at reasonable size)
- **Directory depth** (15%): Files closer to root often more important
- **Name patterns** (15%): Match against important names (core, main, base, manager, controller)
- **Modification frequency** (10%): Recent commits indicate active development (via git log)

**Implementation Notes**:
- Use tree-sitter to parse imports across multiple languages
- Limit analysis to top 20 files to maintain performance
- Cache import graph for reuse in flow analysis

### 4. Dependency Parser

**Responsibility**: Extract and categorize project dependencies

**Interface**:
```python
class DependencyParser:
    def parse_dependencies(repo_path: Path) -> DependencyInfo:
        """
        Extract dependencies from configuration files.
        Returns structured dependency information.
        """
        
    def identify_package_manager(repo_path: Path) -> PackageManager:
        """
        Detect package manager from config files.
        Returns package manager type.
        """
        
    def categorize_dependencies(deps: List[Dependency]) -> CategorizedDeps:
        """
        Categorize dependencies as runtime, dev, or testing.
        Returns categorized dependency lists.
        """
```

**Supported Configuration Files**:
- **JavaScript/TypeScript**: `package.json` (npm/yarn/pnpm)
- **Python**: `requirements.txt`, `setup.py`, `pyproject.toml`, `Pipfile`
- **Java**: `pom.xml` (Maven), `build.gradle` (Gradle)
- **Rust**: `Cargo.toml`
- **Go**: `go.mod`
- **Ruby**: `Gemfile`
- **PHP**: `composer.json`

**Implementation Notes**:
- Parse JSON/TOML/XML using standard libraries
- Use regex for requirements.txt format
- Fetch package descriptions from package registries (npm, PyPI) for major dependencies
- Limit to top 10 most important dependencies for detailed descriptions

### 5. Architecture Detector

**Responsibility**: Infer architectural patterns from codebase structure

**Interface**:
```python
class ArchitectureDetector:
    def detect_architecture(repo_path: Path, structure: DirectoryTree) -> ArchitectureInfo:
        """
        Identify architectural patterns and frameworks.
        Returns architecture description with confidence scores.
        """
        
    def detect_framework(repo_path: Path, deps: DependencyInfo) -> List[Framework]:
        """
        Identify frameworks from dependencies and file patterns.
        Returns list of detected frameworks.
        """
```

**Detection Heuristics**:

1. **MVC Pattern**: Presence of `models/`, `views/`, `controllers/` directories
2. **Microservices**: Multiple service directories, Docker compose, API gateway patterns
3. **Monolithic**: Single main application directory with all code
4. **Layered**: Directories like `presentation/`, `business/`, `data/`, `domain/`
5. **Component-based**: Framework-specific patterns (React components, Vue components)

**Framework Detection**:
- Check dependencies for framework packages
- Look for framework-specific files:
  - React: `jsx/tsx` files, `package.json` with react
  - Django: `settings.py`, `urls.py`, `manage.py`
  - Spring: `@SpringBootApplication` annotations, `application.properties`
  - Express: `app.use()`, `app.get()` patterns
  - Flask: `@app.route` decorators

### 6. Flow Analyzer

**Responsibility**: Trace execution flow through the codebase

**Interface**:
```python
class FlowAnalyzer:
    def analyze_flow(entry_point: Path, import_graph: ImportGraph) -> ExecutionFlow:
        """
        Trace execution from entry point through call graph.
        Returns simplified execution flow description.
        """
        
    def identify_request_handlers(repo_path: Path, framework: Framework) -> List[Handler]:
        """
        For web apps, identify route handlers and their flows.
        Returns list of request handlers with their paths.
        """
```

**Implementation Notes**:
- Start from entry point and follow imports up to 3 levels deep
- For web frameworks, identify routes and their handlers
- Use tree-sitter to parse function calls and build call graph
- Limit to main execution paths to avoid overwhelming users
- Generate textual description rather than complex diagrams

### 7. Explanation Generator

**Responsibility**: Generate beginner-friendly explanations using AI

**Interface**:
```python
class ExplanationGenerator:
    def generate_overview(repo_metadata: RepositoryMetadata, 
                         analysis: StaticAnalysis) -> str:
        """
        Generate high-level overview of the project.
        Returns beginner-friendly description.
        """
        
    def explain_architecture(arch_info: ArchitectureInfo) -> str:
        """
        Explain the architectural pattern in simple terms.
        Returns explanation with analogies.
        """
        
    def explain_file_purpose(file_path: Path, file_content: str) -> str:
        """
        Explain what a specific file does.
        Returns concise purpose description.
        """
        
    def generate_contribution_guide(analysis: StaticAnalysis) -> ContributionGuide:
        """
        Suggest areas for beginner contributions.
        Returns structured contribution suggestions.
        """
```

**AI Prompt Strategy**:

Each explanation uses focused prompts with relevant context:

```
System: You are a helpful coding mentor explaining codebases to beginners.
Use simple language and avoid jargon. When technical terms are necessary,
provide brief definitions.

User: Explain this project architecture:
- Language: {language}
- Framework: {framework}
- Directory structure: {structure}
- Pattern detected: {pattern}

Provide a 2-3 paragraph explanation suitable for someone new to {language}.
```

**Fallback Templates**:
If AI is unavailable, use template-based explanations:
- "This is a {language} project using {framework}..."
- "The codebase follows a {pattern} architecture, which means..."

### 8. Contribution Guide Generator

**Responsibility**: Identify beginner-friendly contribution opportunities

**Interface**:
```python
class ContributionGuideGenerator:
    def find_good_first_issues(repo_url: str) -> List[Issue]:
        """
        Fetch issues labeled 'good first issue' via GitHub API.
        Returns list of beginner-friendly issues.
        """
        
    def suggest_documentation_improvements(analysis: StaticAnalysis) -> List[Suggestion]:
        """
        Identify files lacking documentation.
        Returns suggestions for doc improvements.
        """
        
    def identify_test_gaps(repo_path: Path, structure: DirectoryTree) -> List[Suggestion]:
        """
        Find source files without corresponding tests.
        Returns suggestions for test additions.
        """
```

**Suggestion Categories**:
1. **Documentation**: Files with no docstrings/comments, missing README sections
2. **Testing**: Source files without test coverage
3. **Good First Issues**: Issues from GitHub with beginner labels
4. **Code Quality**: Simple refactoring opportunities (long functions, duplicate code)

### 9. Analysis Orchestrator

**Responsibility**: Coordinate the analysis pipeline and manage caching

**Interface**:
```python
class AnalysisOrchestrator:
    def analyze_repository(url: str, progress_callback: Callable) -> AnalysisResult:
        """
        Run complete analysis pipeline.
        Returns comprehensive analysis results.
        Calls progress_callback with status updates.
        """
        
    def get_cached_analysis(url: str) -> Optional[AnalysisResult]:
        """
        Retrieve cached analysis if available and fresh.
        Returns cached result or None.
        """
        
    def cache_analysis(url: str, result: AnalysisResult) -> None:
        """
        Store analysis result in cache.
        """
```

**Pipeline Stages**:
1. Check cache (return if fresh)
2. Validate URL
3. Fetch repository metadata
4. Clone repository (shallow)
5. Analyze structure (10% progress)
6. Rank files (20% progress)
7. Parse dependencies (30% progress)
8. Detect architecture (40% progress)
9. Analyze flow (50% progress)
10. Generate AI explanations (60-90% progress, incremental)
11. Generate contribution guide (95% progress)
12. Cache results (100% progress)

**Error Recovery**:
- If any stage fails, continue with partial results
- Mark failed stages in result object
- Provide fallback explanations for failed AI generation

### 10. API Layer

**Responsibility**: Expose HTTP endpoints for frontend

**Endpoints**:

```python
POST /api/analyze
Request: { "repository_url": "https://github.com/owner/repo" }
Response: { "analysis_id": "uuid", "status": "processing" }

GET /api/analysis/{analysis_id}
Response: {
    "status": "complete" | "processing" | "failed",
    "progress": 0-100,
    "result": AnalysisResult | null,
    "error": string | null
}

GET /api/analysis/{analysis_id}/stream
Response: Server-Sent Events stream with progress updates
```

**Implementation Notes**:
- Use FastAPI background tasks for async analysis
- Store analysis state in memory (dict with analysis_id keys)
- Use SSE for real-time progress updates
- Set timeout of 5 minutes for analysis

## Data Models

### Repository Metadata
```python
@dataclass
class RepositoryMetadata:
    url: str
    owner: str
    name: str
    description: str
    language: str
    stars: int
    forks: int
    last_updated: datetime
```

### Directory Tree
```python
@dataclass
class FileNode:
    name: str
    path: Path
    type: Literal["file", "directory"]
    size: int
    children: List[FileNode]

@dataclass
class DirectoryTree:
    root: FileNode
    total_files: int
    total_size: int
```

### Ranked File
```python
@dataclass
class RankedFile:
    path: Path
    importance_score: float
    reasons: List[str]  # Why this file is important
    language: str
```

### Dependency Info
```python
@dataclass
class Dependency:
    name: str
    version: str
    category: Literal["runtime", "development", "testing"]
    description: Optional[str]

@dataclass
class DependencyInfo:
    package_manager: str
    runtime_deps: List[Dependency]
    dev_deps: List[Dependency]
    test_deps: List[Dependency]
```

### Architecture Info
```python
@dataclass
class ArchitectureInfo:
    primary_pattern: str
    confidence: float
    frameworks: List[str]
    description: str
    diagram: Optional[str]  # Mermaid diagram
```

### Execution Flow
```python
@dataclass
class ExecutionFlow:
    entry_point: Path
    initialization_steps: List[str]
    main_paths: List[FlowPath]
    request_handlers: List[Handler]  # For web apps

@dataclass
class FlowPath:
    description: str
    files_involved: List[Path]
```

### Contribution Guide
```python
@dataclass
class ContributionSuggestion:
    category: Literal["documentation", "testing", "issue", "refactoring"]
    title: str
    description: str
    difficulty: Literal["easy", "medium", "hard"]
    files_involved: List[Path]

@dataclass
class ContributionGuide:
    suggestions: List[ContributionSuggestion]
    getting_started: str
    contributing_file_url: Optional[str]
```

### Analysis Result
```python
@dataclass
class AnalysisResult:
    metadata: RepositoryMetadata
    structure: DirectoryTree
    important_files: List[RankedFile]
    dependencies: DependencyInfo
    architecture: ArchitectureInfo
    execution_flow: ExecutionFlow
    overview_explanation: str
    architecture_explanation: str
    contribution_guide: ContributionGuide
    analysis_timestamp: datetime
    partial: bool  # True if some stages failed
    errors: List[str]
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: GitHub URL Validation

*For any* string input, the URL validator should return true only for properly formatted GitHub repository URLs matching the pattern `https://github.com/{owner}/{repo}` or `github.com/{owner}/{repo}`.

**Validates: Requirements 1.1**

### Property 2: Error Messages for Invalid Repositories

*For any* invalid, non-existent, or private repository URL, the system should return a specific error message indicating the type of failure (invalid format, not found, or access denied) rather than a generic error.

**Validates: Requirements 1.3**

### Property 3: File Type Identification Completeness

*For any* repository structure, the structure analyzer should categorize all non-ignored files into at least one category (source, configuration, documentation, or test), with no files left uncategorized.

**Validates: Requirements 2.2, 2.3, 2.4**

### Property 4: Directory Tree Consistency

*For any* parsed repository, the generated directory tree should accurately reflect the file system structure, such that traversing the tree visits exactly the same files as traversing the actual directory (excluding ignored paths).

**Validates: Requirements 2.1, 2.5**

### Property 5: Important Files Limit

*For any* repository analysis, the number of files marked as "important" should never exceed 20, regardless of repository size.

**Validates: Requirements 3.5**

### Property 6: File Ranking Determinism

*For any* repository analyzed twice with the same content, the file importance rankings should produce identical results (same files in same order with same scores).

**Validates: Requirements 3.3**

### Property 7: Entry Point Detection

*For any* repository in a supported language (Python, JavaScript, TypeScript, Java, Go, Rust), the system should identify at least one entry point file or explicitly report that no entry point was found.

**Validates: Requirements 3.1, 5.1**

### Property 8: Dependency Extraction Completeness

*For any* repository containing a supported dependency configuration file, the dependency parser should extract all listed dependencies and correctly identify the package manager type.

**Validates: Requirements 6.1, 6.4**

### Property 9: Dependency Categorization

*For any* set of extracted dependencies, each dependency should be assigned to exactly one category (runtime, development, or testing), with no dependencies left uncategorized.

**Validates: Requirements 6.2**

### Property 10: Architecture Pattern Assignment

*For any* analyzed repository, the architecture detector should assign exactly one primary architectural pattern (even if that pattern is "custom" or "mixed").

**Validates: Requirements 4.1, 4.5**

### Property 11: Framework Detection from Dependencies

*For any* repository with framework packages in its dependencies, the architecture detector should identify those frameworks in its framework list.

**Validates: Requirements 4.2**

### Property 12: Execution Flow Traceability

*For any* identified entry point, the flow analyzer should trace at least one execution path, or explicitly report that flow analysis failed for that entry point.

**Validates: Requirements 5.2, 5.3**

### Property 13: Technical Term Definitions

*For any* generated explanation containing technical terms (identified by a predefined list or heuristic), the explanation should include definitions or context for those terms within the same section.

**Validates: Requirements 7.2**

### Property 14: Hierarchical Explanation Structure

*For any* generated explanation, the content should be organized with overview information appearing before detailed information, measurable by checking that high-level concepts are introduced before specific implementation details.

**Validates: Requirements 7.4**

### Property 15: Contribution Suggestions Non-Empty

*For any* successfully analyzed repository, the contribution guide should contain at least one suggestion, or explicitly state why no suggestions could be generated.

**Validates: Requirements 8.1, 8.2**

### Property 16: CONTRIBUTING File Reference

*For any* repository containing a CONTRIBUTING file (CONTRIBUTING.md, CONTRIBUTING.txt, etc.), the contribution guide should include a reference or link to that file.

**Validates: Requirements 8.4**

### Property 17: Contribution Explanation Completeness

*For any* contribution suggestion, the suggestion should include both a description of what to do and an explanation of why it's beginner-friendly.

**Validates: Requirements 8.5**

### Property 18: Large Repository Sampling

*For any* repository with more than 1000 files, the system should analyze a sample of files rather than all files, with the sample size not exceeding a configured maximum (e.g., 500 files).

**Validates: Requirements 9.2**

### Property 19: Partial Results on Error

*For any* analysis where at least one stage fails but at least one stage succeeds, the system should return partial results with the successful stages' data and mark the result as partial.

**Validates: Requirements 9.4, 12.3**

### Property 20: Analysis Caching Round-Trip

*For any* repository, if an analysis is performed and cached, then immediately retrieved from cache, the retrieved result should be equivalent to the original result (excluding timestamp fields).

**Validates: Requirements 9.5**

### Property 21: Progress Indicator Monotonicity

*For any* analysis in progress, progress values reported should be monotonically increasing (never decrease) and should start at 0 and end at 100.

**Validates: Requirements 9.3, 10.2**

### Property 22: Result Section Organization

*For any* completed analysis result, the output should contain distinct, labeled sections for: structure, dependencies, architecture, execution flow, and contribution guide.

**Validates: Requirements 10.3**

### Property 23: AI Fallback on Failure

*For any* AI generation request that fails (timeout, model unavailable, error), the system should return a template-based explanation rather than no explanation.

**Validates: Requirements 11.3, 12.4**

### Property 24: AI Context Inclusion

*For any* AI generation request, the prompt should include relevant context from the static analysis (e.g., language, framework, file structure) appropriate to the explanation being generated.

**Validates: Requirements 11.2**

### Property 25: AI Token Limit Enforcement

*For any* AI generation request, the total token count (prompt + expected response) should not exceed the configured maximum token limit for the model being used.

**Validates: Requirements 11.4**

### Property 26: Specific Error Messages

*For any* error condition (GitHub API failure, clone failure, parse failure), the error message should identify the specific type of error rather than returning a generic "something went wrong" message.

**Validates: Requirements 12.1, 12.2**

### Property 27: Error Logging

*For any* error that occurs during analysis, an entry should be written to the error log containing at minimum: timestamp, error type, error message, and context (repository URL, analysis stage).

**Validates: Requirements 12.5**

## Error Handling

### Error Categories

1. **Input Validation Errors**
   - Invalid GitHub URL format
   - Private repository access denied
   - Repository not found
   - Response: 400 Bad Request with specific error message

2. **External Service Errors**
   - GitHub API rate limit exceeded
   - GitHub API unavailable
   - Git clone timeout
   - Response: 503 Service Unavailable with retry guidance

3. **Analysis Errors**
   - Unsupported language/framework
   - Parse errors in specific files
   - AI model unavailable
   - Response: 200 OK with partial results and error annotations

4. **System Errors**
   - Disk space exhausted
   - Memory limit exceeded
   - Unexpected exceptions
   - Response: 500 Internal Server Error with generic message (log details)

### Error Recovery Strategies

**Graceful Degradation**:
- If AI generation fails → use template-based explanations
- If specific file parsing fails → skip that file, continue with others
- If architecture detection fails → report as "unknown" pattern
- If flow analysis fails → omit flow section, include other sections

**Retry Logic**:
- GitHub API calls: 3 retries with exponential backoff
- Git clone operations: 2 retries with 5-second delay
- AI generation: 2 retries, then fallback to templates

**Timeout Configuration**:
- Git clone: 60 seconds
- Single file analysis: 5 seconds
- AI generation per call: 30 seconds
- Total analysis pipeline: 5 minutes

**Resource Limits**:
- Maximum repository size: 500 MB (shallow clone)
- Maximum files analyzed: 500 files
- Maximum file size for content analysis: 1 MB
- Maximum concurrent analyses: 5

### Error Response Format

```json
{
  "status": "error" | "partial",
  "error": {
    "code": "INVALID_URL" | "REPO_NOT_FOUND" | "ACCESS_DENIED" | "ANALYSIS_FAILED",
    "message": "Human-readable error description",
    "details": "Additional context for debugging",
    "retry_possible": true | false
  },
  "partial_result": AnalysisResult | null
}
```
**Validates: Requirements 12.6**

## Security & Threat Model

- The system SHALL never execute arbitrary code from cloned repositories.
- The system SHALL treat all repository contents as untrusted input.
- The system SHALL restrict file reads to the cloned directory.
- The system SHALL sandbox file analysis operations.
- The system SHALL limit maximum file size to prevent memory exhaustion.


## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests as complementary approaches:

- **Unit tests** verify specific examples, edge cases, and integration points
- **Property-based tests** verify universal properties across randomized inputs
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Unit Testing Focus Areas

Unit tests should focus on:

1. **Specific Examples**
   - Valid GitHub URL formats: `https://github.com/owner/repo`, `github.com/owner/repo`
   - Known repository structures (create test fixtures)
   - Specific dependency file formats (package.json, requirements.txt examples)

2. **Edge Cases**
   - Empty repositories
   - Repositories with only documentation
   - Repositories with unusual characters in names
   - Very small repositories (1-2 files)
   - Repositories with no clear entry point

3. **Integration Points**
   - API endpoint request/response formats
   - Cache read/write operations
   - GitHub API client interactions (use mocks)
   - AI model client interactions (use mocks)

4. **Error Conditions**
   - Specific error scenarios (404, 403, timeout)
   - Malformed configuration files
   - Invalid JSON/TOML/XML in dependency files

### Property-Based Testing Configuration

**Framework**: Use Hypothesis (Python) for property-based testing

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with comment referencing design property
- Tag format: `# Feature: codebase-explainer, Property {N}: {property title}`

**Test Organization**:
```
tests/
  unit/
    test_url_validation.py
    test_structure_analyzer.py
    test_dependency_parser.py
    test_architecture_detector.py
    test_flow_analyzer.py
    test_explanation_generator.py
    test_api_endpoints.py
  property/
    test_properties_validation.py      # Properties 1-2
    test_properties_structure.py       # Properties 3-7
    test_properties_dependencies.py    # Properties 8-9
    test_properties_architecture.py    # Properties 10-11
    test_properties_flow.py            # Properties 12
    test_properties_explanation.py     # Properties 13-14
    test_properties_contribution.py    # Properties 15-17
    test_properties_performance.py     # Properties 18-21
    test_properties_ui.py              # Property 22
    test_properties_ai.py              # Properties 23-25
    test_properties_errors.py          # Properties 26-27
  integration/
    test_full_pipeline.py
    test_api_integration.py
```

### Property Test Examples

**Property 1: GitHub URL Validation**
```python
from hypothesis import given, strategies as st

# Feature: codebase-explainer, Property 1: GitHub URL Validation
@given(st.text())
def test_url_validation_property(url: str):
    """For any string, validator returns true only for valid GitHub URLs"""
    result = validate_github_url(url)
    
    if result:
        # If validation passes, must match GitHub URL pattern
        assert re.match(r'(https://)?github\.com/[\w-]+/[\w-]+', url)
    else:
        # If validation fails, must not match pattern
        assert not re.match(r'(https://)?github\.com/[\w-]+/[\w-]+', url)
```

**Property 5: Important Files Limit**
```python
# Feature: codebase-explainer, Property 5: Important Files Limit
@given(st.lists(st.text(min_size=1), min_size=0, max_size=1000))
def test_important_files_limit_property(file_list: List[str]):
    """For any repository, important files never exceed 20"""
    # Create mock repository with file_list
    repo = create_mock_repo(file_list)
    
    ranker = FileImportanceRanker()
    ranked = ranker.rank_files(repo.path, repo.files)
    
    important = [f for f in ranked if f.importance_score > threshold]
    assert len(important) <= 20
```

**Property 20: Analysis Caching Round-Trip**
```python
# Feature: codebase-explainer, Property 20: Analysis Caching Round-Trip
@given(st.text(min_size=1))
def test_cache_round_trip_property(repo_url: str):
    """For any repository, cached analysis equals original analysis"""
    # Perform analysis
    original = analyze_repository(repo_url)
    
    # Cache result
    cache_analysis(repo_url, original)
    
    # Retrieve from cache
    cached = get_cached_analysis(repo_url)
    
    # Should be equivalent (excluding timestamps)
    assert original.metadata == cached.metadata
    assert original.structure == cached.structure
    assert original.dependencies == cached.dependencies
    # ... compare all fields except analysis_timestamp
```

### Test Data Strategy

**Real Repository Fixtures**:
- Maintain a list of small, stable public repositories for integration tests
- Examples: simple Python CLI tools, basic React apps, minimal Go services
- Use specific commit SHAs to ensure reproducibility

**Generated Test Data**:
- Use Hypothesis strategies to generate:
  - Random directory structures
  - Random file contents with valid syntax
  - Random dependency lists
  - Random GitHub URLs (valid and invalid)

**Mocking Strategy**:
- Mock GitHub API calls to avoid rate limits
- Mock AI model calls to avoid external dependencies
- Use real git operations on local test repositories
- Use real parsing on generated code samples

### Performance Testing

**Benchmarks**:
- Measure analysis time for repositories of different sizes (10, 100, 500, 1000 files)
- Target: < 2 minutes for 1000 files
- Track memory usage during analysis
- Monitor AI token usage per analysis

**Load Testing**:
- Test concurrent analysis requests (5 simultaneous)
- Verify cache effectiveness (hit rate > 80% for repeated requests)
- Test timeout handling under load

### Continuous Integration

**CI Pipeline**:
1. Run unit tests (fast, < 1 minute)
2. Run property tests (slower, ~5 minutes)
3. Run integration tests with real repositories (~3 minutes)
4. Generate coverage report (target: > 80%)
5. Run linting and type checking

**Pre-commit Hooks**:
- Run unit tests
- Run type checker (mypy)
- Run linter (ruff)
- Format code (black)
