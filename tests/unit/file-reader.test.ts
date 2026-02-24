import { describe, it, expect, afterEach } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";
import { readCodebase, formatFilesForPrompt, hasSourceFiles } from "../../src/core/file-reader.js";
import type { FileEntry } from "../../src/types.js";

// Tracks temp directories created during tests so they can be cleaned up.
const tempDirs: string[] = [];

function createTempDir(): string {
  const dir = fs.mkdtempSync(path.join(fs.realpathSync(require("os").tmpdir()), "file-reader-test-"));
  tempDirs.push(dir);
  return dir;
}

afterEach(() => {
  for (const dir of tempDirs.splice(0)) {
    try {
      fs.rmSync(dir, { recursive: true, force: true });
    } catch {
      // Best-effort cleanup
    }
  }
});

describe("readCodebase()", () => {
  it("reads .ts files from a directory", async () => {
    const dir = createTempDir();
    fs.writeFileSync(path.join(dir, "index.ts"), "export const x = 1;\n", "utf-8");

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.value.length).toBeGreaterThan(0);
    const file = result.value.find((f) => f.path.endsWith("index.ts"));
    expect(file).toBeDefined();
    expect(file!.content).toContain("export const x = 1;");
  });

  it("reads multiple source files from a directory", async () => {
    const dir = createTempDir();
    fs.writeFileSync(path.join(dir, "a.ts"), "const a = 1;", "utf-8");
    fs.writeFileSync(path.join(dir, "b.js"), "const b = 2;", "utf-8");
    fs.writeFileSync(path.join(dir, "c.py"), "c = 3", "utf-8");

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value.length).toBe(3);
  });

  it("excludes node_modules directory", async () => {
    const dir = createTempDir();
    fs.writeFileSync(path.join(dir, "index.ts"), "export {};", "utf-8");

    const nmDir = path.join(dir, "node_modules", "some-package");
    fs.mkdirSync(nmDir, { recursive: true });
    fs.writeFileSync(path.join(nmDir, "index.js"), "module.exports = {};", "utf-8");

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const paths = result.value.map((f) => f.path);
    const hasNodeModules = paths.some((p) => p.includes("node_modules"));
    expect(hasNodeModules).toBe(false);
  });

  it("excludes .git directory", async () => {
    const dir = createTempDir();
    fs.writeFileSync(path.join(dir, "app.ts"), "export {};", "utf-8");

    const gitDir = path.join(dir, ".git", "refs");
    fs.mkdirSync(gitDir, { recursive: true });
    fs.writeFileSync(path.join(gitDir, "HEAD"), "ref: refs/heads/main", "utf-8");

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const paths = result.value.map((f) => f.path);
    const hasGit = paths.some((p) => p.includes(".git"));
    expect(hasGit).toBe(false);
  });

  it("excludes non-source file extensions", async () => {
    const dir = createTempDir();
    fs.writeFileSync(path.join(dir, "source.ts"), "export {};", "utf-8");
    fs.writeFileSync(path.join(dir, "image.png"), Buffer.from([137, 80, 78, 71]));
    fs.writeFileSync(path.join(dir, "binary.exe"), Buffer.from([77, 90]));
    fs.writeFileSync(path.join(dir, "notes.docx"), Buffer.from([80, 75]));

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const paths = result.value.map((f) => f.path);
    expect(paths.some((p) => p.endsWith(".png"))).toBe(false);
    expect(paths.some((p) => p.endsWith(".exe"))).toBe(false);
    expect(paths.some((p) => p.endsWith(".docx"))).toBe(false);
    expect(paths.some((p) => p.endsWith(".ts"))).toBe(true);
  });

  it("returns ok:true with empty array for an empty directory", async () => {
    const dir = createTempDir();

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.value).toHaveLength(0);
  });

  it("returns ok:false for a non-existent directory", async () => {
    const result = await readCodebase("/this/path/absolutely/does/not/exist");

    expect(result.ok).toBe(false);
  });

  it("file entries contain relative paths (not absolute)", async () => {
    const dir = createTempDir();
    fs.writeFileSync(path.join(dir, "service.ts"), "export {};", "utf-8");

    const result = await readCodebase(dir);

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const file = result.value.find((f) => f.path.endsWith("service.ts"));
    expect(file).toBeDefined();
    expect(path.isAbsolute(file!.path)).toBe(false);
  });
});

describe("formatFilesForPrompt()", () => {
  it("returns an empty string for an empty file list", () => {
    const output = formatFilesForPrompt([]);
    expect(output).toBe("");
  });

  it("formats a single file with the correct separator header", () => {
    const files: FileEntry[] = [
      { path: "src/index.ts", content: "export const x = 1;" },
    ];

    const output = formatFilesForPrompt(files);

    expect(output).toContain("=== src/index.ts ===");
    expect(output).toContain("export const x = 1;");
  });

  it("formats multiple files separated by double newlines", () => {
    const files: FileEntry[] = [
      { path: "a.ts", content: "const a = 1;" },
      { path: "b.ts", content: "const b = 2;" },
    ];

    const output = formatFilesForPrompt(files);

    expect(output).toContain("=== a.ts ===");
    expect(output).toContain("const a = 1;");
    expect(output).toContain("=== b.ts ===");
    expect(output).toContain("const b = 2;");

    // The two blocks should be separated by double newlines
    const parts = output.split("\n\n");
    expect(parts.length).toBeGreaterThanOrEqual(2);
  });

  it("preserves file content verbatim", () => {
    const content = "function hello() {\n  return 'world';\n}\n";
    const files: FileEntry[] = [{ path: "hello.ts", content }];

    const output = formatFilesForPrompt(files);

    expect(output).toContain(content);
  });
});

describe("hasSourceFiles()", () => {
  it("returns false for an empty array", () => {
    expect(hasSourceFiles([])).toBe(false);
  });

  it("returns true when there is at least one file entry", () => {
    const files: FileEntry[] = [
      { path: "src/index.ts", content: "export {};" },
    ];
    expect(hasSourceFiles(files)).toBe(true);
  });

  it("returns true for multiple file entries", () => {
    const files: FileEntry[] = [
      { path: "a.ts", content: "" },
      { path: "b.ts", content: "" },
    ];
    expect(hasSourceFiles(files)).toBe(true);
  });
});
