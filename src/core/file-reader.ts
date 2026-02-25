/**
 * Codebase file reader — recursively reads source files with filtering.
 * Respects extension filters, directory exclusions, and size caps.
 */

import { readFile, readdir, stat } from "node:fs/promises";
import { join, extname, relative } from "node:path";
import type { FileEntry, Result } from "../types.js";

const SOURCE_EXTENSIONS = new Set([
  ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
  ".py", ".pyw",
  ".java", ".kt", ".kts",
  ".go",
  ".rb", ".erb",
  ".php",
  ".cs",
  ".rs",
  ".c", ".cpp", ".h", ".hpp",
  ".swift",
  ".scala",
  ".sql",
  ".html", ".htm", ".vue", ".svelte",
  ".css", ".scss", ".less",
  ".yaml", ".yml", ".toml", ".json", ".xml",
  ".sh", ".bash", ".zsh",
  ".env", ".env.example",
  ".dockerfile",
  ".tf",
]);

const EXCLUDED_DIRS = new Set([
  "node_modules", ".git", "dist", "build", "vendor",
  ".next", ".nuxt", "__pycache__", ".venv", "venv",
  "target", ".gradle", ".idea", ".vscode",
  "coverage", ".specify", ".claude", "specs", "history",
]);

const EXCLUDED_FILES = new Set([
  "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
  "bun.lockb", "Cargo.lock", "Gemfile.lock",
  "poetry.lock", "composer.lock",
]);

const MAX_FILE_SIZE = 64 * 1024; // 64KB per file
const MAX_TOTAL_SIZE = 100 * 1024; // 100KB total context budget

export interface ReadCodebaseOptions {
  maxFileSize?: number;
  maxTotalSize?: number;
}

export async function readCodebase(
  targetDir: string,
  options: ReadCodebaseOptions = {}
): Promise<Result<FileEntry[]>> {
  const maxFileSize = options.maxFileSize ?? MAX_FILE_SIZE;
  const maxTotalSize = options.maxTotalSize ?? MAX_TOTAL_SIZE;
  const files: FileEntry[] = [];
  let totalSize = 0;

  try {
    await walkDirectory(targetDir, targetDir, files, totalSize, maxFileSize, maxTotalSize);
    return { ok: true, value: files };
  } catch (err) {
    return {
      ok: false,
      error: new Error(`Failed to read codebase: ${err}`),
    };
  }
}

async function walkDirectory(
  rootDir: string,
  currentDir: string,
  files: FileEntry[],
  totalSize: number,
  maxFileSize: number,
  maxTotalSize: number
): Promise<number> {
  const entries = await readdir(currentDir, { withFileTypes: true });

  for (const entry of entries) {
    if (totalSize >= maxTotalSize) break;

    const fullPath = join(currentDir, entry.name);

    if (entry.isDirectory()) {
      if (EXCLUDED_DIRS.has(entry.name)) continue;
      totalSize = await walkDirectory(
        rootDir, fullPath, files, totalSize, maxFileSize, maxTotalSize
      );
    } else if (entry.isFile()) {
      if (EXCLUDED_FILES.has(entry.name)) continue;

      const ext = extname(entry.name).toLowerCase();
      if (!SOURCE_EXTENSIONS.has(ext)) continue;

      try {
        const fileStat = await stat(fullPath);
        if (fileStat.size > maxFileSize) continue;
        if (totalSize + fileStat.size > maxTotalSize) continue;

        const content = await readFile(fullPath, "utf-8");
        const relativePath = relative(rootDir, fullPath);

        files.push({ path: relativePath, content });
        totalSize += fileStat.size;
      } catch {
        // Skip unreadable files
        continue;
      }
    }
  }

  return totalSize;
}

export function formatFilesForPrompt(files: FileEntry[]): string {
  return files
    .map((f) => `=== ${f.path} ===\n${f.content}`)
    .join("\n\n");
}

export function hasSourceFiles(files: FileEntry[]): boolean {
  return files.length > 0;
}
