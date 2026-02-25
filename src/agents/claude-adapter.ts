/**
 * Claude adapter — implements Provider interface using @anthropic-ai/sdk.
 * Streams responses via the messages API.
 */

import Anthropic from "@anthropic-ai/sdk";
import type { Provider } from "./provider.js";
import type { Message, StreamOptions } from "../types.js";

const DEFAULT_MODEL = "claude-sonnet-4-20250514";

export class ClaudeAdapter implements Provider {
  private client: Anthropic;

  constructor(apiKey?: string) {
    this.client = new Anthropic({
      apiKey: apiKey || process.env.ANTHROPIC_API_KEY,
    });
  }

  async *stream(
    messages: Message[],
    options: StreamOptions
  ): AsyncIterable<string> {
    const anthropicMessages = messages.map((m) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    }));

    const stream = this.client.messages.stream({
      model: options.model || DEFAULT_MODEL,
      max_tokens: options.maxTokens,
      system: options.systemPrompt,
      messages: anthropicMessages,
    });

    for await (const event of stream) {
      if (
        event.type === "content_block_delta" &&
        event.delta.type === "text_delta"
      ) {
        yield event.delta.text;
      }
    }
  }
}

export function validateApiKey(): boolean {
  return !!process.env.ANTHROPIC_API_KEY;
}
