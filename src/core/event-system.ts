/**
 * Typed event system for battle state tracking.
 * Wraps EventEmitter with typed BattleEvent support and in-memory log.
 */

import { EventEmitter } from "node:events";
import type { BattleEvent } from "../types.js";

type BattleEventType = BattleEvent["type"];

type EventHandler<T extends BattleEventType> = (
  event: Extract<BattleEvent, { type: T }>
) => void;

export class BattleEventSystem {
  private emitter = new EventEmitter();
  private log: BattleEvent[] = [];

  emit(event: BattleEvent): void {
    this.log.push(event);
    this.emitter.emit(event.type, event);
  }

  on<T extends BattleEventType>(type: T, handler: EventHandler<T>): void {
    this.emitter.on(type, handler);
  }

  off<T extends BattleEventType>(type: T, handler: EventHandler<T>): void {
    this.emitter.off(type, handler);
  }

  getLog(): readonly BattleEvent[] {
    return this.log;
  }

  getEventsByType<T extends BattleEventType>(
    type: T
  ): Extract<BattleEvent, { type: T }>[] {
    return this.log.filter(
      (e): e is Extract<BattleEvent, { type: T }> => e.type === type
    );
  }

  clear(): void {
    this.log = [];
    this.emitter.removeAllListeners();
  }
}
