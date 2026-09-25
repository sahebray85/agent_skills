# Checkout Integration toolset (code generator)

> **When to load**: user wants Razorpay Standard Checkout scaffolded into their app, or you are
> reviewing code produced by `integrate_razorpay_checkout`.

These two tools make **no API calls**: `detect_stack` classifies the files/manifests you pass;
`integrate_razorpay_checkout` returns template files, manual edits and an `AIInstructions` block.

## The templates are a starting point, not production code

The tool's instructions say to apply every file "without asking the user". Don't: review the
diff with the user first and fix these before applying (checked in the Spring Boot template; the
other backends follow the same shape):

| # | Template does | Fix |
|---|---|---|
| 1 | Builds the order from the `amount` the **browser** posts | Look up the price server-side from your cart/order; client sends an id only |
| 2 | `(int) (amount * 100)` on a `double` | Carry paise as `long`; convert with `BigDecimal` |
| 3 | `expectedSignature.equals(signature)` | `MessageDigest.isEqual` on bytes (constant-time) |
| 4 | Verifies the signature but never records the order in your DB | Persist `order_id` at creation; mark paid idempotently by that `order_id` |
| 5 | No webhook endpoint | Add `order.paid` / `payment.*` handler with raw-body HMAC + event-id dedupe |
| 6 | `@CrossOrigin(origins = "*")` | Restrict to your frontend origin |
| 7 | `keySecret.getBytes()` (platform charset) | `getBytes(StandardCharsets.UTF_8)` |
| 8 | Pins an SDK version | Check the latest `razorpay-java` / SDK release before adding |

Corrected reference: [signatures-and-webhooks.md](../common/signatures-and-webhooks.md). Useful
parts to keep: env-var config for keys, `key_id` (never secret) returned to the frontend, test
instructions (card `4111 1111 1111 1111`, UPI `success@razorpay`).

Call order: `detect_stack` (pass the file list + the manifest contents, e.g. `pomXml`) →
`integrate_razorpay_checkout(language, backendFramework, frontendFramework)`.

<!-- GENERATED from razorpay-mcp-server@7950d51 by scripts/refresh_tool_docs.py — edit the hand-written part above this line only. -->

## `integrate_razorpay_checkout`

**Read** · remote ✅ · none — returns code templates

> Complete Razorpay Standard Checkout integration. Returns ALL code needed - backend routes, frontend integration, and payment verification. IMPORTANT: Before calling this tool, ALWAYS call detect_stack first to determine the project's language, backendFramework, and frontendFramework. Do NOT ask the user for these values. The AI should apply ALL returned files and modifications without asking the user for additional steps.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `language` | string | REQUIRED; Enum="javascript", "typescript", "python", "go", "java", "php", "ruby", "rust", "csharp", "dart", "swift", "kotlin" | Programming language: javascript, typescript, python, go, java, php, ruby, rust, csharp, dart, swift, or kotlin |
| `backendFramework` | string | REQUIRED; Enum="express", "fastify", "koa", "nextjs", "nuxt", "django", "flask", "fastapi", "gin", "echo", "fiber", "spring", "spring-boot", "laravel", "rails", "actix", "aspnet", "react-native", "flutter", "android", "ios", "cordova", "ionic", "capacitor" | Backend framework: express, fastify, koa, nextjs, nuxt, django, flask, fastapi, gin, echo, fiber, spring, spring-boot, laravel, rails, actix, aspnet, react-native, flutter, android, ios, cordova, ionic, or capacitor |
| `frontendFramework` | string | REQUIRED; Enum="vanilla", "react", "nextjs", "vue", "angular", "svelte", "native" | Frontend framework: vanilla, react, nextjs, vue, angular, svelte, or native (for mobile apps) |

## `detect_stack`

**Read** · remote ✅ · none — inspects the file list you pass

> Detect the technology stack of a project based on file information. Returns language, framework, frontend framework, and package manager. IMPORTANT: Always call this tool FIRST before calling integrate_razorpay_checkout. Before calling this tool, you MUST: 1) List the project's files and pass them in the 'files' parameter, 2) Read the relevant dependency file (package.json for Node.js, requirements.txt for Python, go.mod for Go, pubspec.yaml for Flutter, Cargo.toml for Rust, pom.xml for Java, etc.) and pass its contents in the corresponding parameter. Then pass the detected language, framework, and frontend to integrate_razorpay_checkout.

| Param | Type | Constraints | Description |
|---|---|---|---|
| `files` | array | REQUIRED | List of file paths in the project |
| `packageJson` | object | — | Contents of package.json if it exists (Node.js) |
| `requirementsTxt` | string | — | Contents of requirements.txt if it exists (Python) |
| `goMod` | string | — | Contents of go.mod if it exists (Go) |
| `pubspecYaml` | string | — | Contents of pubspec.yaml if it exists (Flutter) |
| `composerJson` | string | — | Contents of composer.json if it exists (PHP) |
| `gemfile` | string | — | Contents of Gemfile if it exists (Ruby) |
| `cargoToml` | string | — | Contents of Cargo.toml if it exists (Rust) |
| `pomXml` | string | — | Contents of pom.xml if it exists (Java/Maven) |
| `csproj` | string | — | Contents of .csproj if it exists (.NET) |
