import { describe, it, expect, beforeEach } from "vitest";
import { BattleEventSystem } from "../../src/core/event-system.js";
import type { BattleEvent, Finding, Mitigation } from "../../src/types.js";

const makeFinding = (): Finding => ({
  id: "abc12345",
  roundNumber: 1,
  filePath: "src/db.ts",
  lineReference: "42",
  description: "SQL injection in query builder",
  attackVector: "User-controlled input concatenated into raw SQL",
  severity: "high",
});

const makeMitigation = (): Mitigation => ({
  id: "mit12345",
  findingId: "abc12345",
  roundNumber: 1,
  acknowledgment: "Confirmed SQL injection risk",
  proposedFix: "Use parameterized queries",
  confidence: "high",
});

describe("BattleEventSystem", () => {
  let eventSystem: BattleEventSystem;

  beforeEach(() => {
    eventSystem = new BattleEventSystem();
  });

  describe("emit()", () => {
    it("adds a single event to the log", () => {
      const event: BattleEvent = {
        type: "battle-start",
        timestamp: new Date(),
        data: { battleId: "battle-1", scenario: "sql-injection", targetDir: "/tmp/app" },
      };

      eventSystem.emit(event);

      expect(eventSystem.getLog()).toHaveLength(1);
      expect(eventSystem.getLog()[0]).toBe(event);
    });

    it("adds multiple events to the log in order", () => {
      const event1: BattleEvent = {
        type: "battle-start",
        timestamp: new Date(),
        data: { battleId: "battle-1", scenario: "sql-injection", targetDir: "/tmp/app" },
      };
      const event2: BattleEvent = {
        type: "round-start",
        timestamp: new Date(),
        data: { roundNumber: 1 },
      };
      const event3: BattleEvent = {
        type: "round-end",
        timestamp: new Date(),
        data: { roundNumber: 1, findingCount: 2, mitigationCount: 2 },
      };

      eventSystem.emit(event1);
      eventSystem.emit(event2);
      eventSystem.emit(event3);

      const log = eventSystem.getLog();
      expect(log).toHaveLength(3);
      expect(log[0]).toBe(event1);
      expect(log[1]).toBe(event2);
      expect(log[2]).toBe(event3);
    });
  });

  describe("on()", () => {
    it("handler is called with the correct event when that type is emitted", () => {
      const received: BattleEvent[] = [];

      eventSystem.on("attack", (event) => {
        received.push(event);
      });

      const attackEvent: BattleEvent = {
        type: "attack",
        timestamp: new Date(),
        data: { roundNumber: 1, findings: [makeFinding()] },
      };

      eventSystem.emit(attackEvent);

      expect(received).toHaveLength(1);
      expect(received[0]).toBe(attackEvent);
    });

    it("handler is NOT called for other event types", () => {
      const received: BattleEvent[] = [];

      eventSystem.on("attack", (event) => {
        received.push(event);
      });

      const unrelatedEvent: BattleEvent = {
        type: "round-start",
        timestamp: new Date(),
        data: { roundNumber: 1 },
      };

      eventSystem.emit(unrelatedEvent);

      expect(received).toHaveLength(0);
    });

    it("multiple handlers for the same type are all called", () => {
      const calls: number[] = [];

      eventSystem.on("defend", () => calls.push(1));
      eventSystem.on("defend", () => calls.push(2));

      const defendEvent: BattleEvent = {
        type: "defend",
        timestamp: new Date(),
        data: { roundNumber: 1, mitigations: [makeMitigation()] },
      };

      eventSystem.emit(defendEvent);

      expect(calls).toEqual([1, 2]);
    });

    it("handler receives typed event data correctly", () => {
      let capturedFindingCount = 0;

      eventSystem.on("round-end", (event) => {
        capturedFindingCount = event.data.findingCount;
      });

      const roundEndEvent: BattleEvent = {
        type: "round-end",
        timestamp: new Date(),
        data: { roundNumber: 1, findingCount: 5, mitigationCount: 4 },
      };

      eventSystem.emit(roundEndEvent);

      expect(capturedFindingCount).toBe(5);
    });
  });

  describe("getLog()", () => {
    it("returns an empty array before any events are emitted", () => {
      expect(eventSystem.getLog()).toHaveLength(0);
    });

    it("returns all emitted events in emission order", () => {
      const events: BattleEvent[] = [
        { type: "battle-start", timestamp: new Date(), data: { battleId: "b1", scenario: "xss", targetDir: "/app" } },
        { type: "round-start", timestamp: new Date(), data: { roundNumber: 1 } },
        { type: "attack", timestamp: new Date(), data: { roundNumber: 1, findings: [] } },
        { type: "defend", timestamp: new Date(), data: { roundNumber: 1, mitigations: [] } },
        { type: "round-end", timestamp: new Date(), data: { roundNumber: 1, findingCount: 0, mitigationCount: 0 } },
      ];

      for (const e of events) {
        eventSystem.emit(e);
      }

      const log = eventSystem.getLog();
      expect(log).toHaveLength(events.length);
      for (let i = 0; i < events.length; i++) {
        expect(log[i]).toBe(events[i]);
      }
    });

    it("returns a readonly view (the returned array matches logged events)", () => {
      // Register a listener for the error event type before emitting it
      // (Node's EventEmitter throws on unhandled "error" emissions)
      const event: BattleEvent = {
        type: "error",
        timestamp: new Date(),
        data: { message: "Something went wrong", phase: "attack" },
      };
      eventSystem.on("error", () => {});

      eventSystem.emit(event);

      const log = eventSystem.getLog();
      expect(log).toHaveLength(1);
      expect(log[0].type).toBe("error");
    });
  });

  describe("getEventsByType()", () => {
    it("returns only events matching the requested type", () => {
      const attackEvent: BattleEvent = {
        type: "attack",
        timestamp: new Date(),
        data: { roundNumber: 1, findings: [makeFinding()] },
      };
      const roundStartEvent: BattleEvent = {
        type: "round-start",
        timestamp: new Date(),
        data: { roundNumber: 1 },
      };

      eventSystem.emit(attackEvent);
      eventSystem.emit(roundStartEvent);
      eventSystem.emit(attackEvent);

      const attacks = eventSystem.getEventsByType("attack");
      expect(attacks).toHaveLength(2);
      for (const a of attacks) {
        expect(a.type).toBe("attack");
      }
    });

    it("returns an empty array when no events of that type exist", () => {
      const event: BattleEvent = {
        type: "round-start",
        timestamp: new Date(),
        data: { roundNumber: 1 },
      };
      eventSystem.emit(event);

      const attacks = eventSystem.getEventsByType("attack");
      expect(attacks).toHaveLength(0);
    });

    it("filters correctly across mixed event types", () => {
      const e1: BattleEvent = { type: "battle-start", timestamp: new Date(), data: { battleId: "b1", scenario: "s", targetDir: "/d" } };
      const e2: BattleEvent = { type: "round-start", timestamp: new Date(), data: { roundNumber: 1 } };
      const e3: BattleEvent = { type: "round-start", timestamp: new Date(), data: { roundNumber: 2 } };
      const e4: BattleEvent = { type: "battle-end", timestamp: new Date(), data: { battleId: "b1", status: "completed", summary: { totalRounds: 2, totalFindings: 0, findingsBySeverity: { critical: 0, high: 0, medium: 0, low: 0 }, totalMitigations: 0, mitigationCoverage: 100 } } };

      eventSystem.emit(e1);
      eventSystem.emit(e2);
      eventSystem.emit(e3);
      eventSystem.emit(e4);

      const roundStarts = eventSystem.getEventsByType("round-start");
      expect(roundStarts).toHaveLength(2);
      expect(roundStarts[0].data.roundNumber).toBe(1);
      expect(roundStarts[1].data.roundNumber).toBe(2);
    });
  });

  describe("clear()", () => {
    it("removes all events from the log", () => {
      eventSystem.emit({ type: "round-start", timestamp: new Date(), data: { roundNumber: 1 } });
      eventSystem.emit({ type: "round-start", timestamp: new Date(), data: { roundNumber: 2 } });

      expect(eventSystem.getLog()).toHaveLength(2);

      eventSystem.clear();

      expect(eventSystem.getLog()).toHaveLength(0);
    });

    it("removes all event listeners so handlers are no longer called", () => {
      let callCount = 0;
      eventSystem.on("round-start", () => { callCount++; });

      eventSystem.emit({ type: "round-start", timestamp: new Date(), data: { roundNumber: 1 } });
      expect(callCount).toBe(1);

      eventSystem.clear();

      eventSystem.emit({ type: "round-start", timestamp: new Date(), data: { roundNumber: 2 } });
      // Log has the event but the old handler is gone
      expect(callCount).toBe(1);
    });

    it("allows new events to be emitted after clearing", () => {
      eventSystem.emit({ type: "round-start", timestamp: new Date(), data: { roundNumber: 1 } });
      eventSystem.clear();

      const newEvent: BattleEvent = {
        type: "round-start",
        timestamp: new Date(),
        data: { roundNumber: 2 },
      };
      eventSystem.emit(newEvent);

      const log = eventSystem.getLog();
      expect(log).toHaveLength(1);
      expect(log[0]).toBe(newEvent);
    });
  });
});
