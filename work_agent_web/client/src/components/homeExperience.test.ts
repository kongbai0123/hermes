import { describe, expect, it } from "vitest";
import { HERMES_HOME_COPY, HOME_MODE_TABS } from "./homeExperience";

describe("Hermes home experience", () => {
  it("keeps the home hero copy and mode switcher labels focused on the Hermes workflow", () => {
    expect(HERMES_HOME_COPY).toEqual({
      title: "HERMES AGENT",
      subtitle: "tell me what you're making; i love refactors, tiny helpers, and big scary repos alike (>w<)",
    });

    expect(HOME_MODE_TABS.map((tab) => tab.label)).toEqual([
      "單模型",
      "多模型",
      "代理操作",
      "任務編排",
      "運行監控",
    ]);
    expect(HOME_MODE_TABS.slice(0, 4).map((tab) => tab.kind)).toEqual([
      "task-mode",
      "task-mode",
      "task-mode",
      "task-mode",
    ]);
    expect(HOME_MODE_TABS[4]).toMatchObject({ kind: "monitor", label: "運行監控" });
  });
});
