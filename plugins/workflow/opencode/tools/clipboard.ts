import { tool } from "@opencode-ai/plugin"
import { spawnSync } from "child_process"

/**
 * clipboard — copy text to system clipboard.
 *
 * Поддержка:
 * - macOS: pbcopy
 * - Linux (Wayland): wl-copy
 * - Linux (X11): xclip / xsel
 * - Windows: clip
 */
function tryCopy(cmd: string[], text: string): string | null {
  const res = spawnSync(cmd[0], cmd.slice(1), { input: text, encoding: "utf-8" })
  if (res.error) return null
  if (typeof res.status === "number" && res.status !== 0) return null
  return cmd.join(" ")
}

export default tool({
  description: "Скопировать текст в буфер обмена (pbcopy/wl-copy/xclip/xsel/clip).",
  args: {
    text: tool.schema.string().describe("Текст для копирования"),
  },
  async execute(args) {
    const text = args.text ?? ""
    const candidates: string[][] = []

    // Порядок важен: сначала нативные варианты.
    if (process.platform === "darwin") {
      candidates.push(["pbcopy"])
    } else if (process.platform === "win32") {
      candidates.push(["clip"])
    } else {
      // Linux / WSL
      candidates.push(["wl-copy"])
      candidates.push(["xclip", "-selection", "clipboard"])
      candidates.push(["xsel", "--clipboard", "--input"])
    }

    for (const cmd of candidates) {
      const ok = tryCopy(cmd, text)
      if (ok) return `copied via: ${ok}`
    }

    // Если ничего не сработало — возвращаем текст, чтобы пользователь мог скопировать вручную.
    return [
      "Не удалось автоматически скопировать в буфер (нет pbcopy/wl-copy/xclip/xsel/clip).",
      "",
      "Скопируйте вручную:",
      text,
    ].join("\n")
  },
})
