/**
 * LLM Provider interface — provider-agnostic streaming abstraction.
 */

import type { Message, StreamOptions } from "../types.js";

export interface Provider {
  stream(messages: Message[], options: StreamOptions): AsyncIterable<string>;
}
