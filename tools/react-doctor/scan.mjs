#!/usr/bin/env node

/**
 * Deterministic, privacy-preserving React Doctor adapter.
 *
 * Exit codes form a stable contract for the Python inspection engine:
 *   0: complete scan with no diagnostics
 *   1: complete scan with one or more diagnostics
 *   2: scanner/configuration failure; evidence is not trustworthy
 */

import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { diagnose } from "react-doctor/api";

const ADAPTER_SCHEMA_VERSION = "1.0";
const CATEGORY_ORDER = new Map([
  ["Security", 0],
  ["Bugs", 1],
  ["Performance", 2],
  ["Accessibility", 3],
  ["Maintainability", 4],
]);
const SEVERITY_ORDER = new Map([
  ["error", 0],
  ["warning", 1],
]);
const IGNORED_FILES = [
  "backend/**",
  "node_modules/**",
  "server.ts",
  "scripts/**",
  "deploy/**",
  "migrations/**",
  "docs/**",
  ".agents/**",
  ".github/**",
  "assets/**",
  "qa-*.json",
];
const EXCLUDED_PREFIXES = [
  "backend/",
  "node_modules/",
  "scripts/",
  "deploy/",
  "migrations/",
  "docs/",
  ".agents/",
  ".github/",
  "assets/",
];

function compareText(left, right) {
  return String(left ?? "").localeCompare(String(right ?? ""), "en");
}

function compareDiagnostics(left, right) {
  return (
    (SEVERITY_ORDER.get(left.severity) ?? 99) -
      (SEVERITY_ORDER.get(right.severity) ?? 99) ||
    (CATEGORY_ORDER.get(left.category) ?? 99) -
      (CATEGORY_ORDER.get(right.category) ?? 99) ||
    compareText(left.normalizedFilePath ?? left.filePath, right.normalizedFilePath ?? right.filePath) ||
    (left.line ?? 0) - (right.line ?? 0) ||
    (left.column ?? 0) - (right.column ?? 0) ||
    compareText(left.rule, right.rule) ||
    compareText(left.id, right.id)
  );
}

function orderedCounts(values) {
  const counts = new Map();
  for (const value of values) {
    const key = String(value ?? "Unknown");
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Object.fromEntries(
    [...counts.entries()].sort(
      ([leftKey, leftCount], [rightKey, rightCount]) =>
        rightCount - leftCount || compareText(leftKey, rightKey),
    ),
  );
}

function normalizeDiagnostic(diagnostic) {
  const file = diagnostic.normalizedFilePath ?? diagnostic.filePath ?? null;
  const rule = `${diagnostic.plugin ?? "unknown"}/${diagnostic.rule ?? "unknown"}`;
  const fingerprintMaterial = [
    "react-doctor",
    rule,
    file,
    diagnostic.line ?? 0,
    diagnostic.column ?? 0,
    diagnostic.message ?? "",
  ].join("\0");
  return {
    fingerprint: createHash("sha256")
      .update(fingerprintMaterial)
      .digest("hex")
      .slice(0, 20),
    severity: diagnostic.severity ?? "unknown",
    category: diagnostic.category ?? "Unknown",
    rule,
    file,
    line: diagnostic.line ?? 0,
    column: diagnostic.column ?? 0,
    title: diagnostic.title ?? null,
    message: diagnostic.message ?? null,
    help: diagnostic.help ?? null,
  };
}

function isExcludedDiagnostic(diagnostic) {
  const file = String(
    diagnostic.normalizedFilePath ?? diagnostic.filePath ?? "",
  ).replaceAll("\\", "/");
  return (
    file === "server.ts" ||
    (file.startsWith("qa-") && file.endsWith(".json")) ||
    EXCLUDED_PREFIXES.some((prefix) => file.startsWith(prefix))
  );
}

async function toolVersion() {
  const currentFile = fileURLToPath(import.meta.url);
  const packageFile = path.join(path.dirname(currentFile), "node_modules", "react-doctor", "package.json");
  const packageDocument = JSON.parse(await readFile(packageFile, "utf8"));
  return packageDocument.version;
}

function targetArgument() {
  return process.argv.slice(2).find((argument) => !argument.startsWith("--")) ?? ".";
}

async function main() {
  const requiredPrivacyFlags = ["--no-score", "--no-telemetry", "--no-supply-chain"];
  const missingFlags = requiredPrivacyFlags.filter((flag) => !process.argv.includes(flag));
  if (missingFlags.length) {
    throw new Error(`required privacy flags are missing: ${missingFlags.join(", ")}`);
  }

  process.env.NO_COLOR = "1";
  const targetDirectory = path.resolve(process.cwd(), targetArgument());
  const result = await diagnose({
    projects: [{ directory: targetDirectory }],
    config: {
      ignore: { files: IGNORED_FILES },
      supplyChain: { enabled: false },
      noScore: true,
      share: false,
      scope: "full",
      warnings: true,
    },
    concurrency: 1,
    deadCode: true,
    lint: true,
    warnings: true,
  });

  const project = result.projects[0];
  if (!project || !project.ok) {
    throw new Error(project?.error?.message ?? "React Doctor returned no project result");
  }
  if (project.reactDetected === false) {
    throw new Error("React Doctor did not detect a React runtime in the scan target");
  }
  if (project.skippedChecks?.length) {
    throw new Error(`React Doctor skipped checks: ${project.skippedChecks.join(", ")}`);
  }

  const diagnostics = [...project.diagnostics].sort(compareDiagnostics);
  const excludedDiagnostics = diagnostics.filter(isExcludedDiagnostic);
  if (excludedDiagnostics.length) {
    const firstFile =
      excludedDiagnostics[0].normalizedFilePath ?? excludedDiagnostics[0].filePath;
    throw new Error(
      `React Doctor returned ${excludedDiagnostics.length} out-of-scope diagnostics; first: ${firstFile}`,
    );
  }
  const normalized = diagnostics.map(normalizeDiagnostic);
  const errorCount = diagnostics.filter((item) => item.severity === "error").length;
  const warningCount = diagnostics.filter((item) => item.severity === "warning").length;
  const affectedFiles = new Set(
    diagnostics.map((item) => item.normalizedFilePath ?? item.filePath),
  );
  const report = {
    schema_version: ADAPTER_SCHEMA_VERSION,
    tool: "react-doctor",
    tool_version: await toolVersion(),
    status: diagnostics.length ? "findings" : "passed",
    react_detected: true,
    framework: project.project.framework,
    summary: {
      diagnostic_count: diagnostics.length,
      error_count: errorCount,
      warning_count: warningCount,
      affected_file_count: affectedFiles.size,
      scanned_file_count: project.scannedFileCount ?? null,
    },
    counts_by_category: orderedCounts(diagnostics.map((item) => item.category)),
    counts_by_rule: orderedCounts(
      diagnostics.map((item) => `${item.plugin ?? "unknown"}/${item.rule ?? "unknown"}`),
    ),
    selected_target: normalized[0] ?? null,
    leading_diagnostics: normalized.slice(0, 10),
    ignored_paths: IGNORED_FILES,
  };

  process.stdout.write(`${JSON.stringify(report)}\n`);
  process.exitCode = diagnostics.length ? 1 : 0;
}

main().catch(async (error) => {
  const report = {
    schema_version: ADAPTER_SCHEMA_VERSION,
    tool: "react-doctor",
    tool_version: await toolVersion().catch(() => "unknown"),
    status: "tool_error",
    error: {
      name: error instanceof Error ? error.name : "Error",
      message: error instanceof Error ? error.message : String(error),
    },
  };
  process.stderr.write(`${JSON.stringify(report)}\n`);
  process.exitCode = 2;
});
